#!/bin/bash

# GDial Database Repair and Launch Script
# This script fixes database issues, creates a virtual environment,
# installs dependencies, and starts the GDial application

# Print colorful messages
print_message() {
    local color=$1
    local message=$2
    case $color in
        "green") echo -e "\e[32m$message\e[0m" ;;
        "yellow") echo -e "\e[33m$message\e[0m" ;;
        "red") echo -e "\e[31m$message\e[0m" ;;
        "blue") echo -e "\e[34m$message\e[0m" ;;
        *) echo "$message" ;;
    esac
}

# Create a timestamp for logs
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="startup_${TIMESTAMP}.log"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_message "red" "Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Determine Python version
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
print_message "blue" "Using Python $PYTHON_VERSION"

# Check for virtual environment directory
VENV_DIR="gdial_venv"
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    print_message "yellow" "Creating virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    
    if [ ! -d "$VENV_DIR" ]; then
        print_message "red" "Failed to create virtual environment. Please check your Python installation."
        exit 1
    fi
else
    print_message "green" "Using existing virtual environment: $VENV_DIR"
fi

# Activate virtual environment and install dependencies
print_message "yellow" "Installing dependencies..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
print_message "blue" "Upgrading pip..."
"$VENV_PIP" install --upgrade pip >> "$LOG_FILE" 2>&1

# Install dependencies from requirements.txt
if [ -f "requirements.txt" ]; then
    print_message "blue" "Installing requirements from requirements.txt..."
    "$VENV_PIP" install -r requirements.txt >> "$LOG_FILE" 2>&1
    
    if [ $? -ne 0 ]; then
        print_message "red" "Failed to install dependencies. See $LOG_FILE for details."
        exit 1
    fi
else
    print_message "red" "requirements.txt not found. Cannot install dependencies."
    exit 1
fi

# Check if we need to install PyTorch with GPU support
if command -v nvidia-smi &> /dev/null; then
    print_message "yellow" "NVIDIA GPU detected, installing PyTorch with CUDA support..."
    "$VENV_PIP" install torch --index-url https://download.pytorch.org/whl/cu118 >> "$LOG_FILE" 2>&1
fi

# Create static/audio directory if it doesn't exist
if [ ! -d "static/audio" ]; then
    print_message "blue" "Creating audio directory..."
    mkdir -p static/audio
fi

# Check if database exists
if [ -f "dialer.db" ]; then
    print_message "yellow" "Database found. Checking if migration is needed..."
    
    # Backup the database before any changes
    DB_BACKUP="dialer.db.backup_${TIMESTAMP}"
    cp dialer.db "$DB_BACKUP"
    print_message "green" "Database backed up to $DB_BACKUP"
    
    # Run the migration script to update the schema
    print_message "blue" "Running database migration script..."
    "$VENV_PYTHON" migrate_db.py
    
    if [ $? -ne 0 ]; then
        print_message "red" "Database migration failed. Restoring from backup..."
        cp "$DB_BACKUP" dialer.db
        print_message "yellow" "Original database restored. Please check the migration logs for details."
        exit 1
    else
        print_message "green" "Database migration completed successfully."
    fi
else
    print_message "yellow" "Database file not found. It will be created on first run."
fi

# Pre-download Hugging Face model (optional)
print_message "blue" "Pre-downloading TTS model (this may take a while)..."
"$VENV_PYTHON" -c "from transformers import VitsModel, AutoTokenizer; \
                  tokenizer = AutoTokenizer.from_pretrained('facebook/mms-tts-swe'); \
                  model = VitsModel.from_pretrained('facebook/mms-tts-swe')" >> "$LOG_FILE" 2>&1

# Run the application
print_message "green" "Starting GDial system..."
if [ -f "run_with_logging.sh" ]; then
    # Make executable if it's not
    if [ ! -x "run_with_logging.sh" ]; then
        chmod +x run_with_logging.sh
    fi
    ./run_with_logging.sh
elif [ -f "run.sh" ]; then
    # Make executable if it's not
    if [ ! -x "run.sh" ]; then
        chmod +x run.sh
    fi
    ./run.sh
else
    # Fallback if run scripts are not available
    "$VENV_PYTHON" -m uvicorn app.api:app --host 0.0.0.0 --port 8000
fi

# If we get here, launch failed
print_message "red" "GDial failed to start. Please check the logs for details."
exit 1