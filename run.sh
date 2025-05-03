#!/bin/bash

# Set strict error handling
set -e 

# Determine which virtual environment to use
if [ -d "gdial_venv" ]; then
    echo "Using gdial_venv environment"
    source gdial_venv/bin/activate
elif [ -d "venv" ]; then
    echo "Using venv environment"
    source venv/bin/activate
else
    echo "Error: No virtual environment found"
    exit 1
fi

# Verify critical packages are installed
if ! python -c "import apscheduler" &> /dev/null; then
    echo "APScheduler not found. Installing now..."
    pip install apscheduler==3.10.4
fi

# Check for PyTorch and install if needed (CPU-only version)
if ! python -c "import torch" &> /dev/null; then
    echo "PyTorch not found. Installing CPU-only version..."
    # Get Python version for compatibility
    PY_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    echo "Python version: $PY_VERSION"
    
    # Try multiple methods to install PyTorch without NVIDIA dependencies
    echo "Attempting to install the latest available CPU-only PyTorch version..."
    pip install torch --index-url https://download.pytorch.org/whl/cpu --no-dependencies || \
    pip install "torch>=2.2.0+cpu" --find-links https://download.pytorch.org/whl/torch_stable.html --no-dependencies || \
    # Last resort: try without version constraint
    pip install torch --no-dependencies
fi

# Check for transformers and install if needed (required for TTS)
if ! python -c "import transformers" &> /dev/null; then
    echo "Transformers not found. Installing..."
    pip install transformers numpy
fi

# Check for additional required dependencies
for pkg in numpy sympy scipy pydub; do
    if ! python -c "import $pkg" &> /dev/null; then
        echo "$pkg not found. Installing..."
        pip install $pkg
    fi
done

# Run the application
uvicorn app.api:app --host 0.0.0.0 --port 3003 --reload
