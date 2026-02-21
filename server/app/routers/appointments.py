from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update, or_, desc
from datetime import datetime
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.models.availability import DoctorAvailability
from app.schemas.appointment import AppointmentCreate
from typing import List
from app.schemas.appointment import AppointmentResponse, AppointmentUpdate
from app.services.notification import send_notification

router = APIRouter()

# Book an Appointment
@router.post("/book", status_code=status.HTTP_201_CREATED)
async def book_appointment(
    booking_data: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    # Clean the time (remove milliseconds)
    clean_time = booking_data.appointment_time.replace(tzinfo=None, microsecond=0)

    now = datetime.now()
    current_date = now.date()
    current_time = now.time()

    # Check if the date is in the past
    if booking_data.appointment_date < current_date:
        raise HTTPException(
            status_code=400, 
            detail="You cannot book an appointment on a past date."
        )
        
    # Check if the date is today, but the time has already passed
    if booking_data.appointment_date == current_date and clean_time < current_time:
        raise HTTPException(
            status_code=400, 
            detail="You cannot book an appointment in the past."
        )

    # Check if Doctor exists
    query_doctor = await db.execute(select(Doctor).where(Doctor.id == booking_data.doctor_id).options(selectinload(Doctor.user)))
    doctor = query_doctor.scalars().first()

    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    if doctor.user_id == current_user.id:
        raise HTTPException(
            status_code=400, 
            detail="You cannot book an appointment with yourself."
        )
    
    # Block booking if the doctor is pending approval
    if not doctor.user.is_verified:
        raise HTTPException(
            status_code=400, 
            detail="Cannot book appointments. This doctor's profile is not verified yet."
        )

    # Check if Doctor works on this day (e.g., "Monday")
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

    # Check Time Range (Is 10:00 within 09:00 - 17:00?)
    if not (availability.start_time <= booking_data.appointment_time < availability.end_time):
        raise HTTPException(
            status_code=400, 
            detail=f"Doctor is only available between {availability.start_time} and {availability.end_time}"
        )

    # Check for Double Booking (Is someone else already booked?)
    query_conflict = await db.execute(
        select(Appointment).where(
            and_(
                Appointment.doctor_id == doctor.id,
                Appointment.appointment_date == booking_data.appointment_date,
                Appointment.appointment_time == clean_time,
                Appointment.status.in_(["PENDING", "CONFIRMED"])
            )
        )
    )
    if query_conflict.scalars().first():
        raise HTTPException(status_code=409, detail="This time slot is already booked.")

    # Create the Appointment
    new_appointment = Appointment(
        patient_id=current_user.id,
        doctor_id=doctor.id,
        appointment_date=booking_data.appointment_date,
        appointment_time=clean_time,
        status="PENDING",
        appointment_type=booking_data.appointment_type
    )
    
    db.add(new_appointment)
    try:
        await db.commit()
        await db.refresh(new_appointment)
    except IntegrityError:
        # This catches the race condition if two people book the EXACT same active slot
        await db.rollback()
        raise HTTPException(status_code=409, detail="Slot was just taken by someone else.")
    
    # Notify the Patient
    await send_notification(
        db=db,
        user_id=current_user.id,
        title="Appointment Requested",
        message=f"Your request with Dr. {doctor.user.full_name} is pending confirmation.",
        notification_type="INFO"
    )
    
    # Notify the Doctor
    await send_notification(
        db=db,
        user_id=doctor.user_id,
        title="New Booking Request",
        message=f"A patient has requested an appointment on {booking_data.appointment_date} at {clean_time}.",
        notification_type="INFO"
    )
    
    return {"message": "Appointment booked successfully", "appointment_id": new_appointment.id}

# Get All Appointments for User(Patient/Doctor)
@router.get("/", response_model=List[AppointmentResponse])
async def get_my_appointments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # AUTO-UPDATE PAST APPOINTMENTS
    now = datetime.now()
    today_date = now.date()
    current_time = now.time()

    await db.execute(
        update(Appointment)
        .where(
            Appointment.status == "CONFIRMED",
            or_(
                Appointment.appointment_date < today_date,
                and_(
                    Appointment.appointment_date == today_date,
                    Appointment.appointment_time < current_time
                )
            )
        )
        .values(status="COMPLETED")
    )
    await db.commit()

    # DOCTOR LOGIC
    if current_user.role == "doctor":
        query_doctor = await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))
        doctor = query_doctor.scalars().first()
        
        if not doctor:
            return []

        query = await db.execute(
            select(Appointment)
            .where(Appointment.doctor_id == doctor.id)
            .order_by(desc(Appointment.appointment_date), desc(Appointment.appointment_time))
        )
        return query.scalars().all()

    # PATIENT LOGIC (The Default for everyone else)
    else:
        query = await db.execute(
            select(Appointment)
            .where(Appointment.patient_id == current_user.id)
            .order_by(desc(Appointment.appointment_date), desc(Appointment.appointment_time))
        )
        return query.scalars().all()
    
