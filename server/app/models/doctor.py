import uuid
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Link to the User table (One-to-One)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    # Professional Details
    specialization = Column(String, index=True, nullable=False)  # e.g., "Cardiologist"
    license_number = Column(String, unique=True, nullable=False)
    years_of_experience = Column(Integer, default=0)
    degree_upload_url = Column(String, nullable=True)
    
    consultation_fee = Column(Float, default=0.0)
    bio = Column(Text, nullable=True)
    
    is_available = Column(Boolean, default=True)  # Can they take new appointments?

    # Relationship to User
    user = relationship("User", back_populates="doctor")