"""Settings database models for GDial

This module defines the database models for system and user-configurable settings.
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlmodel import Field, SQLModel, Relationship, JSON, Column

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
        """Get setting value with appropriate type conversion"""
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
        """Set a setting value with automatic type detection"""
        # Get existing setting or create new one
        setting = session.query(cls).filter(cls.key == key).first()
        if not setting:
            setting = cls(key=key)
            
        # Set value and detect type if not specified
        setting.value = str(value)
        
        if value_type:
            setting.value_type = value_type
        elif not hasattr(setting, 'value_type') or not setting.value_type:
            # Auto-detect type
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
        
        # Update other fields if provided
        if description:
            setting.description = description
        if group:
            setting.group = group
            
        setting.updated_at = datetime.now()
        
        # Add and commit
        session.add(setting)
        session.commit()
        
        return setting

class DtmfSetting(SQLModel, table=True):
    """Extended settings for DTMF response behaviors.
    
    Controls how DTMF responses are handled in emergency calls.
    """
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    # Max attempts for DTMF input
    max_attempts: int = 3
    # Timeout for waiting for DTMF input (seconds)
    input_timeout: int = 10
    # Enable/disable response confirmation ("You pressed X. Is this correct?")
    confirm_response: bool = False
    # Enable/disable digit recapturing if invalid digit is pressed
    retry_on_invalid: bool = True
    # Additional digits to accept beyond basic 1,2,3
    additional_digits: Optional[str] = None
    # Whether to add gather functionality to all outgoing messages
    universal_gather: bool = True
    # Digit to press to repeat message
    repeat_message_digit: str = "0"
    # Digit to confirm receipt of message
    confirm_receipt_digit: str = "1"
    # Digit to request callback
    request_callback_digit: str = "8"
    # Digit to transfer to live agent
    transfer_to_live_agent_digit: str = "9"
    # Menu presentation style (standard, concise, detailed)
    dtmf_menu_style: str = "standard"
    # Timeout between digit presses (seconds)
    inter_digit_timeout: int = 3
    # Allow skipping message with # key
    allow_message_skip: bool = True
    # Additional settings as JSON
    extra_settings: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class SmsSettings(SQLModel, table=True):
    """SMS configuration settings.
    
    Controls how SMS messages are formatted and sent.
    """
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    # Whether to include sender name in SMS
    include_sender_name: bool = True
    # Default SMS prefix
    message_prefix: str = "EMERGENCY: "
    # Message suffix or signature
    message_suffix: str = ""
    # Maximum length for SMS messages (standard is 160 chars)
    max_length: int = 160
    # Whether to automatically split long messages
    split_long_messages: bool = True
    # Delay between sending batches of SMS (ms)
    batch_delay_ms: int = 1000
    # Batch size (messages per batch)
    batch_size: int = 50
    # Status callback URL (optional)
    status_callback_url: Optional[str] = None
    # Maximum SMS to send per second
    sms_rate_limit_per_second: int = 10
    # Allow recipients to opt out via reply
    allow_opt_out: bool = True
    # Keyword for opting out
    opt_out_keyword: str = "STOP"
    # Timeout for delivery reports (minutes)
    delivery_report_timeout: int = 60
    # Continue sending other messages if one fails
    fail_silently: bool = True
    # Retry strategy (linear, exponential, fixed)
    sms_retry_strategy: str = "exponential"
    # Automatically shorten URLs in SMS
    sms_url_shortener: bool = False
    # Allow international SMS
    international_sms_enabled: bool = False
    # Additional settings as JSON
    extra_settings: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
class NotificationSettings(SQLModel, table=True):
    """Settings for internal system notifications.
    
    Controls how and when notifications are sent to admins about system events.
    """
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    # Email for admin notifications
    admin_email: Optional[str] = None
    # Notify admin when emergency call is initiated
    notify_on_emergency: bool = True
    # Notify admin on system errors
    notify_on_error: bool = True
    # Notify when calls/SMS fail above this threshold (percentage)
    failure_threshold_pct: int = 10
    # Send daily status reports
    daily_reports: bool = False
    # Send weekly summary reports
    weekly_reports: bool = True
    # Play sound for new alerts
    alert_sound_enabled: bool = True
    # Admin phone numbers for alerts
    admin_phone_numbers: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    # URL for webhook notifications
    webhook_url: Optional[str] = None
    # How often to send usage reports (daily, weekly, monthly)
    usage_report_frequency: str = "weekly"
    # Minutes before escalating emergency alerts
    emergency_escalation_threshold: int = 15
    # Additional settings as JSON
    extra_settings: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class SecuritySettings(SQLModel, table=True):
    """Security-related settings for the application.
    
    Controls security features and behavior.
    """
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    # Force HTTPS for all connections
    force_https: bool = True
    # Mask sensitive data in logs
    sensitive_data_masking: bool = True
    # Auto-logout after inactivity (minutes)
    auto_logout_inactive_min: int = 30
    # Maximum failed login attempts before lockout
    max_login_attempts: int = 5
    # Days before password expires
    password_expiry_days: int = 90
    # API requests per minute
    api_rate_limit: int = 100
    # Days to retain audit logs
    audit_log_retention_days: int = 365
    # Allowed IP addresses for admin access
    ip_whitelist: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    # Allowed CORS origins
    allowed_origins: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    # Additional settings as JSON
    extra_settings: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)