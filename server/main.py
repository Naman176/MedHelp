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
import asyncio
from app.core.database import get_langgraph_db_url, keep_db_alive


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
        check=AsyncConnectionPool.check_connection,
        max_lifetime=1800,
        max_idle=300,
    )

    await pool.open()
    await pool.wait()

    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()

    app.state.chatbot_graph = build_graph(checkpointer)

    keepalive_task = asyncio.create_task(keep_db_alive(pool))

    try:
        yield
    finally:
        keepalive_task.cancel()
        try:
            await keepalive_task
        except asyncio.CancelledError:
            pass
        app.state.chatbot_graph = None
        await pool.close()

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION, lifespan=lifespan)

allowed_origins = [
    "http://localhost:5173",
    settings.FRONTEND_URL,
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(set(allowed_origins)),  # frontend origin
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