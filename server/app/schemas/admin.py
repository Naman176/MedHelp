from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID

# Nested schema to show the User details linked to the Doctor profile
class UserBasicInfo(BaseModel):
    id: UUID
    email: str
    full_name: str
    phone_number: Optional[str] = None
    profile_picture: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

# Schema for GET /admin/doctors/pending
class PendingDoctorResponse(BaseModel):
    id: UUID
    specialization: str
    years_of_experience: int
    license_number: str
    degree_upload_url: str
    consultation_fee: float
    bio: Optional[str] = None
    user: UserBasicInfo  # This maps to the relationship we eagerly loaded with selectinload()

    model_config = ConfigDict(from_attributes=True)

# Schema for PATCH /admin/doctors/{doctor_id}/verify
class VerifyDoctorResponse(BaseModel):
    message: str
    doctor_id: UUID

class RejectDoctorRequest(BaseModel):
    reason: str