from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

# 1. Base Schema (Shared properties)
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None
    profile_picture: Optional[str] = None
    role: str = "user"  # Default to "user", can be "doctor"

# 2. Schema for Creating a User (Incoming Data)
class UserCreate(UserBase):
    password: Optional[str] = None  # Optional for Google Login
    
    # We might add specific fields here later if needed

# 3. Schema for Reading a User (Outgoing Data)
# This hides the password and internal IDs
class UserResponse(UserBase):
    id: UUID
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True  # Tells Pydantic to read data from ORM models