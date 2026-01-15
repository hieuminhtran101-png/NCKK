import os
from pydantic import BaseModel, field_validator

class Settings(BaseModel):
    PROJECT_NAME: str = "Book Management API"
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "fastapi_books")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "super-secret-key-32-chars-minimum-here!!!")
    HF_API_KEY: str = os.getenv("HF_API_KEY", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    @field_validator('JWT_SECRET_KEY')
    @classmethod
    def validate_jwt_secret(cls, v):
        if len(v) < 32:
            raise ValueError('JWT_SECRET_KEY must be at least 32 characters')
        return v

class Config:
    env_file = ".env"
    case_sensitive = True

settings = Settings()
    