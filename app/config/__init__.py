"""Configuration module exports."""

# Import from the main config.py file
try:
    from ..config import get_settings, Settings
except ImportError:
    # Fallback for when config.py is not available
    from .settings_service import SettingsService
    from .settings_models import SystemSetting
    from .settings_defaults import DEFAULT_SYSTEM_SETTINGS
    
    # Create a minimal Settings class if needed
    class Settings:
        def __init__(self):
            self.LOG_LEVEL = "INFO"
            self.TWILIO_ACCOUNT_SID = None
            self.TWILIO_AUTH_TOKEN = None
            self.TWILIO_FROM_NUMBER = None
    
    def get_settings():
        return Settings()

__all__ = ["get_settings", "Settings"]