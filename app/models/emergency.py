from sqlalchemy import Column, String, ForeignKey, DateTime
from app.database import Base
import uuid
from datetime import datetime

class Emergency(Base):
    __tablename__ = "emergencies"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))

    symptoms = Column(String)

    status = Column(String, default="CREATED")

    created_at = Column(DateTime, default=datetime.utcnow)