from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import time
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID
from sqlalchemy.exc import IntegrityError

from app.models.availability import DoctorAvailability
from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.doctor import Doctor
from app.core.cloudinary_utils import delete_file, upload_file
from app.schemas.doctor import AvailabilityCreate, DoctorAvailabilityRead, DoctorResponse

router = APIRouter()

# Apply for Doctor
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
    
    query = await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))
    existing_application = query.scalars().first()
    
    if existing_application:
        raise HTTPException(
            status_code=400, 
            detail="You have already submitted a doctor application."
        )
    
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
    
    db.add(new_doctor)

    try:
        await db.commit()
        await db.refresh(new_doctor)
    except IntegrityError:
        await db.rollback() 
        
        try:
            delete_file(degree_url) 
        except Exception as e:
            print(f"Failed to clean up Cloudinary file: {e}")

        raise HTTPException(
            status_code=400, 
            detail="A doctor with this license number already exists in our system."
        )
    
    return {
        "message": "Application submitted successfully",
        "doctor_id": new_doctor.id
    }

# Set Doctor Availability
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
    
    if not current_user.is_verified:
        raise HTTPException(
            status_code=403, 
            detail="Your profile must be verified by an admin before you can set availability."
        )
    
    # Get Doctor ID
    query = await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))
    doctor = query.scalars().first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")

    start_h = availability_data.start_time.hour
    start_m = availability_data.start_time.minute
    
    end_h = availability_data.end_time.hour
    end_m = availability_data.end_time.minute

    total_start_mins = (start_h * 60) + start_m
    total_end_mins = (end_h * 60) + end_m

    if total_end_mins <= total_start_mins:
        raise HTTPException(
            status_code=400,
            detail="End time must be strictly after the start time."
        )

    # Enforce a minimum working duration (e.g., 60 minutes)
    min_working_minutes = 60 
    if (total_end_mins - total_start_mins) < min_working_minutes:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum availability block must be at least {min_working_minutes} minutes."
        )

    # Create a row for EACH day in the list
    new_days = []
    for day in availability_data.days_of_week:
        slot = DoctorAvailability(
            doctor_id=doctor.id,
            days_of_week=day.capitalize(), 
            start_time=availability_data.start_time,
            end_time=availability_data.end_time
        )
        db.add(slot)
        new_days.append(day)

    await db.commit()
    
    return {
        "message": f"Availability set for {len(new_days)} days",
        "days": new_days
    }

# Get All Doctors
@router.get("/")
async def get_all_doctors(db: AsyncSession = Depends(get_db)):
    # JOIN Doctor and User, and filter by User.is_verified == True
    query = (
        select(Doctor)
        .join(Doctor.user)
        .where(User.is_verified == True, User.is_active == True) # Only active & verified
        .options(selectinload(Doctor.user))
    )
    
    result = await db.execute(query)
    verified_doctors = result.scalars().all()
    
    return verified_doctors

# Get availability of a particular doctor
@router.get("/{doctor_id}/availability", response_model=List[DoctorAvailabilityRead])
async def get_doctor_availability(
    doctor_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    # Check if the doctor exists
    query_doc = await db.execute(select(Doctor).where(Doctor.id == doctor_id).options(selectinload(Doctor.user)))
    doctor = query_doc.scalars().first()
    
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    if not doctor.user.is_verified:
        raise HTTPException(
            status_code=403, 
            detail="This doctor is not verified yet. Availability cannot be viewed."
        )

    # Fetch their schedule
    query_avail = await db.execute(
        select(DoctorAvailability).where(DoctorAvailability.doctor_id == doctor_id)
    )
    schedule = query_avail.scalars().all()
    
    return schedule

# Get Doctor's Professional Profile
@router.get("/me", response_model=DoctorResponse)
async def get_doctor_profile_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only doctors have a professional profile."
        )

    query = await db.execute(
        select(Doctor)
        .where(Doctor.user_id == current_user.id)
        .options(selectinload(Doctor.user))
    )
    doctor = query.scalars().first()
    
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Doctor profile not found."
        )
    
    return doctor

# Search Doctor by Name/Specialization
@router.get("/search", response_model=List[DoctorResponse])
async def search_doctors(
    name: Optional[str] = Query(None, description="Search by doctor's full name"),
    specialization: Optional[str] = Query(None, description="Filter by specialization (e.g., Dentist)"),
    current_user: User = Depends(get_current_user), # Patient must be logged in
    db: AsyncSession = Depends(get_db)
):
    # BASE QUERY: Join User model so we can check verification AND search by name
    query = select(Doctor).join(Doctor.user).where(User.is_verified == True)
    
    # DYNAMIC FILTERS
    if name:
        # Searches the connected User table for the doctor's name
        query = query.where(User.full_name.ilike(f"%{name}%"))
        
    if specialization:
        # Searches the Doctor table for their field of medicine
        query = query.where(Doctor.specialization.ilike(f"%{specialization}%"))

    # Execute and load the nested user relationship to get name, email, etc.
    query = query.options(selectinload(Doctor.user))
    result = await db.execute(query)
    
    return result.scalars().all()