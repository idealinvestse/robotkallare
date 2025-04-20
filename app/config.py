import os
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Runtime
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "3003"))
    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_FROM_NUMBER: str
    # Call logic
    CALL_TIMEOUT_SEC: int = 25
    SECONDARY_BACKOFF_SEC: int = 120
    MAX_SECONDARY_ATTEMPTS: int = 1
    # Database
    SQLITE_DB: str = "sqlite:///./dialer.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings() -> Settings:
    return Settings()
