from fastapi import FastAPI
from app.core.config import settings
from app.routers import users, auth, doctors, appointments, admin, notifications
from fastapi.middleware.cors import CORSMiddleware
from app.chatbot import router as chatbot_router
from contextlib import asynccontextmanager
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.chatbot.agent.graph import build_graph
from psycopg.rows import dict_row
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    langgraph_db_url = get_langgraph_db_url()
    connection_kwargs = {
        "autocommit": True,
        "prepare_threshold": 0,
        "row_factory": dict_row,
    }

    pool = AsyncConnectionPool(
        conninfo=langgraph_db_url,
        min_size=1,
        max_size=5,
        kwargs=connection_kwargs,
        open=False,
    )

    await pool.open()

    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()

    app.state.chatbot_graph = build_graph(checkpointer)
    try:
        yield
    finally:
        app.state.chatbot_graph = None
        await pool.close()

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # allow POST, GET, OPTIONS, etc
    allow_headers=["*"],
)
# Include routers
app.include_router(users.router, prefix="/user", tags=["Users"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(doctors.router, prefix="/doctors", tags=["Doctors"])
app.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
app.include_router(chatbot_router.router, prefix="/chatbot", tags=["Chatbot"])

@app.get("/health")
def health():
    return {"message": "Hello! The Medical App backend is alive."}