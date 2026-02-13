from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update, or_, desc
from datetime import datetime
from uuid import UUID
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.models.availability import DoctorAvailability
from app.schemas.appointment import AppointmentCreate
from typing import List
from app.schemas.appointment import AppointmentResponse, AppointmentUpdate

router = APIRouter()

@router.post("/book", status_code=status.HTTP_201_CREATED)
async def book_appointment(
    booking_data: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    # 1. Clean the time (remove milliseconds)
    clean_time = booking_data.appointment_time.replace(tzinfo=None, microsecond=0)

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
                Appointment.appointment_time == clean_time,
                Appointment.status.in_(["PENDING", "CONFIRMED"])
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
    
    return {"message": "Appointment booked successfully", "appointment_id": new_appointment.id}

@router.get("/", response_model=List[AppointmentResponse])
async def get_my_appointments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # --- STEP 1: AUTO-UPDATE PAST APPOINTMENTS ---
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

    # --- STEP 2: FETCH THE LIST ---

    # A) DOCTOR LOGIC
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

    # B) ADMIN LOGIC
    elif current_user.role == "admin":
         query = await db.execute(
            select(Appointment)
            .order_by(desc(Appointment.appointment_date))
        )
         return query.scalars().all()

    # C) PATIENT LOGIC (The Default for everyone else)
    # This catches role="patient", role="user", or any other normal user
    else:
        query = await db.execute(
            select(Appointment)
            .where(Appointment.patient_id == current_user.id)
            .order_by(desc(Appointment.appointment_date), desc(Appointment.appointment_time))
        )
        return query.scalars().all()
    
@router.put("/{appointment_id}/status", response_model=AppointmentResponse)
async def update_appointment_status(
    appointment_id: UUID,
    update_data: AppointmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Fetch the Appointment
    query = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appointment = query.scalars().first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # --- SCENARIO A: The User is the PATIENT ---
    if appointment.patient_id == current_user.id:
        
        # Rule 1: Patients can ONLY cancel.
        if update_data.status != "CANCELLED":
            raise HTTPException(status_code=400, detail="Patients can only cancel appointments.")

        # Rule 2: Patients can ONLY cancel if it is currently PENDING.
        # Once the doctor touches it (Confirmed/Rejected/Completed), the patient is locked out.
        if appointment.status != "PENDING":
             raise HTTPException(
                status_code=400, 
                detail="Cannot cancel. This appointment has already been processed by the doctor."
            )

    # --- SCENARIO B: The User is the DOCTOR ---
    else:
        # Verify this user is actually the doctor for this specific appointment
        query_doc = await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))
        doctor_record = query_doc.scalars().first()
        
        # If they are NOT the doctor (and not the patient), they are unauthorized (e.g., Admin or Hacker)
        if not doctor_record or appointment.doctor_id != doctor_record.id:
            raise HTTPException(status_code=403, detail="You are not authorized to modify this appointment.")
            
        # --- DOCTOR LOGIC STARTS HERE ---
        current_status = appointment.status
        new_status = update_data.status

        # Rule 3: Dead Ends. 
        # If it's already REJECTED, COMPLETED, or CANCELLED, nobody can change it.
        if current_status in ["REJECTED", "COMPLETED", "CANCELLED"]:
             raise HTTPException(
                status_code=400, 
                detail=f"This appointment is already {current_status} and cannot be changed."
            )

        # Rule 4: Valid Transitions Only
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

        # Rule 5: Generate Link if Confirming Virtual
        if new_status == "CONFIRMED" and appointment.appointment_type == "VIRTUAL":
            appointment.meeting_link = f"https://meet.google.com/med-help-{appointment.id}"

    # --- FINAL: Apply Update ---
    appointment.status = update_data.status
    
    await db.commit()
    await db.refresh(appointment)
    
    return appointment