from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, select
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.models.user import User
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.dependencies import verify_admin
from app.schemas.admin import PendingDoctorResponse, RejectDoctorRequest, VerifyDoctorResponse
from app.schemas.user import UserResponse
from app.schemas.appointment import AppointmentResponse
from app.core.cloudinary_utils import delete_file
from app.services.notification import send_notification

router = APIRouter()

# GET PENDING DOCTORS
@router.get("/doctors/pending", response_model=List[PendingDoctorResponse])
async def get_pending_doctors(
    admin: User = Depends(verify_admin), 
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Doctor)
        .join(Doctor.user)
        .where(User.is_verified == False)
        .options(selectinload(Doctor.user))
    )
    
    result = await db.execute(query)
    return result.scalars().all()

# APPROVE A DOCTOR
@router.patch("/doctors/{doctor_id}/verify", response_model=VerifyDoctorResponse)
async def verify_doctor(
    doctor_id: UUID,
    admin: User = Depends(verify_admin), 
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Doctor)
        .where(Doctor.id == doctor_id)
        .options(selectinload(Doctor.user))
    )
    result = await db.execute(query)
    doctor = result.scalars().first()
    
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
        
    if doctor.user.is_verified:
        raise HTTPException(status_code=400, detail="Doctor is already verified")
    
    doctor.user.is_verified = True
    doctor.user.role = "doctor"

    await db.commit()

    await send_notification(
        db=db,
        user_id=doctor.user_id,
        title="Profile Verified",
        message="Congratulations! Your medical profile is approved. You can now accept bookings.",
        notification_type="SUCCESS"
    )
    
    return {
        "message": f"Doctor {doctor.user.full_name} has been successfully verified.", 
        "doctor_id": doctor.id
    }

# REJECT A DOCTOR APPLICATION
@router.patch("/doctors/{doctor_id}/reject", response_model=VerifyDoctorResponse)
async def reject_doctor(
    doctor_id: UUID,
    payload: RejectDoctorRequest,
    admin: User = Depends(verify_admin), 
    db: AsyncSession = Depends(get_db)
) -> dict:
    
    query = (
        select(Doctor)
        .where(Doctor.id == doctor_id)
        .options(selectinload(Doctor.user))
    )
    result = await db.execute(query)
    doctor = result.scalars().first()
    
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
        
    if doctor.user.is_verified:
        raise HTTPException(status_code=400, detail="Cannot reject a doctor who is already verified.")
    
    await send_notification(
        db=db,
        user_id=doctor.user_id,
        title="Application Declined",
        message=f"Your application to join as a doctor was not approved. Reason: {payload.reason}",
        notification_type="WARNING"
    )

    # Delete the uploaded document from Cloudinary here
    if doctor.degree_upload_url:
        delete_file(doctor.degree_upload_url)

    # Delete the pending doctor record so they can apply again with correct info
    await db.delete(doctor)
    await db.commit()
    
    return {
        "message": f"Doctor {doctor.user.full_name}'s application has been rejected and they have been notified.", 
        "doctor_id": doctor_id
    }

# Delete User
@router.delete("/users/{user_id}", tags=["Admin"])
async def delete_user(
    user_id: UUID,
    admin: User = Depends(verify_admin), 
    db: AsyncSession = Depends(get_db)
):
    # Prevent admins from accidentally deleting themselves
    if user_id == admin.id:
        raise HTTPException(
            status_code=400, 
            detail="You cannot delete your own admin account."
        )

    # Find the user in the database
    query = await db.execute(select(User).where(User.id == user_id))
    user_to_delete = query.scalars().first()
    
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found.")
    
    query_doctor = await db.execute(select(Doctor).where(Doctor.user_id == user_id))
    doctor_to_delete = query_doctor.scalars().first()

    if user_to_delete.profile_picture and "pixabay.com" not in user_to_delete.profile_picture:
        delete_file(user_to_delete.profile_picture)

    if doctor_to_delete and doctor_to_delete.degree_upload_url:
        delete_file(doctor_to_delete.degree_upload_url)

    # Delete the user (SQLAlchemy cascade will handle their doctor profile/appointments)
    await db.delete(user_to_delete)
    await db.commit()
    
    return {
        "message": f"User '{user_to_delete.email}' and all associated data have been permanently deleted.",
        "deleted_user_id": user_to_delete.id
    }

# Get All Users
@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    current_user: User = Depends(verify_admin),
    db: AsyncSession = Depends(get_db)
):
    query = await db.execute(select(User).order_by(desc(User.created_at)))
    return query.scalars().all()

# Get All Appointments
@router.get("/appointments", response_model=List[AppointmentResponse])
async def get_all_appointments(
    current_user: User = Depends(verify_admin),
    db: AsyncSession = Depends(get_db)
):
    query = await db.execute(
        select(Appointment)
        .options(selectinload(Appointment.doctor), selectinload(Appointment.patient))
        .order_by(desc(Appointment.appointment_date), desc(Appointment.appointment_time))
    )
    return query.scalars().all()