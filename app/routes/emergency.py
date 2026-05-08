from fastapi import APIRouter, Depends, HTTPException, Header

from sqlalchemy.orm import Session

import json

from app.database import SessionLocal

from app.schemas.emergency import (
    EmergencyCreate,
    EmergencyResponse
)

from app.services.emergency_service import (
    create_emergency,
    get_emergency
)

from app.core.deps import get_current_user
from app.core.redis_client import redis_client

router = APIRouter()


# =====================================================
# 🔥 DB DEPENDENCY
# =====================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# =====================================================
# 🚑 START EMERGENCY
# =====================================================

@router.post("/emergency/start")
def start_emergency(

    data: EmergencyCreate,

    user_id: str = Depends(get_current_user),

    db: Session = Depends(get_db),

    idempotency_key: str = Header(
        None,
        alias="X-Idempotency-Key"
    )
):

    # ==========================================
    # 🔥 REQUIRE IDEMPOTENCY KEY
    # ==========================================

    if not idempotency_key:

        raise HTTPException(
            status_code=400,
            detail="X-Idempotency-Key header required"
        )

    redis_key = f"idem:{idempotency_key}"

    # ==========================================
    # 🔥 RETURN CACHED RESPONSE
    # ==========================================

    cached = redis_client.get(redis_key)

    if cached:

        return json.loads(cached)

    # ==========================================
    # 🔥 CREATE EMERGENCY
    # ==========================================

    emergency = create_emergency(
        db=db,
        user_id=user_id,
        symptoms=data.symptoms,
        latitude=data.latitude,
        longitude=data.longitude,
        address=data.address
    )

    # ==========================================
    # 🔥 ACTIVE EMERGENCY CHECK
    # ==========================================

    if not emergency:

        raise HTTPException(
            status_code=400,
            detail="Active emergency already exists"
        )

    # ==========================================
    # 🔥 RESPONSE OBJECT
    # ==========================================

    response = {
        "message": "Emergency created",
        "emergency_id": emergency.id,
        "status": emergency.status
    }

    # ==========================================
    # 🔥 CACHE IDEMPOTENT RESPONSE
    # ==========================================

    redis_client.setex(
        redis_key,
        86400,
        json.dumps(response)
    )

    return response


# =====================================================
# 📥 FETCH EMERGENCY
# =====================================================

@router.get(
    "/emergency/{emergency_id}",
    response_model=EmergencyResponse
)
def fetch_emergency(

    emergency_id: str,

    user_id: str = Depends(get_current_user),

    db: Session = Depends(get_db)
):

    emergency = get_emergency(
        db,
        emergency_id
    )

    if not emergency:

        raise HTTPException(
            status_code=404,
            detail="Not found"
        )

    if emergency.user_id != user_id:

        raise HTTPException(
            status_code=403,
            detail="Not allowed"
        )

    # ==========================================
    # 🔥 PARSE JSON FIELDS
    # ==========================================

    if emergency.matched_hospitals:

        emergency.matched_hospitals = json.loads(
            emergency.matched_hospitals
        )

    return emergency