from pydantic import BaseModel
from typing import List

class AvailabilityCreate(BaseModel):
    days_of_week: List[str]
    start_time: str
    end_time: str 

class AvailabilityResponse(AvailabilityCreate):
    id: str

    class Config:
        from_attributes = True