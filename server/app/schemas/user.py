from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

# Base Schema (Shared properties)
class UserBase(BaseModel):
    email: EmailStr
    full_name: str

# Schema for Creating a User (Incoming Data)
class UserCreate(UserBase):
    password: str

# Schema for Reading a User (Outgoing Data)
# This hides the password and internal IDs
class UserResponse(UserBase):
    id: UUID
    phone_number: Optional[str] = None
    profile_picture: Optional[str] = None
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True  # Tells Pydantic to read data from ORM models

class ContactCreate(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str