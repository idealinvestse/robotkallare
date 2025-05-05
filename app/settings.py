"""Application settings initialization.

This module handles all application settings, including loading defaults
and initialization of database settings.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlmodel import Session, select
from app.database import get_session, engine
import uuid
from sqlmodel import Field, SQLModel, Relationship, JSON, Column
from pydantic_settings import BaseSettings

class SystemSetting(SQLModel, table=True):
    """System settings that control GDial's behavior.
    These are admin-level settings that control core functionality.
    """
    key: str = Field(primary_key=True)
    value: str
    value_type: str = "string"  # string, int, float, boolean, json
    description: str
    group: str = "general"  # general, calls, sms, dtmf, integrations, etc.
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @classmethod
    def get_value(cls, session, key: str, default: Any = None) -> Any:
        setting = session.query(cls).filter(cls.key == key).first()
        if not setting:
            return default
        # Convert value to appropriate type
        if setting.value_type == "int":
            return int(setting.value)
        elif setting.value_type == "float":
            return float(setting.value)
        elif setting.value_type == "boolean":
            return setting.value.lower() in ["true", "1", "yes", "y"]
        elif setting.value_type == "json":
            import json
            return json.loads(setting.value)
        else:
            return setting.value
    
    @classmethod 
    def set_value(cls, session, key: str, value: Any, 
                 description: Optional[str] = None, 
                 group: Optional[str] = None,
                 value_type: Optional[str] = None):
        setting = session.query(cls).filter(cls.key == key).first()
        if not setting:
            setting = cls(key=key)
        setting.value = str(value)
        if value_type:
            setting.value_type = value_type
        elif not hasattr(setting, 'value_type') or not setting.value_type:
            if isinstance(value, bool):
                setting.value_type = "boolean"
            elif isinstance(value, int):
                setting.value_type = "int"
            elif isinstance(value, float):
                setting.value_type = "float"
            elif isinstance(value, dict) or isinstance(value, list):
                setting.value_type = "json"
                import json
                setting.value = json.dumps(value)
            else:
                setting.value_type = "string"
        if description:
            setting.description = description
        if group:
            setting.group = group
        setting.updated_at = datetime.now()
        session.add(setting)
        session.commit()
        return setting

class DtmfSetting(SQLModel, table=True):
    """Extended settings for DTMF response behaviors.
    Controls how DTMF responses are handled in emergency calls.
    """
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    max_attempts: int = 3
    input_timeout: int = 10
    confirm_response: bool = False
    retry_on_invalid: bool = True
    additional_digits: Optional[str] = None
    universal_gather: bool = True
    repeat_message_digit: str = "0"
    confirm_receipt_digit: str = "1"
    request_callback_digit: str = "8"
    transfer_to_live_agent_digit: str = "9"
    dtmf_menu_style: str = "standard"
    inter_digit_timeout: int = 3
    allow_message_skip: bool = True
    extra_settings: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class SmsSettings(SQLModel, table=True):
    """SMS configuration settings.
    Controls how SMS messages are formatted and sent.
    """
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    include_sender_name: bool = True
    message_prefix: str = "EMERGENCY: "
    message_suffix: str = ""
    max_length: int = 160
    split_long_messages: bool = True
    batch_delay_ms: int = 1000
    batch_size: int = 50
    status_callback_url: Optional[str] = None
    sms_rate_limit_per_second: int = 10
    allow_opt_out: bool = True
    opt_out_keyword: str = "STOP"
    delivery_report_timeout: int = 60
    fail_silently: bool = True
    sms_retry_strategy: str = "exponential"
    sms_url_shortener: bool = False
    international_sms_enabled: bool = False
    extra_settings: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class NotificationSettings(SQLModel, table=True):
    """Settings for internal system notifications.
    Controls how and when notifications are sent to admins about system events.
    """
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    admin_email: Optional[str] = None
    notify_on_emergency: bool = True
    notify_on_error: bool = True
    failure_threshold_pct: int = 10
    daily_reports: bool = False
    weekly_reports: bool = True
    alert_sound_enabled: bool = True
    admin_phone_numbers: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    webhook_url: Optional[str] = None
    usage_report_frequency: str = "weekly"
    emergency_escalation_threshold: int = 15
    extra_settings: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class SecuritySettings(SQLModel, table=True):
    """Security-related settings for the application.
    Controls security features and behavior.
    """
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    force_https: bool = True
    sensitive_data_masking: bool = True
    auto_logout_inactive_min: int = 30
    max_login_attempts: int = 5
    password_expiry_days: int = 90
    api_rate_limit: int = 100
    audit_log_retention_days: int = 365
    ip_whitelist: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    allowed_origins: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    extra_settings: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class RealtimeSettings(SQLModel, table=True):
    """Real-time AI call settings for the application.
    Controls behavior of real-time AI calls and related features.
    """
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    openai_api_key: str = ""
    voice: str = "alloy"
    system_message: str = "You are a helpful assistant representing our organization. Keep responses brief and professional."
    max_call_duration_minutes: int = 15
    use_dtmf_fallback: bool = True
    record_calls: bool = True
    greeting_message: str = "Hello, I'm an AI assistant. How can I help you today?"
    goodbye_message: str = "Thank you for calling. Have a great day!"
    call_fallback_message: str = "I'm having trouble connecting to the AI service. Please try again later."
    extra_settings: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def update(self, **kwargs):
        """Update attributes on the settings object"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()

