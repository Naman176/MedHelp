from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.models.user import User
from app.models.doctor import Doctor
from app.dependencies import verify_admin
from app.schemas.admin import PendingDoctorResponse, VerifyDoctorResponse
from app.core.cloudinary_utils import delete_file

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
    
    return {
        "message": f"Doctor {doctor.user.full_name} has been successfully verified.", 
        "doctor_id": doctor.id
    }

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