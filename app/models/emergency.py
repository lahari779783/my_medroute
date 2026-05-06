from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    DateTime,
    Float,
    Boolean,
    Text
)

from app.database import Base

import uuid

from datetime import datetime


class Emergency(Base):

    __tablename__ = "emergencies"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id = Column(
        String,
        ForeignKey("users.id")
    )

    symptoms = Column(
        Text,
        nullable=False
    )

    status = Column(
        String,
        default="CREATED"
    )

    # =====================================================
    # 🔥 TRIAGE INTELLIGENCE
    # =====================================================

    severity = Column(
        String,
        nullable=True
    )

    confidence = Column(
        Float,
        nullable=True
    )

    requires_icu = Column(
        Boolean,
        nullable=True
    )

    rationale = Column(
        Text,
        nullable=True
    )

    triage_source = Column(
        String,
        nullable=True
    )

    specializations = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )