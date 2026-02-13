from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import time
from typing import List

from app.models.availability import DoctorAvailability
from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.doctor import Doctor
from app.core.cloudinary_utils import upload_file
from app.schemas.doctor import AvailabilityCreate

router = APIRouter()

# verification from admin left
# apply wala test karna hai becoiz cloudinary was added
@router.post("/apply", status_code=status.HTTP_201_CREATED)
async def apply_for_doctor(
    # We use Form(...) because we are sending a file along with text
    specialization: str = Form(...),
    license_number: str = Form(...),
    experience: int = Form(...),
    consultation_fee: float = Form(...),
    bio: str = Form(None),
    degree_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Check if user is already a doctor
    if current_user.role == "doctor":
        raise HTTPException(status_code=400, detail="You are already a doctor")

    # Upload the file to Cloudinary
    degree_url = upload_file(degree_file)
    if not degree_url:
        raise HTTPException(status_code=500, detail="Failed to upload degree file")

    # Create the Doctor Profile
    new_doctor = Doctor(
        user_id=current_user.id,
        specialization=specialization,
        license_number=license_number,
        years_of_experience=experience,
        consultation_fee=consultation_fee,
        bio=bio,
        degree_upload_url=degree_url
    )
    
    # Update User Role
    current_user.role = "doctor" 
    
    db.add(new_doctor)
    db.add(current_user)
    await db.commit()
    await db.refresh(new_doctor)
    
    return {
        "message": "Application submitted successfully",
        "doctor_id": new_doctor.id
    }

@router.post("/availability")
async def set_availability(
    availability_data: AvailabilityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Input: 
    { "days_of_week": ["Monday", "Wednesday"], "start_time": "09:00", "end_time": "17:00" }
    """
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can set availability")
    
    # Get Doctor ID
    query = await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))
    doctor = query.scalars().first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")

    # Parse times
    start_h, start_m = map(int, availability_data.start_time.split(":"))
    end_h, end_m = map(int, availability_data.end_time.split(":"))

    # Create a row for EACH day in the list
    new_days = []
    for day in availability_data.days_of_week:
        # (Optional) Check if day already exists and update it? 
        # For now, let's just add new ones.
        slot = DoctorAvailability(
            doctor_id=doctor.id,
            days_of_week=day.capitalize(), 
            start_time=time(start_h, start_m),
            end_time=time(end_h, end_m)
        )
        db.add(slot)
        new_days.append(day)

    await db.commit()
    
    return {
        "status": "success", 
        "message": f"Availability set for {len(new_days)} days",
        "days": new_days
    }