"""Helper script to configure pydub to find ffmpeg in the system.

This script checks for ffmpeg in common install locations and 
adds them to the search path used by pydub.

Run this script before executing any tests that involve audio processing.
"""
import os
import sys
import logging
from pathlib import Path
import subprocess

def find_ffmpeg():
    """Find ffmpeg binary on Windows system.
    
    Searches in common locations:
    1. System PATH
    2. WinGet install locations
    3. Common install directories
    """
    possible_locations = []
    
    # Check in system PATH
    print("Checking for ffmpeg in system PATH...")
    try:
        result = subprocess.run(["where", "ffmpeg"], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            ffmpeg_path = result.stdout.strip().split('\n')[0]
            print(f"Found ffmpeg in PATH: {ffmpeg_path}")
            return Path(ffmpeg_path).parent
    except Exception as e:
        print(f"Error checking PATH: {e}")
    
    # Check in WinGet location
    print("Checking WinGet locations...")
    appdata = os.environ.get("LOCALAPPDATA")
    if appdata:
        winget_dir = Path(appdata) / "Microsoft" / "WinGet" / "Packages"
        if winget_dir.exists():
            # Look for Gyan.FFmpeg directories
            for path in winget_dir.glob("Gyan.FFmpeg*"):
                print(f"Found potential WinGet install: {path}")
                possible_locations.append(path)
    
    # Search inside found directories for bin/ffmpeg.exe
    print("Searching for ffmpeg.exe in installation directories...")
    for base_dir in possible_locations:
        # Case 1: Direct bin folder
        bin_dir = base_dir / "bin"
        if (bin_dir / "ffmpeg.exe").exists():
            print(f"Found ffmpeg.exe in: {bin_dir}")
            return bin_dir
        
        # Case 2: Nested inside version directory
        for nested_dir in base_dir.glob("**"):
            if nested_dir.is_dir():
                if (nested_dir / "bin" / "ffmpeg.exe").exists():
                    print(f"Found ffmpeg.exe in nested directory: {nested_dir / 'bin'}")
                    return nested_dir / "bin"
                elif (nested_dir / "ffmpeg.exe").exists():
                    print(f"Found ffmpeg.exe directly in: {nested_dir}")
                    return nested_dir

    # Common install locations
    print("Checking common installation directories...")
    program_files = os.environ.get("PROGRAMFILES", "C:\\Program Files")
    program_files_x86 = os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")
    common_locations = [
        Path(program_files) / "FFmpeg",
        Path(program_files) / "FFmpeg" / "bin",
        Path(program_files_x86) / "FFmpeg",
        Path(program_files_x86) / "FFmpeg" / "bin",
        Path("C:\\FFmpeg"),
        Path("C:\\FFmpeg") / "bin",
    ]
    
    for location in common_locations:
        if location.exists() and (location / "ffmpeg.exe").exists():
            print(f"Found ffmpeg.exe in common location: {location}")
            return location
    
    print("Could not find ffmpeg installation.")
    return None

def patch_pydub():
    """Patch pydub to use the found ffmpeg path"""
    ffmpeg_dir = find_ffmpeg()
    if not ffmpeg_dir:
        print("Warning: Could not find ffmpeg, pydub may not work correctly.")
        return False
    
    # Monkeypatch pydub to look in this directory first
    import pydub.utils
    
    # Save original get_exe_path
    original_get_exe_path = pydub.utils.get_exe_path
    
    def patched_get_exe_path(prog):
        # Check our found directory first
        custom_path = str(ffmpeg_dir / f"{prog}.exe")
        if os.path.isfile(custom_path):
            return custom_path
        # Fall back to original behavior
        return original_get_exe_path(prog)
    
    # Replace the function with our patched version
    pydub.utils.get_exe_path = patched_get_exe_path
    
    # Verify it works
    try:
        # Force pydub to check for ffmpeg again
        pydub.utils._ffmpeg_available = None
        if pydub.utils.mediainfo_json("test_file_that_doesnt_exist.mp3"):
            print("ERROR: This shouldn't succeed, something is wrong with the patch")
    except:
        # Expected behavior - file doesn't exist but ffmpeg binary was found
        print("Successfully patched pydub to find ffmpeg!")
        return True
    
    return False

if __name__ == "__main__":
    print("=" * 60)
    print("FFmpeg finder and pydub patcher")
    print("=" * 60)
    
    success = patch_pydub()
    
    if success:
        print("\nSuccess! pydub should now find ffmpeg correctly.")
        print("Import this module before running code that uses pydub:")
        print("    import fix_pydub_ffmpeg")
        sys.exit(0)
    else:
        print("\nSomething went wrong. You might need to:")
        print("1. Install ffmpeg manually from https://ffmpeg.org/download.html")
        print("2. Add the bin directory to your PATH variable")
        sys.exit(1)
