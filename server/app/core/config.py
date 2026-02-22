from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Medical Appointment App"
    PROJECT_VERSION: str = "1.0.0"
    
    # This must match the variable in your .env file
    DATABASE_URL: str
    
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    DAILY_API_KEY: str
    GOOGLE_CLIENT_ID: str

    class Config:
        env_file = ".env"

settings = Settings()