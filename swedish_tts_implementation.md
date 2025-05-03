# Swedish TTS Implementation in GDial

## Overview

This document provides an overview of the Swedish Text-to-Speech (TTS) implementation in GDial using Facebook's MMS-TTS-SWE model. This implementation allows GDial to generate high-quality Swedish voice prompts locally rather than relying on Twilio's built-in TTS capabilities.

## Components Implemented

1. **TTS Module (`app/tts.py`)**
   - Core functionality for text-to-speech conversion
   - Uses Facebook's MMS-TTS-SWE model via Hugging Face Transformers
   - Includes caching and cleanup mechanisms

2. **Twilio Integration Updates**
   - Modified `twilio_io.py` to use generated audio files
   - Updated all TwiML building functions to support Swedish TTS
   - Implemented graceful fallback to Twilio TTS when needed

3. **API Endpoint for Audio Files**
   - Added `/audio/{file_name}` endpoint to serve generated audio files
   - Configured proper media types for MP3 and WAV formats

4. **Background Tasks**
   - Added scheduled cleanup of old audio files 
   - Implemented with APScheduler

## Installation Requirements

Added the following dependencies to `requirements.txt`:
```
apscheduler==3.10.4
torch>=1.12.0
transformers>=4.33.0
scipy>=1.9.0
pydub>=0.25.1
```

## Usage Flow

1. When a call is initiated:
   - The system generates text-to-speech audio using the MMS-TTS-SWE model
   - The audio file is saved to disk in the `static/audio` directory
   - Twilio plays this audio file using the `<Play>` TwiML verb

2. For DTMF responses:
   - Custom response audio is generated for each response
   - Files are named based on message ID and digit pressed

3. Error handling:
   - If TTS generation fails, the system falls back to Twilio's TTS
   - A logging system records all TTS generation events

## Benefits

1. **Higher Quality Swedish Voice**
   - Much better pronunciation of Swedish text
   - More natural intonation and speech patterns

2. **Local Control**
   - Complete control over voice generation
   - No dependency on Twilio's TTS capabilities

3. **Caching for Performance**
   - Frequently used messages are cached for better performance
   - Reduces generation time for repeated messages

4. **Graceful Degradation**
   - Automatic fallback to Twilio TTS if local generation fails

## Technical Details

### File Cache Management
- Audio files are stored in `static/audio/`
- Files older than a threshold are automatically cleaned up
- The cleanup job runs hourly

### Model Initialization
- Model is loaded lazily on first use
- Model weights are cached in memory after first load
- Seed value ensures consistent voice characteristics

### Audio Format
- Default output is MP3 format
- WAV is supported for higher quality when needed
- 24kHz sampling rate from the MMS-TTS-SWE model

## Future Enhancements

1. **Voice Selection**
   - Add support for multiple voices/speakers
   - Allow administrators to choose preferred voice

2. **Pre-Generation for Templates**
   - Pre-generate audio for common templates
   - Improve performance for frequently used messages

3. **Voice Customization**
   - Add controls for speed, pitch, and other parameters
   - Fine-tune voice characteristics for specific use cases

4. **Multi-Language Support**
   - Add other language models as needed
   - Create a language selection mechanism