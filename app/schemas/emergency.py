from pydantic import BaseModel

from typing import Optional, List, Any

from datetime import datetime


# =====================================================
# 🔥 CREATE EMERGENCY
# =====================================================

class EmergencyCreate(BaseModel):

    symptoms: str

    latitude: float

    longitude: float

    address: Optional[str] = None


# =====================================================
# 🔥 HOSPITAL RESPONSE
# =====================================================

class HospitalMatch(BaseModel):

    hospital: str

    distance_km: float

    score: float

    recommended: bool

    match_reason: str

    latitude: float

    longitude: float


# =====================================================
# 🔥 EMERGENCY RESPONSE
# =====================================================

class EmergencyResponse(BaseModel):

    id: str

    user_id: str

    symptoms: str

    status: str

    latitude: Optional[float] = None

    longitude: Optional[float] = None

    address: Optional[str] = None

    severity: Optional[str] = None

    confidence: Optional[float] = None

    requires_icu: Optional[bool] = None

    rationale: Optional[str] = None

    triage_source: Optional[str] = None

    specializations: Optional[str] = None

    matched_hospitals: Optional[
        List[HospitalMatch]
    ] = None

    created_at: datetime

    class Config:

        from_attributes = True