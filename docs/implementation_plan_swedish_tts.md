# 📋 Historisk implementationsplan: Swedish Text-to-Speech Integration

> **⚠️ HISTORISK DOKUMENTATION**  
> Detta dokument bevaras för historisk referens. Svenska TTS-funktioner har redan implementerats i systemet. Se [swedish_tts_implementation.md](swedish_tts_implementation.md) och [swedish_tts_options.md](swedish_tts_options.md) för aktuell konfiguration.

## Översikt
Detta dokument beskriver den ursprungliga planen för att integrera svenska text-till-tal (TTS) funktioner i GDial-systemet. Målet var att tillhandahålla högkvalitativ svensk röstsyntes för automatiserade samtal och meddelanden.

## 1. Översikt

För närvarande använder GDial Twilios TTS-tjänst via `VoiceResponse.say()`-metoden i TwiML-svaret. Vi kommer att förbättra detta genom:
1. Generating high-quality Swedish audio locally using MMS-TTS-SWE
2. Serving these audio files to Twilio
3. Using Twilio's `<Play>` TwiML verb to deliver the audio during calls

This approach offers several advantages:
- Better Swedish language pronunciation and naturalness
- Complete control over speech generation
- Reduced dependency on Twilio's TTS features
- Ability to save pre-generated audio for frequently used messages

## 2. Technical Components

### 2.1 Required Dependencies

```
# Add to requirements.txt
transformers>=4.33.0
torch>=1.12.0
scipy>=1.9.0
pydub>=0.25.1
```

### 2.2 New Module Structure

Create a new module in `app/tts.py` to handle TTS functionality:

```python
"""Text-to-Speech module for GDial.

Provides functions to generate audio from text using Facebook's MMS-TTS-SWE model.
"""
import os
import uuid
import logging
from pathlib import Path
import torch
from transformers import VitsModel, AutoTokenizer
from scipy.io.wavfile import write
from pydub import AudioSegment

# Setup logging
logger = logging.getLogger("tts")

# Define constants
AUDIO_DIR = Path("static/audio")
AUDIO_CACHE_SIZE = 100  # Number of audio files to keep in cache

# Create audio directory if it doesn't exist
os.makedirs(AUDIO_DIR, exist_ok=True)

# Load model and tokenizer (lazy loading)
_model = None
_tokenizer = None

def _get_model():
    """Lazy load the TTS model."""
    global _model
    if _model is None:
        logger.info("Loading Swedish TTS model")
        _model = VitsModel.from_pretrained("facebook/mms-tts-swe")
    return _model

def _get_tokenizer():
    """Lazy load the tokenizer."""
    global _tokenizer
    if _tokenizer is None:
        logger.info("Loading Swedish TTS tokenizer")
        _tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-swe")
    return _tokenizer

def text_to_audio(text, output_format="mp3", file_id=None):
    """
    Convert text to audio using the Swedish TTS model.
    
    Parameters:
    - text: Text to convert to speech
    - output_format: Output format (mp3 or wav)
    - file_id: Optional UUID for the output file (generated if None)
    
    Returns:
    - Path to generated audio file
    """
    logger.info(f"Converting text to speech: {text[:50]}...")
    
    try:
        # Load model and tokenizer
        model = _get_model()
        tokenizer = _get_tokenizer()
        
        # Generate a file ID if not provided
        if file_id is None:
            file_id = str(uuid.uuid4())
            
        # Ensure valid input
        if not text:
            logger.error("Empty text provided to TTS function")
            return None
            
        # Generate temporary WAV file path
        wav_path = AUDIO_DIR / f"{file_id}.wav"
        
        # Convert text to tokens
        inputs = tokenizer(text, return_tensors="pt")
        
        # Generate audio
        with torch.no_grad():
            output = model(**inputs).waveform
        
        # Save as WAV file
        write(wav_path, 24000, output.float().numpy().squeeze())
        logger.info(f"Generated WAV file: {wav_path}")
        
        # Convert to requested format if not WAV
        if output_format.lower() != "wav":
            output_path = AUDIO_DIR / f"{file_id}.{output_format.lower()}"
            audio = AudioSegment.from_wav(wav_path)
            audio.export(output_path, format=output_format.lower())
            # Remove temporary WAV file
            os.remove(wav_path)
            logger.info(f"Converted to {output_format}: {output_path}")
            return output_path
        
        return wav_path
    
    except Exception as e:
        logger.error(f"Error generating speech: {str(e)}", exc_info=True)
        return None

def clean_audio_cache():
    """
    Clean up old audio files to prevent disk space issues.
    Keeps the AUDIO_CACHE_SIZE most recent files.
    """
    try:
        files = list(AUDIO_DIR.glob("*.mp3")) + list(AUDIO_DIR.glob("*.wav"))
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Delete old files
        if len(files) > AUDIO_CACHE_SIZE:
            for old_file in files[AUDIO_CACHE_SIZE:]:
                os.remove(old_file)
                logger.debug(f"Removed old audio file: {old_file}")
    
    except Exception as e:
        logger.error(f"Error cleaning audio cache: {str(e)}", exc_info=True)
```

