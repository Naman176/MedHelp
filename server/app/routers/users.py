from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import timedelta
import string
import secrets

from app.core.cloudinary_utils import upload_file, delete_file
from app.core.database import get_db
from app.core.security import create_access_token
from app.schemas.user import ContactCreate, UserCreate, UserResponse
from app.schemas.token import GoogleTokenRequest
from app.services.user import create_user, get_user_by_email 
from app.models.user import User
from app.dependencies import get_current_user
from app.core.config import settings

router = APIRouter()

GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID

@router.post("/google")
async def google_auth(request: GoogleTokenRequest, db: AsyncSession = Depends(get_db)):
    try:
        # Verify the token with Google's servers
        id_info = id_token.verify_oauth2_token(
            request.token, 
            requests.Request(), 
            GOOGLE_CLIENT_ID
        )
        
        # Extract the user's info from the verified token
        email = id_info.get("email")
        name = id_info.get("name")
        
        if not email:
            raise HTTPException(status_code=400, detail="No email provided by Google")

        # Check if this user already exists
        user = await get_user_by_email(db, email=email)

        # Auto-Register new user
        if not user:
            # Generate a random 16-character dummy password
            alphabet = string.ascii_letters + string.digits
            dummy_password = ''.join(secrets.choice(alphabet) for i in range(16))
            
            user = UserCreate(
                email=email,
                full_name=name,
                password = dummy_password,
            )
            await create_user(db=db, user=user)

        # Generate standard JWT token 
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": user.email, "role": user.role}, expires_delta=access_token_expires)
        return {"access_token": access_token, "token_type": "bearer"}

    except ValueError:
        # This catches invalid or expired Google tokens
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Google Token"
        )


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