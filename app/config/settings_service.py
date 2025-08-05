"""Settings service for managing application configuration."""
import logging
from typing import Dict, Any, Optional, List
from sqlmodel import Session, select
import json
from datetime import datetime

from app.config.settings_models import (
    SystemSetting, DtmfSetting, SmsSettings, 
    NotificationSettings, SecuritySettings
)
from app.config.settings_defaults import DEFAULT_SYSTEM_SETTINGS

logger = logging.getLogger(__name__)


class SettingsService:
    """Service for managing application settings."""
    
    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session
    
    def get_system_setting(self, key: str, default_value: Any = None) -> Any:
        """
        Get a system setting value by key.
        
        Args:
            key: Setting key
            default_value: Default value if setting doesn't exist
            
        Returns:
            The setting value or default value
        """
        return SystemSetting.get_value(self.session, key, default_value)
    
    def set_system_setting(
        self, 
        key: str, 
        value: Any, 
        description: Optional[str] = None,
        group: Optional[str] = None,
        value_type: Optional[str] = None
    ) -> SystemSetting:
        """
        Set a system setting value.
        
        Args:
            key: Setting key
            value: Setting value
            description: Optional description
            group: Optional group name
            value_type: Optional value type
            
        Returns:
            Updated SystemSetting object
        """
        return SystemSetting.set_value(
            self.session, key, value, description, group, value_type
        )
    
    def get_settings_by_group(self, group_name: Optional[str] = None) -> Dict[str, List[SystemSetting]]:
        """
        Get settings organized by group.
        
        Args:
            group_name: Optional specific group name
            
        Returns:
            Dictionary of settings organized by group
        """
        if group_name:
            settings = self.session.query(SystemSetting).filter(
                SystemSetting.group == group_name
            ).all()
            return {group_name: settings}
        
        # Get all settings and organize by group
        settings = self.session.query(SystemSetting).all()
        settings_by_group = {}
        
        for setting in settings:
            if setting.group not in settings_by_group:
                settings_by_group[setting.group] = []
            settings_by_group[setting.group].append(setting)
        
        return settings_by_group
    
    def get_dtmf_settings(self) -> Optional[DtmfSetting]:
        """Get DTMF settings from database."""
        # Return list of DtmfSetting rows for compatibility with older tests
        try:
            setting = self.session.exec(
                select(SystemSetting).where(SystemSetting.key == key)
            ).first()
            return setting.value if setting else None
        except Exception as e:
            logger.error(f"Error getting system setting {key}: {str(e)}")
            return None
    
    def set_system_setting(self, key: str, value: str) -> bool:
        """Set a system setting value by key."""
        try:
            setting = self.session.exec(
                select(SystemSetting).where(SystemSetting.key == key)
            ).first()
            
            if setting:
                setting.value = str(value)
                setting.updated_at = datetime.utcnow()
            else:
                setting = SystemSetting(
                    key=key,
                    value=str(value),
                    description="",
                    group=""
                )
                self.session.add(setting)
            
            self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Error setting system setting {key}: {str(e)}")
            self.session.rollback()
            return False
    
    def get_all_system_settings(self) -> Dict[str, str]:
        """Get all system settings as a dictionary."""
        try:
            settings = self.session.exec(select(SystemSetting)).all()
            return {setting.key: setting.value for setting in settings}
        except Exception as e:
            logger.error(f"Error getting all system settings: {str(e)}")
            return {}
    
    def get_sms_settings(self) -> Optional[SmsSettings]:
        """Get SMS settings."""
        try:
            return self.session.exec(select(SmsSettings)).first()
        except Exception as e:
            logger.error(f"Error getting SMS settings: {str(e)}")
            return None
    
    def update_sms_settings(
        self, 
        sms_settings: Optional[SmsSettings] = None,
        **kwargs: Any
    ) -> Optional[SmsSettings]:
        """
        Update SMS settings with either an SmsSettings object or keyword arguments.
        
        Args:
            sms_settings: Optional SmsSettings object with updated values
            **kwargs: SMS setting fields to update
            
        Returns:
            Updated SmsSettings object or None
        """
        try:
            # Determine source of update values
            if sms_settings is not None:
                update_data = sms_settings.dict(exclude_none=True)
            else:
                update_data = kwargs

            sms_settings_db = self.get_sms_settings()
            if not sms_settings_db:
                sms_settings_db = SmsSettings()
                self.session.add(sms_settings_db)

            for key, value in update_data.items():
                if hasattr(sms_settings_db, key):
                    setattr(sms_settings_db, key, value)

            # Persist each field individually as separate system setting keys for legacy compatibility
            for field, value in update_data.items():
                self.set_system_setting(f"sms.{field}", value)

            self.session.commit()
            return sms_settings_db
        except Exception as e:
            logger.error(f"Error updating SMS settings: {str(e)}", exc_info=True)
            self.session.rollback()
            return None

    def get_dtmf_settings(self) -> Optional[DtmfSetting]:
        """Get DTMF settings."""
        try:
            return self.session.exec(select(DtmfSetting)).first()
        except Exception as e:
            logger.error(f"Error getting DTMF settings: {str(e)}")
            return None
    
    def update_dtmf_settings(
        self, 
        digit: Optional[str] = None,
        action: Optional[str] = None,
        value: Optional[str] = None
    ) -> Optional[DtmfSetting]:
        """
        Update DTMF settings with legacy compatibility fields.

        # Retain original detailed validation returning list of issues
        """
        issues = []
        # Validate required Twilio settings
        twilio_sid = self.get_system_setting("calls.twilio_account_sid")
        twilio_token = self.get_system_setting("calls.twilio_auth_token")
        twilio_from = self.get_system_setting("calls.twilio_from_number")
        
        if not twilio_sid:
            issues.append("Twilio Account SID is not configured")
        if not twilio_token:
            issues.append("Twilio Auth Token is not configured")
        if not twilio_from:
            issues.append("Twilio From Number is not configured")
        
        # Validate numeric settings
        numeric_settings = [
            ("calls.call_timeout_sec", "Call timeout"),
            ("calls.max_concurrent_calls", "Max concurrent calls"),
            ("sms.max_sms_length", "Max SMS length"),
            ("security.max_requests_per_minute", "Rate limit")
        ]
        
        for key, name in numeric_settings:
            value = self.get_system_setting(key)
            if value is not None:
                try:
                    int(value)
                except (ValueError, TypeError):
                    issues.append(f"{name} must be a valid number")
            
            for key, name in numeric_settings:
                value = self.get_system_setting(key)
                if value is not None:
                    try:
                        int(value)
                    except (ValueError, TypeError):
                        issues.append(f"{name} must be a valid number")
