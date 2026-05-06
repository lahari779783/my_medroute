from sqlalchemy.orm import Session
from app.models.profile import MedicalProfile

def create_or_update_profile(db: Session, user_id: str, data):
    profile = db.query(MedicalProfile).filter(
        MedicalProfile.user_id == user_id
    ).first()

    if profile:
        # update existing
        for key, value in data.dict().items():
            setattr(profile, key, value)
    else:
        # create new
        profile = MedicalProfile(
            user_id=user_id,
            **data.dict()
        )
        db.add(profile)

    db.commit()
    db.refresh(profile)
    return profile


def get_profile(db: Session, user_id: str):
    return db.query(MedicalProfile).filter(
        MedicalProfile.user_id == user_id
    ).first()