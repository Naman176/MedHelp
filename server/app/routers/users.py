from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.user import create_user, get_user_by_email 
from app.models.user import User
from app.dependencies import get_current_user

router = APIRouter()

# This endpoint allows users to register with email and password, or via Google (if password is not provided)
@router.post("/", response_model=UserResponse)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.
    """
    # 1. Check if email already exists
    db_user = await get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 2. Create the user
    return await create_user(db=db, user=user)

# This endpoint allows users to get their own profile information
@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Validates the token, retrieves the user from the database, and returns the user's information.
    """
    return current_user

# Update profile, logout