# Setup logging
logger = logging.getLogger(__name__)

def get_system_setting(session: Session, key: str, default_value: Any = None) -> Any:
    """Get a system setting value by key.
    
    If the setting doesn't exist, returns the default value.
    
    Args:
        session: Database session
        key: Setting key
        default_value: Default value if setting doesn't exist
        
    Returns:
        The setting value or default value
    """
    setting = session.exec(
        select(SystemSetting).where(SystemSetting.key == key)
    ).first()
    
    if setting:
        return setting.value
    
    return default_value

# Default system settings - these are used if no settings exist in the database
DEFAULT_SYSTEM_SETTINGS = {
    "realtime": {
        "openai_api_key": {
            "value": "",  # Empty by default for security, must be set in environment or admin interface
            "description": "OpenAI API key for realtime calls",
            "group": "realtime"
        },
        "voice": {
            "value": "alloy",
            "description": "OpenAI voice for realtime calls (alloy, echo, fable, onyx, nova, shimmer)",
            "group": "realtime"
        },
        "system_message": {
            "value": "You are a helpful assistant representing our organization. Keep responses brief and professional.",
            "description": "System message that guides AI behavior during calls",
            "group": "realtime"
        },
        "max_call_duration_minutes": {
            "value": "15",
            "description": "Maximum duration for realtime AI calls in minutes",
            "group": "realtime"
        },
        "use_dtmf_fallback": {
            "value": "true",
            "description": "Enable fallback to DTMF if speech recognition fails",
            "group": "realtime"
        },
        "record_calls": {
            "value": "true",
            "description": "Whether to record calls for quality assurance",
            "group": "realtime"
        },
        "greeting_message": {
            "value": "Hello, I'm an AI assistant. How can I help you today?",
            "description": "Initial greeting message for realtime calls",
            "group": "realtime"
        },
        "goodbye_message": {
            "value": "Thank you for calling. Have a great day!",
            "description": "Goodbye message for realtime calls",
            "group": "realtime"
        },
        "call_fallback_message": {
            "value": "I'm having trouble connecting to the AI service. Please try again later.",
            "description": "Message to play if the AI service fails",
            "group": "realtime"
        }
    },
    "system": {
        "app_name": {
            "value": "GDial",
            "description": "Application name",
            "group": "system"
        },
        "language": {
            "value": "sv",
            "description": "Default language (sv, en)",
            "group": "system"
        },
        "public_url": {
            "value": os.getenv("PUBLIC_URL", "http://localhost:3003"),
            "description": "Public URL for the application",
            "group": "system"
        },
        "audio_directory": {
            "value": "static/audio",
            "description": "Directory for audio files",
            "group": "system"
        },
        "log_level": {
            "value": "INFO",
            "description": "Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
            "group": "system"
        },
        "environment": {
            "value": os.getenv("ENVIRONMENT", "development"),
            "description": "Environment (development, testing, production)",
            "group": "system"
        }
    },
    "calls": {
        "twilio_account_sid": {
            "value": os.getenv("TWILIO_ACCOUNT_SID", ""),
            "description": "Twilio Account SID",
            "group": "calls"
        },
        "twilio_auth_token": {
            "value": os.getenv("TWILIO_AUTH_TOKEN", ""),
            "description": "Twilio Auth Token (masked)",
            "group": "calls"
        },
        "twilio_from_number": {
            "value": os.getenv("TWILIO_FROM_NUMBER", ""),
            "description": "Twilio phone number to use as caller ID",
            "group": "calls"
        },
        "max_concurrent_calls": {
            "value": "100",
            "value_type": "int",
            "description": "Maximum number of concurrent outbound calls",
            "group": "calls"
        },
        "call_bots_count": {
            "value": "3",
            "value_type": "int",
            "description": "Number of call bots to use when making emergency calls",
            "group": "calls"
        },
        "calls_per_bot": {
            "value": "20",
            "value_type": "int",
            "description": "Maximum number of concurrent calls per bot",
            "group": "calls"
        },
        "default_voice": {
            "value": "alice",
            "description": "Default TTS voice to use",
            "group": "calls"
        },
        "call_timeout_sec": {
            "value": "25",
            "value_type": "int",
            "description": "Number of seconds before a call times out",
            "group": "calls"
        },
        "enable_call_recording": {
            "value": "false",
            "value_type": "boolean",
            "description": "Enable recording of calls",
            "group": "calls"
        },
        "call_retry_attempts": {
            "value": "2",
            "value_type": "int",
            "description": "Number of retry attempts for failed calls",
            "group": "calls"
        },
        "call_retry_delay": {
            "value": "60",
            "value_type": "int",
            "description": "Delay between retry attempts in seconds",
            "group": "calls"
        }
    },
    "bot_scaling": {
        "queue_max_size": {
            "value": "1000",
            "value_type": "int",
            "description": "Maximum queue size for call jobs",
            "group": "bot_scaling"
        },
        "queue_scaling_factor": {
            "value": "20",
            "value_type": "int", 
            "description": "Number of queued calls per bot instance",
            "group": "bot_scaling"
        },
        "worker_startup_time": {
            "value": "5",
            "value_type": "int",
            "description": "Estimated time in seconds for a new worker to start",
            "group": "bot_scaling"
        },
        "min_replicas": {
            "value": "1",
            "value_type": "int",
            "description": "Minimum number of bot instances to keep running",
            "group": "bot_scaling"
        },
        "max_replicas": {
            "value": "50",
            "value_type": "int",
            "description": "Maximum number of bot instances to scale to",
            "group": "bot_scaling"
        },
        "scaling_metric": {
            "value": "queue_length",
            "description": "Metric used for scaling (queue_length, active_calls, combined)",
            "group": "bot_scaling"
        },
        "scale_down_delay": {
            "value": "5",
            "value_type": "int",
            "description": "Minutes to wait before scaling down workers",
            "group": "bot_scaling"
        }
    },
    "queue": {
        "queue_type": {
            "value": "rabbitmq",
            "description": "Type of message queue to use (rabbitmq, internal)",
            "group": "queue"
        },
        "queue_host": {
            "value": "localhost",
            "description": "Host for the message queue",
            "group": "queue"
        },
        "queue_port": {
            "value": "5672",
            "value_type": "int",
            "description": "Port for the message queue",
            "group": "queue"
        },
        "queue_name": {
            "value": "ringbot.jobs",
            "description": "Name of the call job queue",
            "group": "queue"
        },
        "queue_username": {
            "value": "guest",
            "description": "Username for the message queue",
            "group": "queue"
        },
        "queue_password": {
            "value": "guest",
            "description": "Password for the message queue",
            "group": "queue"
        }
    },
    "tts": {
        "tts_engine": {
            "value": "google",
            "description": "Text-to-speech engine (google, amazon, coqui)",
            "group": "tts"
        },
        "tts_language": {
            "value": "sv-SE",
            "description": "TTS language code",
            "group": "tts"
        },
        "tts_voice": {
            "value": "sv-SE-Wavenet-A",
            "description": "Voice ID for the TTS engine",
            "group": "tts"
        },
        "tts_cache_enabled": {
            "value": "true",
            "value_type": "boolean",
            "description": "Enable caching of TTS audio",
            "group": "tts"
        },
        "tts_cache_size": {
            "value": "100",
            "value_type": "int",
            "description": "Maximum number of cached TTS files",
            "group": "tts"
        }
    }
}

