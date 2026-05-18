from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
import asyncio
from psycopg_pool import AsyncConnectionPool


def get_langgraph_db_url() -> str:
    """
    Convert the existing SQLAlchemy asyncpg URL into a Psycopg-compatible
    URL for LangGraph's AsyncPostgresSaver.

    Original app DB URL:
        postgresql+asyncpg://...

    LangGraph/PostgresSaver DB URL:
        postgresql://...
    """
    url = settings.DATABASE_URL

    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://", 1)

    elif url.startswith("postgres+asyncpg://"):
        url = url.replace("postgres+asyncpg://", "postgresql://", 1)

    # Neon requires SSL for remote Postgres connections.
    # Add SSL params only to the derived LangGraph URL, not to settings.DATABASE_URL.
    if "sslmode=" not in url:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}sslmode=require&channel_binding=require"

    return url


async def keep_db_alive(pool: AsyncConnectionPool):
    """
    Pings DB every 4 minutes to prevent idle connection timeout.
    """
    while True:
        await asyncio.sleep(240)
        try:
            async with pool.connection() as conn:
                await conn.execute("SELECT 1")
        except Exception:
            pass


# 1. Create the Async Engine
# We use settings.DATABASE_URL from your config file
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
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