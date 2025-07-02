# GDial Launch Script

This script simplifies the launch process for GDial by automatically setting up a virtual environment, installing dependencies, and starting the application.

## Features

- **Creates Virtual Environment**: Sets up isolated Python environment for GDial
- **Installs Dependencies**: Automatically installs all required packages
- **GPU Detection**: Detects NVIDIA GPUs and installs PyTorch with CUDA support
- **Pre-downloads TTS Model**: Downloads the Swedish TTS model during setup
- **Logging**: Captures installation logs for troubleshooting
- **Error Handling**: Provides clear error messages if problems occur

## Usage

1. Make the script executable (if not already):
   ```
   chmod +x launch.sh
   ```

2. Run the script:
   ```
   ./launch.sh
   ```

3. The script will:
   - Create a virtual environment in `gdial_venv` (if it doesn't exist)
   - Install all dependencies from `requirements.txt`
   - Pre-download the Swedish TTS model
   - Start the GDial application

## Requirements

- Python 3.8 or higher
- Internet connection for downloading packages
- Sufficient disk space for dependencies (~500MB)

## Advanced Options

You can modify the script to customize:

- Virtual environment location
- Log file naming and location
- Server host and port settings

## Troubleshooting

If you encounter issues:

1. Check the startup log file in the root directory (`startup_YYYY-MM-DD_HH-MM-SS.log`)
2. Ensure Python 3.8+ is installed and available in your PATH
3. Verify that you have write permissions in the GDial directory
4. For TTS issues, try manually installing the transformers package:
   ```
   gdial_venv/bin/pip install transformers torch scipy pydub
   ```

## Notes for GPU Acceleration

If you have an NVIDIA GPU, the script will detect it and install the CUDA-enabled version of PyTorch, which can significantly improve TTS performance.

For optimal performance:
- Ensure your NVIDIA drivers are up to date
- Check that nvidia-smi is available in your PATH
- Consider using CUDA 11.8 compatible drivers