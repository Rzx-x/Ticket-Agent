from pydantic_settings import BaseSettings
from typing import Optional, List, Dict, Any
import os
import secrets
from datetime import datetime

class Settings(BaseSettings):
    # Basic settings
    APP_NAME: str = "OmniDesk AI Backend"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False  # Default to False for security
    
    # Instance identification
    INSTANCE_ID: str = secrets.token_hex(8)
    START_TIME: datetime = datetime.utcnow()
    
    # Database
    DATABASE_URL: str
    
    # AI Services
    ANTHROPIC_API_KEY: str
    
    # Vector Database
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    
    # External Integrations
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    GLPI_URL: Optional[str] = None
    GLPI_USER_TOKEN: Optional[str] = None
    GLPI_APP_TOKEN: Optional[str] = None
    
    SOLMAN_URL: Optional[str] = None
    SOLMAN_USERNAME: Optional[str] = None
    SOLMAN_PASSWORD: Optional[str] = None
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)  # Generate secure secret key
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    PASSWORD_HASH_ALGORITHM: str = "bcrypt"
    JWT_ALGORITHM: str = "HS256"
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # HST API
    HST_API_KEY: Optional[str] = None
    HST_API_URL: str = "https://api.hst.io"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 10
    REDIS_TIMEOUT: int = 5
    
    # CORS and Security
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    TRUSTED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()