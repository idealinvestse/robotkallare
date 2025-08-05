"""Settings models for database-stored configuration."""
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from sqlmodel import Field, SQLModel
from sqlalchemy import JSON, Column

logger = logging.getLogger(__name__)


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
        """Get a setting value with type conversion."""
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
            return json.loads(setting.value)
        else:
            return setting.value
    
    @classmethod 
    def set_value(cls, session, key: str, value: Any, 
                 description: Optional[str] = None, 
                 group: Optional[str] = None,
                 value_type: Optional[str] = None):
        """Set a setting value with automatic type detection."""
        setting = session.query(cls).filter(cls.key == key).first()
        if not setting:
            setting = cls(key=key)
        
        setting.value = str(value)
        
        # Auto-detect value type if not provided
        if value_type:
            setting.value_type = value_type
        elif not hasattr(setting, 'value_type') or not setting.value_type:
            if isinstance(value, bool):
                setting.value_type = "boolean"
            elif isinstance(value, int):
                setting.value_type = "int"
            elif isinstance(value, float):
                setting.value_type = "float"
            elif isinstance(value, (dict, list)):
                setting.value_type = "json"
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
    # Legacy per-digit routing fields expected by older tests
    digit: Optional[str] = None
    action: Optional[str] = None
    value: Optional[str] = None
    
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
    extra_settings: Optional[str] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class SmsSettings(SQLModel, table=True):
    """SMS configuration settings.
    Controls how SMS messages are formatted and sent.
    """
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    include_sender_name: bool = True
    max_message_length: int = 160
    enable_unicode: bool = True
    auto_split_long_messages: bool = True
    include_unsubscribe_link: bool = False
    delivery_receipt_enabled: bool = True
    retry_failed_messages: bool = True
    max_retry_attempts: int = 3
    retry_delay_minutes: int = 5
    rate_limit_per_minute: int = 100
    enable_scheduling: bool = True
    timezone: str = "Europe/Stockholm"
    business_hours_only: bool = False
    business_hours_start: str = "08:00"
    business_hours_end: str = "18:00"
    international_sms_enabled: bool = False
    extra_settings: Optional[str] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # ---------------- Legacy alias properties ----------------
    @property
    def enabled(self) -> bool:  # type: ignore
        """Legacy alias for include_sender_name."""
        return self.include_sender_name

    @enabled.setter
    def enabled(self, value: bool):  # type: ignore
        self.include_sender_name = value

    @property
    def rate_limit(self) -> int:  # type: ignore
        return self.rate_limit_per_minute

    @rate_limit.setter
    def rate_limit(self, value: int):  # type: ignore
        self.rate_limit_per_minute = value

    @property
    def retry_attempts(self) -> int:  # type: ignore
        return self.max_retry_attempts

    @retry_attempts.setter
    def retry_attempts(self, value: int):  # type: ignore
        self.max_retry_attempts = value

    class Config:
        extra = "allow"


class NotificationSettings(SQLModel, table=True):
    """Settings for internal system notifications.
    Controls how and when notifications are sent to admins about system events.
    """
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    email_notifications_enabled: bool = True
    sms_notifications_enabled: bool = False
    webhook_notifications_enabled: bool = False
    notification_email: Optional[str] = None
    notification_phone: Optional[str] = None
    webhook_url: Optional[str] = None
    notify_on_system_errors: bool = True
    notify_on_failed_calls: bool = True
    notify_on_failed_sms: bool = True
    notify_on_high_volume: bool = True
    high_volume_threshold: int = 100
    emergency_escalation_enabled: bool = True
    emergency_escalation_threshold: int = 15
    extra_settings: Optional[str] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class SecuritySettings(SQLModel, table=True):
    """Security-related settings for the application.
    Controls security features and behavior.
    """
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    force_https: bool = True
    session_timeout_minutes: int = 60
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    require_strong_passwords: bool = True
    enable_two_factor_auth: bool = False
    api_rate_limit_per_minute: int = 1000
    enable_request_logging: bool = True
    log_sensitive_data: bool = False
    extra_settings: Optional[str] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
