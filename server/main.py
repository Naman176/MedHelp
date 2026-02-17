from fastapi import FastAPI
from app.core.config import settings
from app.routers import users, auth, doctors, appointments, admin
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)
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

@app.get("/health")
def health():
    return {"message": "Hello! The Medical App backend is alive."}