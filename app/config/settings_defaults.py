"""Default system settings configuration."""
import os
from typing import Dict, Any


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
        "timezone": {
            "value": "Europe/Stockholm",
            "description": "Default timezone",
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
            "description": "Twilio Auth Token",
            "group": "calls"
        },
        "twilio_from_number": {
            "value": os.getenv("TWILIO_FROM_NUMBER", ""),
            "description": "Twilio phone number to call from",
            "group": "calls"
        },
        "max_concurrent_calls": {
            "value": "10",
            "value_type": "int",
            "description": "Maximum number of concurrent calls",
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
            "description": "Whether to record calls",
            "group": "calls"
        },
        "max_retry_attempts": {
            "value": "3",
            "value_type": "int",
            "description": "Maximum number of retry attempts for failed calls",
            "group": "calls"
        },
        "call_retry_delay": {
            "value": "60",
            "value_type": "int",
            "description": "Delay between retry attempts in seconds",
            "group": "calls"
        }
    },
    
    "sms": {
        "enable_sms": {
            "value": "true",
            "value_type": "boolean",
            "description": "Whether SMS functionality is enabled",
            "group": "sms"
        },
        "max_sms_length": {
            "value": "160",
            "value_type": "int",
            "description": "Maximum SMS message length",
            "group": "sms"
        },
        "enable_unicode_sms": {
            "value": "true",
            "value_type": "boolean",
            "description": "Whether to enable Unicode in SMS",
            "group": "sms"
        },
        "sms_retry_attempts": {
            "value": "3",
            "value_type": "int",
            "description": "Number of retry attempts for failed SMS",
            "group": "sms"
        },
        "sms_rate_limit": {
            "value": "100",
            "value_type": "int",
            "description": "SMS rate limit per minute",
            "group": "sms"
        }
    },
    
    "dtmf": {
        "enable_dtmf": {
            "value": "true",
            "value_type": "boolean",
            "description": "Whether DTMF functionality is enabled",
            "group": "dtmf"
        },
        "dtmf_timeout": {
            "value": "10",
            "value_type": "int",
            "description": "DTMF input timeout in seconds",
            "group": "dtmf"
        },
        "max_dtmf_attempts": {
            "value": "3",
            "value_type": "int",
            "description": "Maximum DTMF input attempts",
            "group": "dtmf"
        },
        "dtmf_inter_digit_timeout": {
            "value": "3",
            "value_type": "int",
            "description": "Timeout between DTMF digits",
            "group": "dtmf"
        }
    },
    
    "tts": {
        "enable_tts": {
            "value": "true",
            "value_type": "boolean",
            "description": "Whether TTS functionality is enabled",
            "group": "tts"
        },
        "default_tts_voice": {
            "value": "sv-SE-SofiaNeural",
            "description": "Default TTS voice for Swedish",
            "group": "tts"
        },
        "tts_speed": {
            "value": "1.0",
            "value_type": "float",
            "description": "TTS speech speed multiplier",
            "group": "tts"
        },
        "tts_cache_enabled": {
            "value": "true",
            "value_type": "boolean",
            "description": "Whether to cache TTS audio files",
            "group": "tts"
        },
        "tts_cache_duration_hours": {
            "value": "24",
            "value_type": "int",
            "description": "How long to cache TTS files in hours",
            "group": "tts"
        }
    },
    
    "security": {
        "api_key_required": {
            "value": "true",
            "value_type": "boolean",
            "description": "Whether API key is required for requests",
            "group": "security"
        },
        "rate_limit_enabled": {
            "value": "true",
            "value_type": "boolean",
            "description": "Whether rate limiting is enabled",
            "group": "security"
        },
        "max_requests_per_minute": {
            "value": "1000",
            "value_type": "int",
            "description": "Maximum requests per minute per IP",
            "group": "security"
        },
        "enable_cors": {
            "value": "true",
            "value_type": "boolean",
            "description": "Whether CORS is enabled",
            "group": "security"
        },
        "session_timeout_minutes": {
            "value": "60",
            "value_type": "int",
            "description": "Session timeout in minutes",
            "group": "security"
        }
    },
    
    "monitoring": {
        "enable_metrics": {
            "value": "true",
            "value_type": "boolean",
            "description": "Whether to collect metrics",
            "group": "monitoring"
        },
        "log_level": {
            "value": "INFO",
            "description": "Logging level (DEBUG, INFO, WARNING, ERROR)",
            "group": "monitoring"
        },
        "enable_health_checks": {
            "value": "true",
            "value_type": "boolean",
            "description": "Whether health checks are enabled",
            "group": "monitoring"
        },
        "metrics_retention_days": {
            "value": "30",
            "value_type": "int",
            "description": "How long to retain metrics data",
            "group": "monitoring"
        }
    },
    
    "integrations": {
        "rabbitmq_enabled": {
            "value": "true",
            "value_type": "boolean",
            "description": "Whether RabbitMQ integration is enabled",
            "group": "integrations"
        },
        "openai_enabled": {
            "value": "false",
            "value_type": "boolean",
            "description": "Whether OpenAI integration is enabled",
            "group": "integrations"
        },
        "webhook_enabled": {
            "value": "false",
            "value_type": "boolean",
            "description": "Whether webhook notifications are enabled",
            "group": "integrations"
        }
    }
}


def get_default_settings_by_group(group_name: str = None) -> Dict[str, Any]:
    """Get default settings for a specific group or all groups."""
    if group_name:
        return DEFAULT_SYSTEM_SETTINGS.get(group_name, {})
    return DEFAULT_SYSTEM_SETTINGS


def get_default_setting_value(group: str, key: str, default: Any = None) -> Any:
    """Get a specific default setting value."""
    group_settings = DEFAULT_SYSTEM_SETTINGS.get(group, {})
    setting = group_settings.get(key, {})
    return setting.get("value", default)
