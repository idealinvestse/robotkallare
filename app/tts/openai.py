"""
OpenAI TTS module for GDial.
Uses OpenAI's audio generation API as an alternative TTS provider.
"""
import os
import logging
import uuid
from pathlib import Path

import openai
from pydub import AudioSegment
from openai import OpenAI

logger = logging.getLogger("openai_tts")

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "tts-1")
AUDIO_DIR = Path("static/audio")
OUTPUT_FORMATS = {"mp3", "wav", "flac", "aac", "opus", "pcm"}

# Ensure audio dir exists
os.makedirs(AUDIO_DIR, exist_ok=True)

def generate_audio_openai(text, output_format="mp3", file_id=None, voice=None):
    """
    Generate audio using OpenAI TTS.

    Parameters:
    - text: Text to synthesize.
    - output_format: "mp3" or "wav".
    - file_id: Optional identifier (UUID).
    - voice: Optional voice name for OpenAI.

    Returns:
    - Path to generated audio file or None on failure.
    """
    if not text:
        logger.error("Empty text provided to OpenAI TTS function")
        return None

    if file_id is None:
        file_id = str(uuid.uuid4())

    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not set")
        return None

    if output_format.lower() not in OUTPUT_FORMATS:
        logger.error(f"Unsupported output format: {output_format}")
        return None

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.audio.speech.create(
            model=OPENAI_TTS_MODEL,
            voice=voice or "alloy",
            input=text,
            response_format=output_format.lower()
        )
        audio_bytes = response.content if hasattr(response, "content") else getattr(response, "audio", None)
        if not audio_bytes:
            logger.error("No audio bytes returned from OpenAI")
            return None
        
        out_path = AUDIO_DIR / f"{file_id}.{output_format.lower()}"
        with open(out_path, "wb") as f:
            f.write(audio_bytes)
        return out_path
    except Exception as e:
        logger.error(f"Error generating speech with OpenAI: {e}", exc_info=True)
        return None
