from pydantic import BaseModel, ConfigDict
from typing import List
from datetime import time
from uuid import UUID

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