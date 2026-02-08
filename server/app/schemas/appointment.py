from pydantic import BaseModel
from datetime import date, time
from uuid import UUID

class AppointmentCreate(BaseModel):
    doctor_id: UUID
    appointment_date: date  # Format: YYYY-MM-DD
    appointment_time: time