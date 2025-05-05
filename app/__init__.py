"""
GDial application package.
"""
from .config import get_settings
settings = get_settings()

# Configure FFmpeg for audio processing
try:
    from app.utils import ffmpeg_helper
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Failed to configure FFmpeg: {e}")

# Apply fixes for known issues
from app.repositories.sms_repository_fix import fix_message_by_id_method
try:
    # fix_message_by_id_method() # Moved to lifespan in app/api.py
    pass # Keep the try-except structure for now, in case other fixes are added
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Failed to apply SmsRepository fix: {e}")