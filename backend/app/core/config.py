"""
Configuration settings for SCOUT Backend
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True

    # Database Configuration
    DATABASE_URL: str = "postgresql://scout:scout_dev_password@localhost:5432/scout"

    # Data Storage
    DATA_ROOT: str = "./data"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: str = "pdf,docx"

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    # Security
    ENCRYPTION_KEY: str = "change_me_32_chars_long_key_here"
    SECRET_KEY: str = "your_secret_key_here_make_it_long_and_random"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "./logs/scout.log"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # PII Protection
    PII_REDACTION_ENABLED: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env


# Global settings instance
settings = Settings()