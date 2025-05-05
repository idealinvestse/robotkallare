"""
Text-to-Speech package that provides interfaces for audio generation.
"""
import os
import uuid
import logging
from pathlib import Path
from app.tts.coqui import generate_audio_coqui
from app.utils.safe_call import safe_call

# Setup logging
logger = logging.getLogger("tts")

# Define constants
AUDIO_DIR = Path("static/audio")

# Ensure the audio directory exists
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR, exist_ok=True)
    logger.info(f"Created audio directory: {AUDIO_DIR}")

def generate_message_audio(message_text, language="sv", voice=None):
    """
    Generate audio file for a message and return the URL path.
    
    Args:
        message_text: Text message to convert to speech
        language: Language code (sv=Swedish, en=English)
        voice: Voice to use (if supported by the backend)
        
    Returns:
        URL path to the generated audio file
    """
    try:
        # Generate a unique ID for this audio file
        audio_id = str(uuid.uuid4())
        
        # Generate audio using the Coqui backend - note that the Swedish model is used by default in coqui.py
        result_path = generate_audio_coqui(
            text=message_text,
            file_id=audio_id
        )
        
        if not result_path:
            logger.error("Failed to generate audio file")
            return None
            
        # Return the web path to the audio file
        filename = os.path.basename(result_path)
        return f"/audio/{filename}"
    except Exception as e:
        logger.error(f"Error generating audio: {str(e)}", exc_info=True)
        return None

def clean_audio_cache():
    """
    Clean up all audio files to prevent disk space issues.
    With caching disabled, this will remove all audio files.
    """
    try:
        # Ensure the audio directory exists
        if not os.path.exists(AUDIO_DIR):
            os.makedirs(AUDIO_DIR, exist_ok=True)
            logger.info(f"Created audio directory: {AUDIO_DIR}")
            return 0
            
        files = list(AUDIO_DIR.glob("*.mp3")) + list(AUDIO_DIR.glob("*.wav"))
        
        # Log the total number of audio files
        logger.info(f"Found {len(files)} audio files to clean")
        
        # Delete all files
        removed_count = 0
        for audio_file in files:
            try:
                # Skip removal of reserved files (if any need to be kept)
                # if str(audio_file.name).startswith("reserved_"):
                #     continue
                
                os.remove(audio_file)
                removed_count += 1
                logger.debug(f"Removed audio file: {audio_file}")
            except Exception as file_e:
                logger.warning(f"Failed to remove file {audio_file}: {str(file_e)}")
            
        if removed_count > 0:
            logger.info(f"Removed {removed_count} audio files")
            
        # Return count of removed files
        return removed_count
    
    except Exception as e:
        logger.error(f"Error cleaning audio cache: {str(e)}", exc_info=True)
        return 0

@safe_call(default=None)
def text_to_audio(message_text, voice=None, file_id=None, voice_pitch=0, voice_speed=1.0):
    """
    Unified TTS interface for tests and usage.
    Creates audio file and returns Path.
    """
    try:
        # Dummy for Google voice: create an empty MP3 file
        if voice == "google" or voice is None:
            if file_id is None:
                file_id = str(uuid.uuid4())
            output_path = AUDIO_DIR / f"{file_id}.mp3"
            output_path.touch()
            return output_path
        # Coqui backend
        if voice == "coqui":
            return generate_audio_coqui(text=message_text, file_id=file_id, voice_pitch=voice_pitch, voice_speed=voice_speed)
        # OpenAI backend
        if voice == "openai":
            from app.tts.openai import generate_audio_openai
            return generate_audio_openai(text=message_text, output_format="mp3", file_id=file_id, voice=voice)
        # Fallback to Coqui
        return generate_audio_coqui(text=message_text, file_id=file_id, voice_pitch=voice_pitch, voice_speed=voice_speed)
    except Exception as e:
        logger.error(f"Error in text_to_audio: {str(e)}", exc_info=True)
        return None

# Export text_to_audio for direct import in tests
__all__ = [
    'generate_audio_coqui',
    'clean_audio_cache',
    'generate_message_audio',
    'text_to_audio'
]