def initialize_settings():
    """Initialize all application settings.
    
    This function loads default settings if the database is empty.
    """
    try:
        session = Session(engine)
        
        # Check if we have any system settings
        existing_settings = session.query(SystemSetting).count()
        
        if existing_settings == 0:
            logger.info("No settings found in database. Initializing with defaults.")
            # Create default settings
            for category, settings in DEFAULT_SYSTEM_SETTINGS.items():
                for key, setting_data in settings.items():
                    value = setting_data["value"]
                    value_type = setting_data.get("value_type")
                    description = setting_data["description"]
                    group = setting_data["group"]
                    
                    SystemSetting.set_value(
                        session=session,
                        key=key,
                        value=value,
                        value_type=value_type,
                        description=description,
                        group=group
                    )
            
            # Create DTMF settings
            dtmf_settings = DtmfSetting()
            session.add(dtmf_settings)
            
            # Create SMS settings
            sms_settings = SmsSettings()
            session.add(sms_settings)
            
            # Create notification settings
            notification_settings = NotificationSettings()
            session.add(notification_settings)
            
            # Create security settings
            security_settings = SecuritySettings()
            session.add(security_settings)
            
            # Commit all settings
            session.commit()
            logger.info("Default settings initialized successfully")
        else:
            logger.info("Database already contains data, skipping initialization.")
        
        session.close()
        return True
    except Exception as e:
        logger.error(f"Failed to initialize settings: {str(e)}", exc_info=True)
        return False

