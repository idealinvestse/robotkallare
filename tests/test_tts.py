import os
import uuid
import pytest
from app.tts import text_to_audio
from pathlib import Path

AUDIO_DIR = Path("static/audio")

def cleanup_audio_files():
    for ext in ("mp3", "wav"):
        for f in AUDIO_DIR.glob(f"test_*/*.{ext}"):
            try:
                os.remove(f)
            except Exception:
                pass

def test_google_tts_basic():
    file_id = f"test_google_{uuid.uuid4()}"
    audio_path = text_to_audio("Hej världen!", voice="google", file_id=file_id)
    assert audio_path is not None
    assert audio_path.exists()
    assert audio_path.suffix == ".mp3"
    os.remove(audio_path)

def test_coqui_tts_basic(monkeypatch):
    # Skip if piper binary/model not set
    from app.tts.coqui import PIPER_BINARY, PIPER_MODEL
    if not os.path.exists(PIPER_BINARY) or not os.path.exists(PIPER_MODEL):
        pytest.skip("Piper binary/model missing")
    file_id = f"test_coqui_{uuid.uuid4()}"
    audio_path = text_to_audio("Hej världen!", voice="coqui", file_id=file_id)
    assert audio_path is not None
    assert audio_path.exists()
    assert audio_path.suffix in (".mp3", ".wav")
    os.remove(audio_path)

def test_openai_tts_basic(monkeypatch):
    import openai
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")
    file_id = f"test_openai_{uuid.uuid4()}"
    audio_path = text_to_audio("Hej världen!", voice="openai", file_id=file_id)
    assert audio_path is not None
    assert audio_path.exists()
    assert audio_path.suffix in (".mp3", ".wav")
    os.remove(audio_path)

def test_voice_pitch_and_speed():
    file_id = f"test_pitch_{uuid.uuid4()}"
    audio_path = text_to_audio("Testar höjd och hastighet", voice="google", file_id=file_id, voice_pitch=2, voice_speed=0.7)
    assert audio_path is not None
    assert audio_path.exists()
    os.remove(audio_path)
