from fastapi import FastAPI
from app.core.config import settings
from app.routers import users, auth, doctors

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

# Include routers
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(doctors.router, prefix="/doctors", tags=["Doctors"])

@app.get("/health")
def health():
    return {"message": "Hello! The Medical App backend is alive."}