from sqlalchemy.orm import Session

from app.models.emergency import Emergency
from app.core.redis_client import redis_client

import json

ACTIVE_STATES = [
    "CREATED",
    "PROCESSING",
    "MATCHED",
    "SELECTED",
    "ACCEPTED"
]


def create_emergency(
    db: Session,
    user_id: str,
    symptoms: str,
    latitude: float,
    longitude: float,
    address: str = None
):

    existing = db.query(Emergency).filter(
        Emergency.user_id == user_id,
        Emergency.status.in_(ACTIVE_STATES)
    ).first()

    if existing:
        return None

    emergency = Emergency(
        user_id=user_id,
        symptoms=symptoms,
        latitude=latitude,
        longitude=longitude,
        address=address,
        status="CREATED"
    )

    db.add(emergency)

    db.commit()

    db.refresh(emergency)

    # ==========================================
    # 🔥 PUSH TO REDIS QUEUE
    # ==========================================

    redis_client.lpush(
        "emergency_queue",
        json.dumps({
            "emergency_id": emergency.id
        })
    )

    return emergency


def get_emergency(
    db: Session,
    emergency_id: str
):

    return db.query(Emergency).filter(
        Emergency.id == emergency_id
    ).first()