from pydantic import BaseModel

class ProfileCreate(BaseModel):
    name: str
    age: int
    blood_group: str
    allergies: str
    chronic_conditions: str
    medications: str
    emergency_contact: str