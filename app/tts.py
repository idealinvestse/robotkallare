"""Text-to-Speech module for GDial.

Provides functions to generate audio from text using Google's TTS service for Swedish.
"""
import os
import uuid
import logging
from pathlib import Path
from gtts import gTTS
from pydub import AudioSegment

# Setup logging
logger = logging.getLogger("tts")

# Define constants
AUDIO_DIR = Path("static/audio")
AUDIO_CACHE_SIZE = 0  # No caching by default (0 means don't cache)

# Create audio directory if it doesn't exist
os.makedirs(AUDIO_DIR, exist_ok=True)

# Configuration for Swedish TTS
TTS_LANGUAGE = 'sv'  # Swedish language code
TTS_SLOW = False     # Normal speech rate

def text_to_audio(text, output_format="mp3", file_id=None, seed=None, voice_pitch=0, voice_speed=1.0):
    """
    Convert text to audio using Google's TTS service for Swedish.
    
    Parameters:
    - text: Text to convert to speech
    - output_format: Output format (mp3 or wav)
    - file_id: Optional UUID for the output file (generated if None)
    - seed: Not used with Google TTS but kept for API compatibility
    - voice_pitch: Not directly supported by Google TTS but kept for API compatibility
    - voice_speed: Set TTS_SLOW parameter (if voice_speed < 0.8, use slow=True)
    
    Returns:
    - Path to generated audio file
    """
    logger.info(f"Converting text to speech: {text[:50]}...")
    
    try:
        # Generate a file ID if not provided
        if file_id is None:
            file_id = str(uuid.uuid4())
            
        # Ensure valid input
        if not text:
            logger.error("Empty text provided to TTS function")
            return None
        
        # Prepare text for Swedish TTS - handle common issues
        # Add periods to ensure proper pauses if missing
        if not any(text.endswith(c) for c in ['.', '!', '?']):
            text = text + '.'
            
        # Define paths
        if file_id:
            mp3_path = AUDIO_DIR / f"{file_id}.mp3"
            wav_path = AUDIO_DIR / f"{file_id}.wav"
            
            # Remove any existing files with this ID to avoid using cached versions
            if mp3_path.exists():
                os.remove(mp3_path)
                logger.debug(f"Removed existing MP3 file: {mp3_path}")
            if wav_path.exists():
                os.remove(wav_path)
                logger.debug(f"Removed existing WAV file: {wav_path}")
        
        try:
            # Determine if we should use slow speech rate
            use_slow = voice_speed < 0.8 if voice_speed else TTS_SLOW
            
            # Initialize Google TTS with Swedish language
            tts = gTTS(text=text, lang=TTS_LANGUAGE, slow=use_slow)
            
            # Save directly as MP3 (Google TTS only outputs MP3)
            mp3_path = AUDIO_DIR / f"{file_id}.mp3"
            tts.save(str(mp3_path))
            logger.info(f"Generated MP3 file with Google TTS: {mp3_path}")
            
            # If requested format is WAV, convert from MP3
            if output_format.lower() == "wav":
                wav_path = AUDIO_DIR / f"{file_id}.wav"
                audio = AudioSegment.from_mp3(mp3_path)
                
                # Apply voice modifications if needed
                if voice_pitch != 0:
                    try:
                        # Basic pitch shifting with pydub
                        octaves = float(voice_pitch) / 12.0
                        new_sample_rate = int(audio.frame_rate * (2.0 ** octaves))
                        audio = audio._spawn(audio.raw_data, overrides={
                            "frame_rate": new_sample_rate
                        })
                        audio = audio.set_frame_rate(44100)  # Reset to standard frame rate
                        logger.info(f"Applied pitch shift of {voice_pitch}")
                    except Exception as e:
                        logger.warning(f"Could not apply pitch shift: {e}")
                
                # Export to WAV
                audio.export(wav_path, format="wav")
                
                # Clean up MP3 if not needed
                if output_format.lower() != "mp3":
                    os.remove(mp3_path)
                    
                logger.info(f"Converted to WAV: {wav_path}")
                return wav_path
            
            # For MP3 output with modifications
            if voice_pitch != 0 and output_format.lower() == "mp3":
                try:
                    # Load the MP3
                    audio = AudioSegment.from_mp3(mp3_path)
                    
                    # Apply pitch shifting
                    octaves = float(voice_pitch) / 12.0
                    new_sample_rate = int(audio.frame_rate * (2.0 ** octaves))
                    audio = audio._spawn(audio.raw_data, overrides={
                        "frame_rate": new_sample_rate
                    })
                    audio = audio.set_frame_rate(44100)  # Reset to standard frame rate
                    
                    # Save back to MP3
                    audio.export(mp3_path, format="mp3")
                    logger.info(f"Applied pitch shift of {voice_pitch} to MP3")
                except Exception as e:
                    logger.warning(f"Could not apply pitch shift to MP3: {e}")
            
            return mp3_path
            
        except Exception as e:
            logger.error(f"Error in Google TTS generation: {str(e)}", exc_info=True)
            # If we have a fallback mechanism, we would call it here
            return None
    
    except Exception as e:
        logger.error(f"Error generating speech: {str(e)}", exc_info=True)
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

def get_audio_url(file_path, base_url):
    """
    Generate a URL for accessing an audio file.
    
    Parameters:
    - file_path: Path to the audio file
    - base_url: Base URL for the application
    
    Returns:
    - Full URL to access the audio file
    """
    if not file_path:
        return None
        
    file_name = Path(file_path).name
    return f"{base_url}/audio/{file_name}"

def generate_message_audio(message_content, base_url=None, message_id=None):
    """
    Generate audio for a message and return the playable URL.
    
    Parameters:
    - message_content: Text content to convert to speech
    - base_url: Base URL for the application (required for URL generation)
    - message_id: Optional message ID to use as file identifier
    
    Returns:
    - Audio URL or None if generation failed
    """
    if not message_content or not base_url:
        return None
        
    # Use message_id as file_id if available, otherwise generate random UUID
    file_id = str(message_id) if message_id else None
    
    # Generate audio file
    audio_path = text_to_audio(message_content, file_id=file_id)
    
    # Return URL if generation was successful
    if audio_path:
        return get_audio_url(audio_path, base_url)
    
    return None