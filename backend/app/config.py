import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Employee Burnout Early-Warning & Intervention System"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-for-burnout-mvp-2026-change-in-prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days for MVP ease
    
    # Database: Default to SQLite for easy local dev, PostgreSQL supported
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./burnout_system.db")
    
    # K-Anonymity threshold for HR reports
    K_ANONYMITY_THRESHOLD: int = 5
    
    # Default CBI Cut-offs
    LOW_MODERATE_CUTOFF: float = 35.0
    HIGH_CUTOFF: float = 50.0
    
    class Config:
        case_sensitive = True

settings = Settings()
