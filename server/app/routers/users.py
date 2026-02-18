from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.cloudinary_utils import upload_file, delete_file
from app.core.database import get_db
from app.schemas.user import ContactCreate, UserCreate, UserResponse
from app.services.user import create_user, get_user_by_email 
from app.models.user import User
from app.dependencies import get_current_user

router = APIRouter()

# Register User
@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if email already exists
    db_user = await get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create the user
    return await create_user(db=db, user=user)

# Get User Profile
@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# Update User Profile
@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    full_name: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    profile_picture: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Update text fields if provided
    if full_name:
        current_user.full_name = full_name
    if phone_number:
        # Check if it only contains numbers (and optionally a leading '+')
        clean_phone = phone_number.replace("+", "")
        if not clean_phone.isdigit():
            raise HTTPException(status_code=400, detail="Phone number can only contain numbers.")
        current_user.phone_number = phone_number
        
    # Upload and update profile picture if provided
    if profile_picture:
        # Delete old pic if it exists and isn't the default blank avatar
        if current_user.profile_picture and "pixabay.com" not in current_user.profile_picture:
            delete_file(current_user.profile_picture)
            
        # Upload the new one to the specific folder
        image_url = upload_file(profile_picture, folder="medhelp_profiles")
        
        if not image_url:
            raise HTTPException(status_code=500, detail="Failed to upload profile picture")
            
        current_user.profile_picture = image_url

    # Save to database
    await db.commit()
    await db.refresh(current_user)
    
    return current_user

# Contact Us Route
@router.post("/contact")
async def submit_contact_form(contact_data: ContactCreate):
    """
    Accepts queries from the public 'Contact Us' form.
    """
    # Note: In a full production app, you would save this to a Contact table in the DB, 
    # or use a library like fastapi-mail to send an actual email to the Admin. 
    # For now, we will simulate a successful submission.
    
    print(f"New Message from {contact_data.name} ({contact_data.email}): {contact_data.subject}")
    
    return {
        "status": "success",
        "message": "Thank you for reaching out! Your query has been received and our team will get back to you shortly."
    }