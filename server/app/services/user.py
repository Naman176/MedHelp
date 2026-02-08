from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash

# 1. Get user by email (to check if they already exist)
async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

# 2. Create a new user
async def create_user(db: AsyncSession, user: UserCreate):

    # Hash the password if it exists
    hashed_password = get_password_hash(user.password) if user.password else None

    # Convert Pydantic model to DB model
    db_user = User(
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        password_hash=hashed_password,
        phone_number=user.phone_number,
        profile_picture=user.profile_picture
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user