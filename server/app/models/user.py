import uuid
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    # We use UUID as the type, and uuid.uuid4 as the default generator
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Login Info
    email = Column(String, unique=True, index=True, nullable=False)
    # Nullable because Google users won't have a password
    password_hash = Column(String, nullable=True)
    
    # Profile Info - MANDATORY
    full_name = Column(String, nullable=False)
    
    phone_number = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)
    
    # Role: "user", "doctor", "admin"
    role = Column(String, default="user", nullable=False)
    
    # Status
    # True = Can login. False = Banned/Deactivated.
    is_active = Column(Boolean, default=True)
    # True = Approved by Admin (only for doctors).
    is_verified = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # One-to-One relationship (User can be a Doctor)
    # uselist=False ensures we get a single object, not a list
    doctor = relationship("Doctor", back_populates="user", uselist=False, cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="patient")