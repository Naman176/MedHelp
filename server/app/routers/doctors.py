from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.doctor import Doctor
from app.core.cloudinary_utils import upload_file

router = APIRouter()

@router.post("/apply", status_code=status.HTTP_201_CREATED)
async def apply_for_doctor(
    # We use Form(...) because we are sending a file along with text
    specialization: str = Form(...),
    license_number: str = Form(...),
    experience: int = Form(...),
    consultation_fee: float = Form(...),
    bio: str = Form(None),
    degree_file: UploadFile = File(...),  # <--- The File
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Check if user is already a doctor
    if current_user.role == "doctor":
        raise HTTPException(status_code=400, detail="You are already a doctor")

    # 2. Upload the file to Cloudinary
    degree_url = upload_file(degree_file)
    if not degree_url:
        raise HTTPException(status_code=500, detail="Failed to upload degree file")

    # 3. Create the Doctor Profile
    new_doctor = Doctor(
        user_id=current_user.id,
        specialization=specialization,
        license_number=license_number,
        years_of_experience=experience,
        consultation_fee=consultation_fee,
        bio=bio,
        degree_upload_url=degree_url
    )
    
    # 4. Update User Role
    # In a real app, you might set this to "pending" until an Admin approves.
    # For now, we auto-approve:
    current_user.role = "doctor" 
    
    db.add(new_doctor)
    db.add(current_user)
    await db.commit()
    await db.refresh(new_doctor)
    
    return {
        "message": "Application submitted successfully",
        "doctor_id": new_doctor.id
    }