### 2.3 Modify `twilio_io.py` to Support TTS

Update the existing TwiML generation functions to use our new TTS system:

```python
# Import the new TTS module
from .tts import text_to_audio

def build_twiml(message_id: Optional[str | uuid.UUID] = None, db: Optional[Session] = None) -> str:
    # ... existing code ...
    
    # If we have a custom message, use it
    if message_content:
        # Generate audio file instead of using say()
        audio_path = text_to_audio(message_content)
        if audio_path:
            # Use absolute URL to ensure Twilio can access the file
            audio_url = f"{base_url}/audio/{audio_path.name}"
            gather.play(url=audio_url)
            twiml_logger.info(f"Using generated audio: {audio_url}")
        else:
            # Fallback to text-to-speech if audio generation fails
            gather.say(message_content)
            twiml_logger.info("Fallback to TTS for custom message content")
    # ... rest of function ...
```

Similar modifications should be made to `build_custom_twiml` and `build_custom_dtmf_response` functions.

### 2.4 Add Audio File Serving Endpoint

Add a new endpoint in `api.py` to serve the generated audio files:

```python
@router.get("/audio/{file_name}", response_class=FileResponse)
async def get_audio_file(file_name: str):
    """Serve a generated audio file."""
    audio_path = Path(f"static/audio/{file_name}")
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(
        audio_path, 
        media_type="audio/mpeg" if file_name.endswith(".mp3") else "audio/wav"
    )
```

### 2.5 Add Scheduled Task for Audio Cache Cleanup

Create a scheduled task to clean up old audio files:

```python
from fastapi import FastAPI, BackgroundTasks
from apscheduler.schedulers.background import BackgroundScheduler
from .tts import clean_audio_cache

def setup_audio_cleanup(app: FastAPI):
    """Setup scheduled audio cleanup task."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(clean_audio_cache, 'interval', hours=1)
    scheduler.start()
    
    # Add event to stop scheduler when shutting down
    @app.on_event("shutdown")
    def shutdown_scheduler():
        scheduler.shutdown()
```

## 3. Implementation Steps

1. **Install Dependencies**
   - Add required packages to requirements.txt
   - Create a script to download the model ahead of time

2. **Create TTS Module**
   - Implement `app/tts.py` with the code above
   - Add unit tests for the TTS functionality

3. **Modify Twilio Integration**
   - Update the TwiML building functions in `twilio_io.py`
   - Make the changes backward compatible

4. **Add Audio Serving Endpoint**
   - Add the endpoint to serve audio files in `api.py`
   - Configure appropriate MIME types

5. **Add Cache Management**
   - Implement automatic cleanup of old audio files
   - Add configuration options for cache size

6. **Testing**
   - Test with various Swedish texts
   - Verify quality of generated speech
   - Test the integration with Twilio

## 4. Configuration Options

Add these configuration parameters to `.env` and `config.py`:

```
# Swedish TTS Configuration
TTS_ENABLED=true
TTS_MODEL="facebook/mms-tts-swe"
TTS_AUDIO_FORMAT="mp3"
TTS_AUDIO_CACHE_SIZE=100
```

## 5. UI Integration (Optional)

For the admin UI, consider adding:
- Preview functionality to listen to generated TTS before sending
- Option to choose between Twilio TTS and local TTS
- Quality settings for audio generation

## 6. Performance Considerations

- Lazy-load the model on first use
- Consider running inference on GPU if available
- Pre-generate audio for common messages
- Monitor disk usage for generated audio files
- Implement proper error handling and fallbacks

## 7. Deployment Requirements

- Sufficient disk space for model and audio files (approx. 500MB)
- Increased memory requirements (min. 2GB RAM recommended)
- GPU support optional but beneficial
- Static file serving properly configured

## 8. Future Enhancements

- Add support for multiple languages and voices
- Implement audio caching at message level
- Add voice customization parameters (speed, pitch)
- Support for more advanced audio processing (normalization, compression)