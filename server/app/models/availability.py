import uuid
from sqlalchemy import Column, String, Time, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class DoctorAvailability(Base):
    __tablename__ = "doctor_availabilities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=False)
    
    # We will store days as "Monday", "Tuesday", etc.
    days_of_week = Column(String, nullable=False) 
    
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    # Relationship back to Doctor
    doctor = relationship("Doctor", back_populates="availabilities")