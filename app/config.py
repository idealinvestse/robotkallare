"""Secure configuration management for GDial application.

This module provides environment-based configuration with proper validation
and security enforcement. No hardcoded secrets are allowed.
"""
import os
import logging
import secrets
from functools import lru_cache
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("gdial.log")
    ]
)

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Application settings with environment variable enforcement.
    
    All critical settings must be provided via environment variables.
    No hardcoded secrets or production values are allowed.
    """
    
    # Environment and Runtime
    ENVIRONMENT: str = Field(default="development")
    API_HOST: str = Field(default="127.0.0.1")
    API_PORT: int = Field(default=8000)
    PUBLIC_URL: Optional[str] = Field(default=None)
    BASE_URL: str = Field(default="http://localhost:8000")
    
    # Security - NO DEFAULTS for production secrets
    SECRET_KEY: str = Field(..., min_length=32)
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    
    # Twilio - Required for core functionality
    TWILIO_ACCOUNT_SID: str = Field(..., min_length=34)
    TWILIO_AUTH_TOKEN: str = Field(..., min_length=32)
    TWILIO_FROM_NUMBER: str = Field(..., regex=r'^\+[1-9]\d{1,14}$')
    SKIP_TWILIO_VALIDATION: bool = Field(default=False)
    
    # Call Configuration
    CALL_TIMEOUT_SEC: int = Field(default=25, ge=10, le=300)
    SECONDARY_BACKOFF_SEC: int = Field(default=60, ge=30, le=600)
    MAX_SECONDARY_ATTEMPTS: int = Field(default=1, ge=0, le=5)
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./gdial.db")
    
    # RabbitMQ
    RABBITMQ_URL: str = Field(default="amqp://guest:guest@localhost/")
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    OPENAI_TTS_MODEL: str = Field(default="tts-1")
    VOICE: str = Field(default="alloy")
    
    # File Storage
    AUDIO_DIR: str = Field(default="static/audio")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    
    # CORS Configuration
    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://127.0.0.1:3000")
    
    # Cleanup Intervals (in minutes)
    AUDIO_CACHE_CLEANUP_INTERVAL_MINUTES: int = Field(default=60)
    BURN_MESSAGE_CLEANUP_INTERVAL_MINUTES: int = Field(default=15)
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=True
    )
    
    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate that SECRET_KEY is not a default/example value."""
        forbidden_values = [
            "a_very_secret_key_needs_to_be_set_in_env_for_production",
            "your_secret_key_here",
            "change_me",
            "secret",
            "your_32_character_secret_key_here"
        ]
        
        if v in forbidden_values:
            raise ValueError(
                "SECRET_KEY must be set to a secure value. "
                "Use a cryptographically secure random string."
            )
        
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        
        return v
    
    @field_validator('TWILIO_ACCOUNT_SID')
    @classmethod
    def validate_twilio_account_sid(cls, v: str) -> str:
        """Validate Twilio Account SID format."""
        if not v.startswith('AC') or len(v) != 34:
            raise ValueError("TWILIO_ACCOUNT_SID must be a valid Twilio Account SID (starts with 'AC' and 34 characters long)")
        return v
    
    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith(('sqlite:///', 'postgresql://', 'mysql://', 'mariadb://')):
            raise ValueError("DATABASE_URL must be a valid database connection string")
        return v
    
    @field_validator('ENVIRONMENT')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        valid_environments = ['development', 'testing', 'staging', 'production']
        if v not in valid_environments:
            raise ValueError(f"ENVIRONMENT must be one of: {', '.join(valid_environments)}")
        return v
    
    @classmethod
    def generate_secret_key(cls) -> str:
        """Generate a secure secret key for development use.
        
        Returns:
            A cryptographically secure random string
        """
        return secrets.token_urlsafe(32)
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"

@lru_cache
def get_settings() -> Settings:
    return Settings()
