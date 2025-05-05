"""
FFmpeg helper module for GDial.

Helps locate FFmpeg binaries and configures the environment correctly.
"""
import os
import sys
import shutil
import platform
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def find_ffmpeg():
    """
    Find the ffmpeg binary in common locations.
    Returns the path to the directory containing ffmpeg binaries, or None if not found.
    """
    # First check if it's in the PATH
    ffmpeg_command = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
    ffmpeg_path = shutil.which(ffmpeg_command)
    
    if ffmpeg_path:
        logger.info(f"Found ffmpeg in PATH: {ffmpeg_path}")
        return Path(ffmpeg_path).parent
    
    # Common locations by platform
    if platform.system() == "Windows":
        # WinGet locations
        appdata = os.environ.get("LOCALAPPDATA")
        if appdata:
            winget_dir = Path(appdata) / "Microsoft" / "WinGet" / "Packages"
            if winget_dir.exists():
                # Look for Gyan.FFmpeg directories
                for root_dir in winget_dir.glob("Gyan.FFmpeg*"):
                    # Search recursively for bin/ffmpeg.exe
                    for bin_dir in root_dir.glob("**/bin"):
                        if (bin_dir / "ffmpeg.exe").exists():
                            logger.info(f"Found ffmpeg in WinGet: {bin_dir}")
                            return bin_dir
        
        # Other common Windows locations
        common_locations = [
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "FFmpeg" / "bin",
            Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")) / "FFmpeg" / "bin",
            Path("C:\\FFmpeg") / "bin",
        ]
    elif platform.system() == "Darwin":  # macOS
        common_locations = [
            Path("/usr/local/bin"),
            Path("/usr/bin"),
            Path("/opt/homebrew/bin"),
        ]
    else:  # Linux and others
        common_locations = [
            Path("/usr/bin"),
            Path("/usr/local/bin"),
            Path("/usr/local/ffmpeg/bin"),
        ]
    
    for location in common_locations:
        ffmpeg_file = location / ffmpeg_command
        if location.exists() and ffmpeg_file.exists():
            logger.info(f"Found ffmpeg in: {location}")
            return location
    
    logger.warning("ffmpeg not found in any common location")
    return None

def configure_ffmpeg():
    """
    Configure the environment to find and use ffmpeg binaries.
    Returns True if configured successfully, False otherwise.
    """
    ffmpeg_dir = find_ffmpeg()
    if not ffmpeg_dir:
        logger.warning(
            "FFmpeg not found. Audio conversion features may not work properly. "
            "Please install FFmpeg and make sure it's in your PATH."
        )
        return False
    
    # Set environment variables for tools like pydub to find ffmpeg
    if platform.system() == "Windows":
        ffmpeg_path = str(ffmpeg_dir / "ffmpeg.exe")
        ffprobe_path = str(ffmpeg_dir / "ffprobe.exe")
    else:
        ffmpeg_path = str(ffmpeg_dir / "ffmpeg")
        ffprobe_path = str(ffmpeg_dir / "ffprobe")
    
    os.environ["FFMPEG_BINARY"] = ffmpeg_path
    os.environ["FFPROBE_BINARY"] = ffprobe_path
    
    # Also update PATH just to be safe
    if str(ffmpeg_dir) not in os.environ.get("PATH", ""):
        path_sep = ";" if platform.system() == "Windows" else ":"
        os.environ["PATH"] = f"{str(ffmpeg_dir)}{path_sep}{os.environ.get('PATH', '')}"
    
    logger.info(f"FFmpeg configured: {ffmpeg_path}")
    return True

# Auto-configure when this module is imported
configured = configure_ffmpeg()
if not configured:
    logger.warning(
        "To enable audio features, install FFmpeg: https://ffmpeg.org/download.html "
        "and restart the application."
    )
