"""Settings service for managing application configuration."""
import logging
from typing import Dict, Any, Optional, List
from sqlmodel import Session

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
        return self.session.query(DtmfSetting).first()
    
    def get_sms_settings(self) -> Optional[SmsSettings]:
        """Get SMS settings from database."""
        return self.session.query(SmsSettings).first()
    
    def get_notification_settings(self) -> Optional[NotificationSettings]:
        """Get notification settings from database."""
        return self.session.query(NotificationSettings).first()
    
    def get_security_settings(self) -> SecuritySettings:
        """Get security settings from database."""
        return self.session.query(SecuritySettings).first() or SecuritySettings()
    
    def initialize_default_settings(self) -> bool:
        """
        Initialize database with default settings if they don't exist.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if settings already exist
            existing_count = self.session.query(SystemSetting).count()
            
            if existing_count == 0:
                logger.info("Initializing default system settings...")
                
                # Initialize system settings from defaults
                for group_name, group_settings in DEFAULT_SYSTEM_SETTINGS.items():
                    for key, setting_data in group_settings.items():
                        full_key = f"{group_name}.{key}"
                        
                        SystemSetting.set_value(
                            self.session,
                            key=full_key,
                            value=setting_data["value"],
                            description=setting_data["description"],
                            group=setting_data["group"],
                            value_type=setting_data.get("value_type", "string")
                        )
                
                # Create default specialized settings
                self._create_default_specialized_settings()
                
                logger.info("Default settings initialized successfully")
                return True
            else:
                logger.info("Database already contains settings, skipping initialization.")
                return True
                
        except Exception as e:
            logger.error(f"Failed to initialize settings: {str(e)}", exc_info=True)
            return False
    
    def _create_default_specialized_settings(self) -> None:
        """Create default specialized settings (DTMF, SMS, etc.)."""
        try:
            # Create DTMF settings if they don't exist
            if not self.session.query(DtmfSetting).first():
                dtmf_settings = DtmfSetting()
                self.session.add(dtmf_settings)
            
            # Create SMS settings if they don't exist
            if not self.session.query(SmsSettings).first():
                sms_settings = SmsSettings()
                self.session.add(sms_settings)
            
            # Create notification settings if they don't exist
            if not self.session.query(NotificationSettings).first():
                notification_settings = NotificationSettings()
                self.session.add(notification_settings)
            
            # Create security settings if they don't exist
            if not self.session.query(SecuritySettings).first():
                security_settings = SecuritySettings()
                self.session.add(security_settings)
            
            self.session.commit()
            logger.info("Default specialized settings created")
            
        except Exception as e:
            logger.error(f"Error creating default specialized settings: {str(e)}", exc_info=True)
            self.session.rollback()
    
    def update_dtmf_settings(self, **kwargs) -> Optional[DtmfSetting]:
        """
        Update DTMF settings.
        
        Args:
            **kwargs: DTMF setting fields to update
            
        Returns:
            Updated DtmfSetting object or None
        """
        try:
            dtmf_settings = self.get_dtmf_settings()
            if not dtmf_settings:
                dtmf_settings = DtmfSetting()
                self.session.add(dtmf_settings)
            
            for key, value in kwargs.items():
                if hasattr(dtmf_settings, key):
                    setattr(dtmf_settings, key, value)
            
            dtmf_settings.updated_at = datetime.now()
            self.session.commit()
            return dtmf_settings
            
        except Exception as e:
            logger.error(f"Error updating DTMF settings: {str(e)}", exc_info=True)
            self.session.rollback()
            return None
    
    def update_sms_settings(self, **kwargs) -> Optional[SmsSettings]:
        """
        Update SMS settings.
        
        Args:
            **kwargs: SMS setting fields to update
            
        Returns:
            Updated SmsSettings object or None
        """
        try:
            sms_settings = self.get_sms_settings()
            if not sms_settings:
                sms_settings = SmsSettings()
                self.session.add(sms_settings)
            
            for key, value in kwargs.items():
                if hasattr(sms_settings, key):
                    setattr(sms_settings, key, value)
            
            sms_settings.updated_at = datetime.now()
            self.session.commit()
            return sms_settings
            
        except Exception as e:
            logger.error(f"Error updating SMS settings: {str(e)}", exc_info=True)
            self.session.rollback()
            return None
    
    def export_settings(self) -> Dict[str, Any]:
        """
        Export all settings to a dictionary for backup/migration.
        
        Returns:
            Dictionary containing all settings
        """
        try:
            export_data = {
                "system_settings": [],
                "dtmf_settings": None,
                "sms_settings": None,
                "notification_settings": None,
                "security_settings": None
            }
            
            # Export system settings
            system_settings = self.session.query(SystemSetting).all()
            for setting in system_settings:
                export_data["system_settings"].append({
                    "key": setting.key,
                    "value": setting.value,
                    "value_type": setting.value_type,
                    "description": setting.description,
                    "group": setting.group
                })
            
            # Export specialized settings
            dtmf = self.get_dtmf_settings()
            if dtmf:
                export_data["dtmf_settings"] = dtmf.dict()
            
            sms = self.get_sms_settings()
            if sms:
                export_data["sms_settings"] = sms.dict()
            
            notification = self.get_notification_settings()
            if notification:
                export_data["notification_settings"] = notification.dict()
            
            security = self.get_security_settings()
            if security:
                export_data["security_settings"] = security.dict()
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting settings: {str(e)}", exc_info=True)
            return {}
    
    def validate_settings(self) -> List[str]:
        """
        Validate current settings and return list of issues.
        
        Returns:
            List of validation error messages
        """
        issues = []
        
        try:
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
            
            return issues
            
        except Exception as e:
            logger.error(f"Error validating settings: {str(e)}", exc_info=True)
            return [f"Settings validation error: {str(e)}"]
