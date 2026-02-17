from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash

# Get user by email (to check if they already exist)
async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

# Create a new user
async def create_user(db: AsyncSession, user: UserCreate):

    # Hash the password if it exists
    hashed_password = get_password_hash(user.password) if user.password else None

    # Convert Pydantic model to DB model
    db_user = User(
        email=user.email,
        full_name=user.full_name,
        password_hash=hashed_password,
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user