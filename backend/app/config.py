import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./faturamento.db"
    
    # Storage
    cloudinary_name: str = ""
    cloudinary_key: str = ""
    cloudinary_secret: str = ""
    
    # Email
    sendgrid_api_key: str = ""
    
    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    allowed_origins: str = "http://localhost:5173"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # App
    debug: bool = True
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )

settings = Settings()
