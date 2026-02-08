from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.models.availability import DoctorAvailability
from app.schemas.appointment import AppointmentCreate

router = APIRouter()

@router.post("/book", status_code=status.HTTP_201_CREATED)
async def book_appointment(
    booking_data: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Check if Doctor exists
    query_doctor = await db.execute(select(Doctor).where(Doctor.id == booking_data.doctor_id))
    doctor = query_doctor.scalars().first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # 2. Check if Doctor works on this day (e.g., "Monday")
    # Convert date (2023-10-27) to day name ("Friday")
    day_name = booking_data.appointment_date.strftime("%A")
    
    query_availability = await db.execute(
        select(DoctorAvailability).where(
            DoctorAvailability.doctor_id == doctor.id,
            DoctorAvailability.days_of_week == day_name
        )
    )
    availability = query_availability.scalars().first()
    
    if not availability:
        raise HTTPException(
            status_code=400, 
            detail=f"Doctor is not available on {day_name}s"
        )

    # 3. Check Time Range (Is 10:00 within 09:00 - 17:00?)
    if not (availability.start_time <= booking_data.appointment_time < availability.end_time):
        raise HTTPException(
            status_code=400, 
            detail=f"Doctor is only available between {availability.start_time} and {availability.end_time}"
        )

    # 4. Check for Double Booking (Is someone else already booked?)
    query_conflict = await db.execute(
        select(Appointment).where(
            and_(
                Appointment.doctor_id == doctor.id,
                Appointment.appointment_date == booking_data.appointment_date,
                Appointment.appointment_time == booking_data.appointment_time,
                Appointment.status != "CANCELLED" # Ignore cancelled slots
            )
        )
    )
    if query_conflict.scalars().first():
        raise HTTPException(status_code=409, detail="This time slot is already booked.")

    # 5. Create the Appointment
    new_appointment = Appointment(
        patient_id=current_user.id,
        doctor_id=doctor.id,
        appointment_date=booking_data.appointment_date,
        appointment_time=booking_data.appointment_time,
        status="CONFIRMED" # Auto-confirm for now
    )
    
    db.add(new_appointment)
    await db.commit()
    await db.refresh(new_appointment)
    
    return {"message": "Appointment booked successfully", "appointment_id": new_appointment.id}