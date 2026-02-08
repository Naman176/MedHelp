import uuid
from sqlalchemy import Column, String, Date, Time, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Who is the Patient? (Links to Users table)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Who is the Doctor? (Links to Doctors table)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=False)
    
    # When?
    appointment_date = Column(Date, nullable=False)  # YYYY-MM-DD
    appointment_time = Column(Time, nullable=False)  # HH:MM:SS
    
    # Status (PENDING, CONFIRMED, COMPLETED, CANCELLED)
    status = Column(String, default="PENDING")

    # Relationships (Standard SQLAlchemy linking)
    patient = relationship("User", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    __table_args__ = (
        UniqueConstraint('doctor_id', 'appointment_date', 'appointment_time', name='uq_doctor_appointment_slot'),
    )