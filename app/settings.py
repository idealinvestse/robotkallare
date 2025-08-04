"""Refactored settings module with clean separation of concerns.

This module provides backward compatibility while using the new modular settings architecture.
"""
import logging
from typing import Dict, Any, Optional, List
from sqlmodel import Session

# Import new modular components
from app.config.settings_models import (
    SystemSetting, DtmfSetting, SmsSettings, 
    NotificationSettings, SecuritySettings
)
from app.config.settings_service import SettingsService
from app.config.settings_defaults import DEFAULT_SYSTEM_SETTINGS
from app.config import get_settings as get_app_settings

logger = logging.getLogger(__name__)

# Deprecation warning
logger.warning(
    "settings.py is deprecated. Use app.config.settings_service.SettingsService instead. "
    "This module will be removed in a future version."
)


# Legacy function wrappers for backward compatibility
def get_system_setting(session: Session, key: str, default_value: Any = None) -> Any:
    """
    DEPRECATED: Get a system setting value by key.
    
    Use app.config.settings_service.SettingsService.get_system_setting instead.
    """
    logger.warning("get_system_setting function is deprecated. Use SettingsService.get_system_setting instead.")
    
    settings_service = SettingsService(session)
    return settings_service.get_system_setting(key, default_value)


def initialize_settings() -> bool:
    """
    DEPRECATED: Initialize database settings.
    
    Use app.config.settings_service.SettingsService.initialize_default_settings instead.
    """
    logger.warning("initialize_settings function is deprecated. Use SettingsService.initialize_default_settings instead.")
    
    try:
        from app.database import get_session
        
        with next(get_session()) as session:
            settings_service = SettingsService(session)
            return settings_service.initialize_default_settings()
            
    except Exception as e:
        logger.error(f"Failed to initialize settings: {str(e)}", exc_info=True)
        return False


def get_dtmf_settings(session: Session) -> Optional[DtmfSetting]:
    """
    DEPRECATED: Get DTMF settings from database.
    
    Use app.config.settings_service.SettingsService.get_dtmf_settings instead.
    """
    logger.warning("get_dtmf_settings function is deprecated. Use SettingsService.get_dtmf_settings instead.")
    
    settings_service = SettingsService(session)
    return settings_service.get_dtmf_settings()


def get_sms_settings(session: Session) -> Optional[SmsSettings]:
    """
    DEPRECATED: Get SMS settings from database.
    
    Use app.config.settings_service.SettingsService.get_sms_settings instead.
    """
    logger.warning("get_sms_settings function is deprecated. Use SettingsService.get_sms_settings instead.")
    
    settings_service = SettingsService(session)
    return settings_service.get_sms_settings()


def get_notification_settings(session: Session) -> Optional[NotificationSettings]:
    """
    DEPRECATED: Get notification settings from database.
    
    Use app.config.settings_service.SettingsService.get_notification_settings instead.
    """
    logger.warning("get_notification_settings function is deprecated. Use SettingsService.get_notification_settings instead.")
    
    settings_service = SettingsService(session)
    return settings_service.get_notification_settings()


def get_security_settings(session: Session) -> SecuritySettings:
    """
    DEPRECATED: Get security settings from database.
    
    Use app.config.settings_service.SettingsService.get_security_settings instead.
    """
    logger.warning("get_security_settings function is deprecated. Use SettingsService.get_security_settings instead.")
    
    settings_service = SettingsService(session)
    return settings_service.get_security_settings()


def get_settings_by_group(session: Session, group_name: Optional[str] = None) -> Dict[str, List[SystemSetting]]:
    """
    DEPRECATED: Get settings organized by group.
    
    Use app.config.settings_service.SettingsService.get_settings_by_group instead.
    """
    logger.warning("get_settings_by_group function is deprecated. Use SettingsService.get_settings_by_group instead.")
    
    settings_service = SettingsService(session)
    return settings_service.get_settings_by_group(group_name)


# Re-export the Settings class for backward compatibility
from app.config import Settings as AppSettings

# Re-export the settings instance for backward compatibility
settings = get_app_settings()

# Re-export models for backward compatibility (with deprecation warnings)
class LegacySystemSetting(SystemSetting):
    """DEPRECATED: Use app.config.settings_models.SystemSetting instead."""
    
    def __init__(self, *args, **kwargs):
        logger.warning("LegacySystemSetting is deprecated. Use app.config.settings_models.SystemSetting instead.")
        super().__init__(*args, **kwargs)


class LegacyDtmfSetting(DtmfSetting):
    """DEPRECATED: Use app.config.settings_models.DtmfSetting instead."""
    
    def __init__(self, *args, **kwargs):
        logger.warning("LegacyDtmfSetting is deprecated. Use app.config.settings_models.DtmfSetting instead.")
        super().__init__(*args, **kwargs)


class LegacySmsSettings(SmsSettings):
    """DEPRECATED: Use app.config.settings_models.SmsSettings instead."""
    
    def __init__(self, *args, **kwargs):
        logger.warning("LegacySmsSettings is deprecated. Use app.config.settings_models.SmsSettings instead.")
        super().__init__(*args, **kwargs)


class LegacyNotificationSettings(NotificationSettings):
    """DEPRECATED: Use app.config.settings_models.NotificationSettings instead."""
    
    def __init__(self, *args, **kwargs):
        logger.warning("LegacyNotificationSettings is deprecated. Use app.config.settings_models.NotificationSettings instead.")
        super().__init__(*args, **kwargs)


class LegacySecuritySettings(SecuritySettings):
    """DEPRECATED: Use app.config.settings_models.SecuritySettings instead."""
    
    def __init__(self, *args, **kwargs):
        logger.warning("LegacySecuritySettings is deprecated. Use app.config.settings_models.SecuritySettings instead.")
        super().__init__(*args, **kwargs)


# Backward compatibility aliases
SystemSetting = LegacySystemSetting
DtmfSetting = LegacyDtmfSetting
SmsSettings = LegacySmsSettings
NotificationSettings = LegacyNotificationSettings
SecuritySettings = LegacySecuritySettings

logger.info("Legacy settings module loaded with deprecation warnings")
