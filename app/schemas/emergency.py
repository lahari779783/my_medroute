from pydantic import BaseModel

class EmergencyCreate(BaseModel):
    symptoms: str