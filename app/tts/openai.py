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

logger = logging.getLogger("openai_tts")

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "tts-1")
AUDIO_DIR = Path("static/audio")

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

    openai.api_key = OPENAI_API_KEY
    try:
        response = openai.audio.speech.create(
            model=OPENAI_TTS_MODEL,
            voice=voice,
            input=text
        )
        audio_bytes = response.audio
        # Save WAV
        wav_path = AUDIO_DIR / f"{file_id}.wav"
        with open(wav_path, "wb") as f:
            f.write(audio_bytes)
        if output_format.lower() == "wav":
            return wav_path
        # Convert to MP3
        mp3_path = AUDIO_DIR / f"{file_id}.mp3"
        audio_seg = AudioSegment.from_wav(wav_path)
        audio_seg.export(mp3_path, format="mp3")
        os.remove(wav_path)
        return mp3_path
    except Exception as e:
        logger.error(f"Error generating speech with OpenAI: {e}", exc_info=True)
        return None