# Update Appointment Status
@router.put("/{appointment_id}/status", response_model=AppointmentResponse)
async def update_appointment_status(
    appointment_id: UUID,
    update_data: AppointmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Fetch the Appointment
    query = await db.execute(select(Appointment).where(Appointment.id == appointment_id).options(
        selectinload(Appointment.doctor).selectinload(Doctor.user)
    ))
    appointment = query.scalars().first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # The User is the PATIENT
    if appointment.patient_id == current_user.id:
        
        # Patients can ONLY cancel
        if update_data.status != "CANCELLED":
            raise HTTPException(status_code=400, detail="Patients can only cancel appointments.")

        # Patients can ONLY cancel if it is currently PENDING.
        # Once the doctor touches it (Confirmed/Rejected/Completed), the patient is locked out.
        if appointment.status != "PENDING":
             raise HTTPException(
                status_code=400, 
                detail="Cannot cancel. This appointment has already been processed by the doctor."
            )

    # The User is the DOCTOR
    else:
        # Verify this user is actually the doctor for this specific appointment
        query_doc = await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))
        doctor_record = query_doc.scalars().first()
        
        # If they are NOT the doctor (and not the patient), they are unauthorized (e.g., Admin or Hacker)
        if not doctor_record or appointment.doctor_id != doctor_record.id:
            raise HTTPException(status_code=403, detail="You are not authorized to modify this appointment.")
            
        # DOCTOR LOGIC STARTS HERE
        current_status = appointment.status
        new_status = update_data.status

        # Dead Ends. 
        # If it's already REJECTED, COMPLETED, or CANCELLED, nobody can change it.
        if current_status in ["REJECTED", "COMPLETED", "CANCELLED"]:
             raise HTTPException(
                status_code=400, 
                detail=f"This appointment is already {current_status} and cannot be changed."
            )

        # Valid Transitions Only
        # PENDING   -> CONFIRMED  (Accept)
        # PENDING   -> REJECTED   (Reject)
        # CONFIRMED -> COMPLETED  (Finish)
        
        is_valid_transition = False
        
        if current_status == "PENDING" and new_status in ["CONFIRMED", "REJECTED"]:
            is_valid_transition = True
        elif current_status == "CONFIRMED" and new_status == "COMPLETED":
            is_valid_transition = True
            
        if not is_valid_transition:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid move. You cannot go from {current_status} to {new_status}."
            )

        # Generate Link if Confirming Virtual
        if new_status == "CONFIRMED" and appointment.appointment_type == "VIRTUAL":
            appointment.meeting_link = f"https://meet.google.com/med-help-{appointment.id}"

    # Apply Update
    appointment.status = update_data.status
    
    await db.commit()
    await db.refresh(appointment)

    # If the PATIENT cancelled it
    if appointment.patient_id == current_user.id and update_data.status == "CANCELLED":
        # We need the doctor's user_id to notify them
        query_doc = await db.execute(select(Doctor).where(Doctor.id == appointment.doctor_id))
        doc_record = query_doc.scalars().first()
        if doc_record:
            await send_notification(
                db=db,
                user_id=doc_record.user_id,
                title="Appointment Cancelled",
                message=f"A patient cancelled their slot on {appointment.appointment_date}.",
                notification_type="WARNING"
            )

    # If the DOCTOR changed it (Confirmed or Rejected)
    elif appointment.doctor_id == doctor_record.id:
        if update_data.status == "CONFIRMED":
            await send_notification(
                db=db,
                user_id=appointment.patient_id,
                title="Appointment Confirmed!",
                message=f"Great news! Your appointment with Dr. {appointment.doctor.user.full_name} on {appointment.appointment_date} is confirmed.",
                notification_type="SUCCESS"
            )
        elif update_data.status == "REJECTED":
            await send_notification(
                db=db,
                user_id=appointment.patient_id,
                title="Appointment Declined",
                message=f"Your appointment request for {appointment.appointment_date} could not be accepted.",
                notification_type="WARNING"
            )
    
    return appointment