def get_dtmf_settings(session: Session) -> Optional[DtmfSetting]:
    """Get DTMF settings from database."""
    return session.query(DtmfSetting).first()

def get_sms_settings(session: Session) -> Optional[SmsSettings]:
    """Get SMS settings from database."""
    return session.query(SmsSettings).first()

def get_notification_settings(session: Session) -> Optional[NotificationSettings]:
    """Get notification settings from database."""
    return session.query(NotificationSettings).first()

def get_security_settings(session: Session) -> SecuritySettings:
    """Get security settings from database."""
    return session.query(SecuritySettings).first() or SecuritySettings()

def get_realtime_settings(session: Session) -> RealtimeSettings:
    """Get realtime AI call settings from database."""
    return session.query(RealtimeSettings).first() or RealtimeSettings()

def get_settings_by_group(session: Session, group_name: Optional[str] = None) -> Dict[str, List[SystemSetting]]:
    """Get settings organized by group."""
    if group_name:
        settings = session.query(SystemSetting).filter(SystemSetting.group == group_name).all()
        return {group_name: settings}
    
    # Get all settings and organize by group
    settings = session.query(SystemSetting).all()
    settings_by_group = {}
    
    for setting in settings:
        if setting.group not in settings_by_group:
            settings_by_group[setting.group] = []
        settings_by_group[setting.group].append(setting)
    
    return settings_by_group

# --- Environment-based Settings --- 
class AppSettings(BaseSettings):
    # Database
    DATABASE_URL: Optional[str] = "sqlite:///./gdial.db" # Default to SQLite if not set

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@localhost/"
    
    # Logging
    LOG_LEVEL: str = "INFO"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Scheduler Intervals (in minutes)
    AUDIO_CACHE_CLEANUP_INTERVAL_MINUTES: int = 60
    BURN_MESSAGE_CLEANUP_INTERVAL_MINUTES: int = 15

    # Twilio Credentials
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    TWILIO_FROM_NUMBER: Optional[str] = None

    # Security / JWT
    SECRET_KEY: str = "a_very_secret_key_needs_to_be_set_in_env_for_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None

    # Add other environment variables identified from errors or known requirements
    # (Adjust types as needed, e.g., int, bool)
    AUDIO_DIR: str = "static/audio" # Example from errors
    MAX_SECONDARY_ATTEMPTS: Optional[int] = None # Example from errors
    OPENAI_TTS_MODEL: Optional[str] = None # Example from errors

    # More variables from latest errors
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    BASE_URL: str = "http://localhost:8000"
    PUBLIC_URL: Optional[str] = None # Often same as BASE_URL if not behind proxy
    SQLITE_DB: Optional[str] = "sqlite:///./gdial.db" # Likely redundant if DATABASE_URL is used
    CALL_TIMEOUT_SEC: int = 30
    SECONDARY_BACKOFF_SEC: int = 60


    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

# Instantiate the settings object to be imported by other modules
settings = AppSettings()

logger.info(f"AppSettings loaded. Log Level: {settings.LOG_LEVEL}, CORS Origins: {settings.CORS_ORIGINS}")