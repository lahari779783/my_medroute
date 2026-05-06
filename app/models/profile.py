from sqlalchemy import Column, String, Integer, ForeignKey
from app.database import Base
import uuid

class MedicalProfile(Base):
    __tablename__ = "medical_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), unique=True)

    name = Column(String)
    age = Column(Integer)
    blood_group = Column(String)

    allergies = Column(String)
    chronic_conditions = Column(String)
    medications = Column(String)

    emergency_contact = Column(String)