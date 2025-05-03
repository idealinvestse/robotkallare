"""
GDial application package.
"""
from .config import get_settings
settings = get_settings()

# Apply fixes for known issues
from app.repositories.sms_repository_fix import fix_message_by_id_method
try:
    fix_message_by_id_method()
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Failed to apply SmsRepository fix: {e}")