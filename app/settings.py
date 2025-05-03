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
from app.models.settings import SystemSetting, DtmfSetting, SmsSettings, NotificationSettings, SecuritySettings

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

def get_security_settings(session: Session) -> Optional[SecuritySettings]:
    """Get security settings from database."""
    return session.query(SecuritySettings).first()

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