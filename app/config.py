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
    
    # OpenAI TTS
    OPENAI_TTS_MODEL: str = os.getenv("OPENAI_TTS_MODEL", "tts-1")
    AUDIO_DIR: str = os.getenv("AUDIO_DIR", "static/audio")
    VOICE: str = os.getenv("VOICE", "alloy") # Note: OpenAI has different voice names for TTS vs Realtime

    # OpenAI (for realtime calls)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    REALTIME_VOICE: str = os.getenv("REALTIME_VOICE", "alloy")
    REALTIME_SYSTEM_MESSAGE: str = os.getenv("REALTIME_SYSTEM_MESSAGE", 
        "You are a helpful assistant representing our organization. Keep responses brief and professional.")
    REALTIME_ENABLED: bool = os.getenv("REALTIME_ENABLED", "False").lower() == "true"
    # Database
    SQLITE_DB: str = "sqlite:///./dialer.db"
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "DEBUG")
    # Auth/JWT
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

@lru_cache
def get_settings() -> Settings:
    return Settings()
