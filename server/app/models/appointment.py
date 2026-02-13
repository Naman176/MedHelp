import uuid
from sqlalchemy import Column, String, Date, Time, ForeignKey, Index, text
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

    # Type: IN_PERSON or VIRTUAL
    appointment_type = Column(String, default="IN_PERSON")
    
    # Link for video calls (Generated when confirmed)
    meeting_link = Column(String, nullable=True)

    # Relationships (Standard SQLAlchemy linking)
    patient = relationship("User", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    __table_args__ = (
        Index(
            'uq_doctor_active_slot', 
            'doctor_id', 'appointment_date', 'appointment_time',
            unique=True,
            postgresql_where=text("status NOT IN ('CANCELLED', 'REJECTED')")
        ),
    )