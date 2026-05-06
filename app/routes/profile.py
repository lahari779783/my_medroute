from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas.profile import ProfileCreate
from app.services.profile_service import create_or_update_profile, get_profile
from app.core.deps import get_current_user

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/profile")
def create_profile(
    data: ProfileCreate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = create_or_update_profile(db, user_id, data)

    return {
        "message": "Profile saved",
        "profile_id": profile.id
    }


@router.get("/profile")
def fetch_profile(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = get_profile(db, user_id)

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return profile