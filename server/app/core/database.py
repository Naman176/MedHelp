from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# 1. Create the Async Engine
# We use settings.DATABASE_URL from your config file
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Set to False in production
    future=True
)

# 2. Create the Session Factory
# This generates a new database session for every request
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 3. Base Class
# All your future database models (User, Appointment) will inherit from this
Base = declarative_base()

# 4. Dependency Injection
# This is the function you will use in your API routes to access the DB
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()