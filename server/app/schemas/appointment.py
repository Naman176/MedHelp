from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict
from datetime import date, time
from uuid import UUID

class AppointmentCreate(BaseModel):
    doctor_id: UUID
    appointment_date: date  # Format: YYYY-MM-DD
    appointment_time: time
    appointment_type: Literal["IN_PERSON", "VIRTUAL"] = "IN_PERSON"
# Schema for Updating Status (For Doctors/Admin)
class AppointmentUpdate(BaseModel):
    status: Literal["PENDING", "CONFIRMED", "CANCELLED", "REJECTED", "COMPLETED"]

# Nested schemas to show simple details about the other person
class DoctorInfo(BaseModel):
    id: UUID
    specialization: str
    # We might want to add 'name' here later if we join with User table

class PatientInfo(BaseModel):
    id: UUID
    email: str

class AppointmentResponse(BaseModel):
    id: UUID
    doctor_id: UUID
    patient_id: UUID
    appointment_date: date
    appointment_time: time
    status: str
    appointment_type: str
    meeting_link: Optional[str] = None

    # Optional: We can add these later to show names
    # doctor: DoctorInfo 
    # patient: PatientInfo

    model_config = ConfigDict(from_attributes=True)