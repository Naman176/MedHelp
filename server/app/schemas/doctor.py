from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import time
from uuid import UUID
from app.schemas.user import UserResponse 

class DoctorResponse(BaseModel):
    id: UUID
    user_id: UUID
    specialization: str
    license_number: str
    degree_upload_url: str
    bio: Optional[str] = None
    years_of_experience: int
    consultation_fee: float
    is_available: bool
    user: UserResponse

    model_config = ConfigDict(from_attributes=True)

class AvailabilityCreate(BaseModel):
    days_of_week: List[str]
    start_time: time
    end_time: time

class AvailabilityResponse(AvailabilityCreate):
    id: str

    class Config:
        from_attributes = True

class DoctorAvailabilityRead(BaseModel):
    id: UUID
    doctor_id: UUID
    days_of_week: str  
    start_time: time
    end_time: time

    model_config = ConfigDict(from_attributes=True)