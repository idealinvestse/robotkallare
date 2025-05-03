import os
import logging
import tempfile
import uuid
from pathlib import Path
from subprocess import Popen, PIPE

logger = logging.getLogger("coqui_tts")

# Configuration
PIPER_BINARY = os.getenv("PIPER_BINARY", "/usr/local/bin/piper")
PIPER_MODEL = os.getenv("PIPER_MODEL", "/usr/local/share/piper/sv/sv_SE-marin-medium.onnx")
AUDIO_DIR = Path("static/audio")

def generate_audio_coqui(text, file_id=None, voice_pitch=0, voice_speed=1.0):
    """
    Generate audio using Coqui TTS/Piper
    
    Parameters:
    - text: Text to convert to speech
    - file_id: Optional UUID for the output file (generated if None)
    - voice_pitch: Pitch adjustment (-10 to 10)
    - voice_speed: Speed adjustment (0.5 to 2.0)
    
    Returns:
    - Path to generated audio file or None if generation failed
    """
    try:
        # Generate a file ID if not provided
        if file_id is None:
            file_id = str(uuid.uuid4())
            
        # Ensure valid input
        if not text:
            logger.error("Empty text provided to Coqui TTS function")
            return None
            
        # Define output path
        output_path = AUDIO_DIR / f"{file_id}.wav"
        
        # Create a temporary file for the text
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp:
            temp.write(text)
            temp_path = temp.name
            
        try:
            # Build piper command
            cmd = [
                PIPER_BINARY,
                "--model", PIPER_MODEL,
                "--output_file", str(output_path)
            ]
            
            # Add optional parameters
            if voice_pitch != 0:
                cmd.extend(["--pitch", str(voice_pitch)])
                
            if voice_speed != 1.0:
                cmd.extend(["--rate", str(voice_speed)])
                
            # Input from file
            cmd.extend(["--file", temp_path])
            
            # Execute piper
            logger.info(f"Executing Piper: {' '.join(cmd)}")
            process = Popen(cmd, stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Piper failed: {stderr.decode()}")
                return None
                
            # Convert to MP3 if needed (using pydub)
            try:
                from pydub import AudioSegment
                mp3_path = AUDIO_DIR / f"{file_id}.mp3"
                AudioSegment.from_wav(output_path).export(mp3_path, format="mp3")
                
                # Clean up WAV file
                if mp3_path.exists():
                    os.remove(output_path)
                    return mp3_path
            except Exception as e:
                logger.error(f"Error converting to MP3: {str(e)}")
                # Just return the WAV if conversion fails
                return output_path
                
            return output_path
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        logger.error(f"Error generating speech with Coqui: {str(e)}", exc_info=True)
        return None