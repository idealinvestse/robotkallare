"""Pydantic schemas for settings-related API operations.

This module contains the schemas for the settings API endpoints.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, UUID4, Field

class SystemSettingResponse(BaseModel):
    """Response schema for system settings."""
    key: str
    value: str
    value_type: str
    description: str
    group: str
    created_at: datetime
    updated_at: datetime
    
class SystemSettingCreate(BaseModel):
    """Schema for creating a new system setting."""
    key: str
    value: str
    value_type: Optional[str] = "string"
    description: str
    group: Optional[str] = "general"
    
class SystemSettingUpdate(BaseModel):
    """Schema for updating a system setting."""
    value: Optional[str] = None
    value_type: Optional[str] = None
    description: Optional[str] = None
    group: Optional[str] = None
    
class SystemSettingBulkUpdate(BaseModel):
    """Schema for bulk updating system settings."""
    settings: Dict[str, str]

class DtmfSettingResponse(BaseModel):
    """Response schema for DTMF settings."""
    id: UUID4
    max_attempts: int
    input_timeout: int
    confirm_response: bool
    retry_on_invalid: bool
    additional_digits: Optional[str] = None
    universal_gather: bool
    repeat_message_digit: str
    confirm_receipt_digit: str
    request_callback_digit: str
    transfer_to_live_agent_digit: str
    dtmf_menu_style: str
    inter_digit_timeout: int
    allow_message_skip: bool
    extra_settings: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
class DtmfSettingUpdate(BaseModel):
    """Schema for updating DTMF settings."""
    max_attempts: Optional[int] = None
    input_timeout: Optional[int] = None
    confirm_response: Optional[bool] = None
    retry_on_invalid: Optional[bool] = None
    additional_digits: Optional[str] = None
    universal_gather: Optional[bool] = None
    repeat_message_digit: Optional[str] = None
    confirm_receipt_digit: Optional[str] = None
    request_callback_digit: Optional[str] = None
    transfer_to_live_agent_digit: Optional[str] = None
    dtmf_menu_style: Optional[str] = None
    inter_digit_timeout: Optional[int] = None
    allow_message_skip: Optional[bool] = None
    extra_settings: Optional[Dict[str, Any]] = None

class SmsSettingsResponse(BaseModel):
    """Response schema for SMS settings."""
    id: UUID4
    include_sender_name: bool
    message_prefix: str
    message_suffix: str
    max_length: int
    split_long_messages: bool
    batch_delay_ms: int
    batch_size: int
    status_callback_url: Optional[str] = None
    sms_rate_limit_per_second: int
    allow_opt_out: bool
    opt_out_keyword: str
    delivery_report_timeout: int
    fail_silently: bool
    sms_retry_strategy: str
    sms_url_shortener: bool
    international_sms_enabled: bool
    extra_settings: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
class SmsSettingsUpdate(BaseModel):
    """Schema for updating SMS settings."""
    include_sender_name: Optional[bool] = None
    message_prefix: Optional[str] = None
    message_suffix: Optional[str] = None
    max_length: Optional[int] = None
    split_long_messages: Optional[bool] = None
    batch_delay_ms: Optional[int] = None
    batch_size: Optional[int] = None
    status_callback_url: Optional[str] = None
    sms_rate_limit_per_second: Optional[int] = None
    allow_opt_out: Optional[bool] = None
    opt_out_keyword: Optional[str] = None
    delivery_report_timeout: Optional[int] = None
    fail_silently: Optional[bool] = None
    sms_retry_strategy: Optional[str] = None
    sms_url_shortener: Optional[bool] = None
    international_sms_enabled: Optional[bool] = None
    extra_settings: Optional[Dict[str, Any]] = None

class NotificationSettingsResponse(BaseModel):
    """Response schema for notification settings."""
    id: UUID4
    admin_email: Optional[str] = None
    notify_on_emergency: bool
    notify_on_error: bool
    failure_threshold_pct: int
    daily_reports: bool
    weekly_reports: bool
    alert_sound_enabled: bool
    admin_phone_numbers: Optional[Dict[str, Any]] = None
    webhook_url: Optional[str] = None
    usage_report_frequency: str
    emergency_escalation_threshold: int
    extra_settings: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
class NotificationSettingsUpdate(BaseModel):
    """Schema for updating notification settings."""
    admin_email: Optional[str] = None
    notify_on_emergency: Optional[bool] = None
    notify_on_error: Optional[bool] = None
    failure_threshold_pct: Optional[int] = None
    daily_reports: Optional[bool] = None
    weekly_reports: Optional[bool] = None
    alert_sound_enabled: Optional[bool] = None
    admin_phone_numbers: Optional[Dict[str, Any]] = None
    webhook_url: Optional[str] = None
    usage_report_frequency: Optional[str] = None
    emergency_escalation_threshold: Optional[int] = None
    extra_settings: Optional[Dict[str, Any]] = None

class SecuritySettingsResponse(BaseModel):
    """Response schema for security settings."""
    id: UUID4
    force_https: bool
    sensitive_data_masking: bool
    auto_logout_inactive_min: int
    max_login_attempts: int
    password_expiry_days: int
    api_rate_limit: int
    audit_log_retention_days: int
    ip_whitelist: Optional[Dict[str, Any]] = None
    allowed_origins: Optional[Dict[str, Any]] = None
    extra_settings: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
class SecuritySettingsUpdate(BaseModel):
    """Schema for updating security settings."""
    force_https: Optional[bool] = None
    sensitive_data_masking: Optional[bool] = None
    auto_logout_inactive_min: Optional[int] = None
    max_login_attempts: Optional[int] = None
    password_expiry_days: Optional[int] = None
    api_rate_limit: Optional[int] = None
    audit_log_retention_days: Optional[int] = None
    ip_whitelist: Optional[Dict[str, Any]] = None
    allowed_origins: Optional[Dict[str, Any]] = None
    extra_settings: Optional[Dict[str, Any]] = None

class SettingsGroup(BaseModel):
    """Schema for a group of settings."""
    group_name: str
    settings: List[SystemSettingResponse]