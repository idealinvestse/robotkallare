import os
import logging
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "DEBUG"),
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("gdial.log")
    ]
)

class Settings(BaseSettings):
    # Runtime
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "3003"))
    PUBLIC_URL: str = os.getenv("PUBLIC_URL", "http://titanic.urem.org:3003")
    BASE_URL: str = os.getenv("BASE_URL", "http://titanic.urem.org:3003")  # Base URL for link generation
    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_FROM_NUMBER: str
    SKIP_TWILIO_VALIDATION: bool = os.getenv("SKIP_TWILIO_VALIDATION", "True").lower() == "true"
    # Call logic
    CALL_TIMEOUT_SEC: int = 25
    SECONDARY_BACKOFF_SEC: int = 120
    MAX_SECONDARY_ATTEMPTS: int = 1
    # Database
    SQLITE_DB: str = "sqlite:///./dialer.db"
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "DEBUG")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

@lru_cache
def get_settings() -> Settings:
    return Settings()
