#!/bin/bash

# ==============================================================================
# GDial Advanced Launch Script
# This script provides a robust environment setup, dependency management,
# and application startup with comprehensive error handling and recovery
# ==============================================================================

# ----- Script Configuration -----
set -o pipefail  # Fail on pipeline errors

# ----- Color Configuration -----
COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[0;33m'
COLOR_BLUE='\033[0;34m'
COLOR_PURPLE='\033[0;35m'
COLOR_CYAN='\033[0;36m'
COLOR_RESET='\033[0m'

# ----- Timestamp and Logging -----
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_DIR="logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/startup_${TIMESTAMP}.log"
DEPENDENCY_LOG="$LOG_DIR/dependencies_${TIMESTAMP}.log"

# ----- Script Paths -----
VENV_DIR="gdial_venv"
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"
REQUIREMENTS_FILE="requirements.txt"
DB_FILE="dialer.db"
MIGRATION_SCRIPT="migrate_db.py"

# ----- Package Configuration -----
# Packages to skip during installation (add more as needed)
SKIP_PACKAGES=(
    "nvidia_nccl_cu12-2.26.2-py3-none-manylinux2014_x86_64.manylinux_2_17_x86_64.whl"
    "nvidia-nccl"
    "nvidia-nccl-cu12"
)

# ----- Function Definitions -----

# Print colorful message with timestamp and log to file
log_message() {
    local color=$1
    local type=$2
    local message=$3
    local color_code
    
    case $color in
        "red") color_code=$COLOR_RED ;;
        "green") color_code=$COLOR_GREEN ;;
        "yellow") color_code=$COLOR_YELLOW ;;
        "blue") color_code=$COLOR_BLUE ;;
        "purple") color_code=$COLOR_PURPLE ;;
        "cyan") color_code=$COLOR_CYAN ;;
        *) color_code="" ;;
    esac
    
    # Format the message
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    local log_line="[$timestamp] [$type] $message"
    
    # Print to console with color
    echo -e "${color_code}$log_line${COLOR_RESET}"
    
    # Log to file without color codes
    echo "$log_line" >> "$LOG_FILE"
}

# Check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Check Python version and requirements
check_python() {
    log_message "blue" "SETUP" "Checking Python installation..."
    
    if ! command_exists python3; then
        log_message "red" "ERROR" "Python 3 is not installed. Please install Python 3 and try again."
        exit 1
    fi
    
    local python_version=$(python3 --version 2>&1 | awk '{print $2}')
    local python_major=$(echo "$python_version" | cut -d. -f1)
    local python_minor=$(echo "$python_version" | cut -d. -f2)
    
    log_message "blue" "INFO" "Found Python $python_version"
    
    # Check Python version requirements
    if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 8 ]); then
        log_message "yellow" "WARNING" "Python 3.8+ is recommended. You are using Python $python_version"
    fi
    
    # Check for required Python modules for venv creation
    if ! python3 -c "import venv" &> /dev/null; then
        log_message "red" "ERROR" "Python venv module is not available. Please install it and try again."
        exit 1
    fi
}

# Create or update virtual environment
setup_venv() {
    log_message "blue" "SETUP" "Setting up virtual environment..."
    
    if [ ! -d "$VENV_DIR" ]; then
        log_message "yellow" "SETUP" "Creating new virtual environment in $VENV_DIR..."
        python3 -m venv "$VENV_DIR"
        
        if [ ! -d "$VENV_DIR" ]; then
            log_message "red" "ERROR" "Failed to create virtual environment. Check Python installation."
            exit 1
        fi
        
        log_message "green" "SUCCESS" "Virtual environment created successfully"
    else
        log_message "blue" "INFO" "Using existing virtual environment: $VENV_DIR"
        
        # Validate existing venv
        if [ ! -f "$VENV_PYTHON" ]; then
            log_message "red" "ERROR" "Virtual environment exists but appears to be corrupted."
            log_message "yellow" "REPAIR" "Attempting to repair by creating a new environment..."
            
            # Backup the old environment
            mv "$VENV_DIR" "${VENV_DIR}_backup_${TIMESTAMP}"
            python3 -m venv "$VENV_DIR"
            
            if [ ! -d "$VENV_DIR" ]; then
                log_message "red" "ERROR" "Failed to create new virtual environment. Exiting."
                exit 1
            fi
            
            log_message "green" "SUCCESS" "Created new virtual environment successfully"
        fi
    fi
    
    # Ensure pip is available in the virtual environment
    if [ ! -f "$VENV_PIP" ]; then
        log_message "red" "ERROR" "pip not found in virtual environment. Attempting to install..."
        "$VENV_PYTHON" -m ensurepip
        
        if [ ! -f "$VENV_PIP" ]; then
            log_message "red" "ERROR" "Failed to install pip in virtual environment. Exiting."
            exit 1
        fi
    fi
    
    # Activate the virtual environment
    log_message "blue" "SETUP" "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    log_message "blue" "SETUP" "Upgrading pip..."
    "$VENV_PIP" install --upgrade pip setuptools wheel >> "$DEPENDENCY_LOG" 2>&1
    
    if [ $? -ne 0 ]; then
        log_message "yellow" "WARNING" "Failed to upgrade pip. Continuing with existing version."
    else
        log_message "green" "SUCCESS" "pip upgraded successfully"
    fi
}

# Generate pip install command with appropriate flags for skipping problematic packages
generate_pip_install_command() {
    local cmd="$VENV_PIP install -r $REQUIREMENTS_FILE"
    
    # Add flags for skipping problematic packages
    local skip_flags=""
    for pkg in "${SKIP_PACKAGES[@]}"; do
        skip_flags="$skip_flags --exclude $pkg"
    done
    
    # Add additional helpful flags
    cmd="$cmd $skip_flags --no-build-isolation --no-cache-dir"
    
    echo "$cmd"
}

# Install dependencies with robust error handling and retry logic
install_dependencies() {
    log_message "blue" "SETUP" "Installing dependencies..."
    
    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        log_message "red" "ERROR" "$REQUIREMENTS_FILE not found. Cannot install dependencies."
        exit 1
    fi
    
    # Set PyTorch index URL for better compatibility
    export PIP_EXTRA_INDEX_URL="https://download.pytorch.org/whl/cu118"
    
    # Ensure APScheduler is installed first (critical dependency)
    log_message "blue" "INSTALL" "Installing APScheduler (critical dependency)..."
    "$VENV_PIP" install apscheduler==3.10.4 >> "$DEPENDENCY_LOG" 2>&1
    
    # First attempt: try with standard installation
    log_message "blue" "INSTALL" "Installing packages (attempt 1/3)..."
    "$VENV_PIP" install -r "$REQUIREMENTS_FILE" >> "$DEPENDENCY_LOG" 2>&1
    
    # If first attempt fails, try with skip flags
    if [ $? -ne 0 ]; then
        log_message "yellow" "RETRY" "Standard installation failed. Trying with package exclusions (attempt 2/3)..."
        
        # Generate and execute command with exclusions
        local pip_cmd=$(generate_pip_install_command)
        log_message "cyan" "COMMAND" "Running: $pip_cmd"
        eval "$pip_cmd" >> "$DEPENDENCY_LOG" 2>&1
        
        # If second attempt fails, try installing packages one by one
        if [ $? -ne 0 ]; then
            log_message "yellow" "RETRY" "Bulk installation failed. Installing packages individually (attempt 3/3)..."
            
            # Read requirements file line by line and install each package separately
            while IFS= read -r line || [ -n "$line" ]; do
                # Skip comments and empty lines
                if [[ $line =~ ^#.*$ ]] || [[ -z "${line// }" ]]; then
                    continue
                fi
                
                # Extract package name (remove version specification)
                package=$(echo "$line" | cut -d'=' -f1 | cut -d'<' -f1 | cut -d'>' -f1 | cut -d'[' -f1 | cut -d'~' -f1 | cut -d'^' -f1 | cut -d' ' -f1)
                
                # Skip if package is in SKIP_PACKAGES
                skip=false
                for skip_pkg in "${SKIP_PACKAGES[@]}"; do
                    if [[ "$package" == *"$skip_pkg"* ]] || [[ "$skip_pkg" == *"$package"* ]]; then
                        skip=true
                        break
                    fi
                done
                
                if [ "$skip" = true ]; then
                    log_message "cyan" "SKIP" "Skipping package: $package"
                    continue
                fi
                
                log_message "cyan" "INSTALL" "Installing package: $package"
                "$VENV_PIP" install "$line" --no-cache-dir --no-build-isolation >> "$DEPENDENCY_LOG" 2>&1
                
                if [ $? -ne 0 ]; then
                    log_message "yellow" "WARNING" "Failed to install $package, continuing with next package"
                fi
            done < "$REQUIREMENTS_FILE"
            
            # Final verification
            log_message "blue" "VERIFY" "Verifying critical dependencies..."
            missing_critical=false
            
            # List critical packages that must be present for the application to function
            critical_packages=("fastapi" "uvicorn" "sqlmodel" "twilio" "httpx" "apscheduler" "transformers" "numpy" "sympy" "scipy" "pydub")
            
            for pkg in "${critical_packages[@]}"; do
                if ! "$VENV_PYTHON" -c "import $pkg" &> /dev/null; then
                    log_message "red" "ERROR" "Critical package $pkg is missing"
                    missing_critical=true
                fi
            done
            
            if [ "$missing_critical" = true ]; then
                log_message "yellow" "REPAIR" "Some critical dependencies are missing. Attempting to fix..."
                # Try to repair by installing missing packages directly
                install_missing_packages
                
                # Check again if we fixed the issue
                missing_critical=false
                for pkg in "${critical_packages[@]}"; do
                    if ! "$VENV_PYTHON" -c "import $pkg" &> /dev/null; then
                        log_message "red" "ERROR" "Critical package $pkg is still missing"
                        missing_critical=true
                    fi
                done
                
                if [ "$missing_critical" = true ]; then
                    log_message "red" "ERROR" "Failed to install all critical dependencies."
                    log_message "yellow" "ACTION" "Check $DEPENDENCY_LOG for details. You may need to install packages manually."
                    log_message "yellow" "CONTINUE" "Continuing with startup, but application may not function correctly."
                else
                    log_message "green" "SUCCESS" "All critical dependencies are now installed"
                fi
            else
                log_message "green" "SUCCESS" "All critical dependencies are installed"
            fi
        else
            log_message "green" "SUCCESS" "Dependencies installed with exclusions"
        fi
    else
        log_message "green" "SUCCESS" "Dependencies installed successfully"
    fi
    
    # Check for TTS dependencies separately as they're more complex
    check_tts_dependencies
}

# Check and install TTS-specific dependencies
check_tts_dependencies() {
    log_message "blue" "SETUP" "Checking TTS dependencies..."
    
    # Verify torch is installed 
    if ! "$VENV_PYTHON" -c "import torch" &> /dev/null; then
        log_message "yellow" "INSTALL" "PyTorch not found, installing..."
        
        # Alternative installation methods for PyTorch (trying multiple approaches)
        log_message "blue" "INSTALL" "Installing PyTorch CPU-only version (attempt 1)..."
        
        # Get Python version for compatibility
        PY_VERSION=$("$VENV_PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        log_message "blue" "INFO" "Python version: $PY_VERSION"
        
        # Method 1: Install latest CPU-only version with explicit options
        log_message "blue" "INSTALL" "Attempting to install the latest available CPU-only PyTorch..."
        "$VENV_PIP" install torch --index-url https://download.pytorch.org/whl/cpu \
            --no-deps --no-cache-dir --no-build-isolation >> "$DEPENDENCY_LOG" 2>&1
        
        # Check if installation succeeded
        if ! "$VENV_PYTHON" -c "import torch" &> /dev/null; then
            log_message "yellow" "RETRY" "PyTorch installation failed, trying alternative method (attempt 2)..."
            
            # Method 2: Use torch_stable with newer version
            "$VENV_PIP" install "torch>=2.2.0+cpu" --find-links https://download.pytorch.org/whl/torch_stable.html \
                --no-deps --no-cache-dir >> "$DEPENDENCY_LOG" 2>&1
                
            # Check if installation succeeded
            if ! "$VENV_PYTHON" -c "import torch" &> /dev/null; then
                log_message "yellow" "RETRY" "PyTorch installation failed, trying standard installation (attempt 3)..."
                
                # Method 3: Just try standard PyPI without version constraint
                "$VENV_PIP" install torch --no-deps >> "$DEPENDENCY_LOG" 2>&1
                
                if ! "$VENV_PYTHON" -c "import torch" &> /dev/null; then
                    log_message "red" "ERROR" "All PyTorch installation attempts failed. TTS functionality will not work."
                else
                    log_message "green" "SUCCESS" "Minimal PyTorch installed successfully"
                fi
            else
                log_message "green" "SUCCESS" "PyTorch installed successfully using alternative method"
            fi
        else
            log_message "green" "SUCCESS" "PyTorch CPU version installed successfully"
        fi
    fi
    
    # Verify transformers is installed for the TTS models
    if ! "$VENV_PYTHON" -c "import transformers" &> /dev/null; then
        log_message "yellow" "INSTALL" "Transformers library not found, installing..."
        "$VENV_PIP" install transformers >> "$DEPENDENCY_LOG" 2>&1
        
        if [ $? -ne 0 ]; then
            log_message "yellow" "WARNING" "Failed to install transformers. TTS functionality may not work correctly."
        else
            log_message "green" "SUCCESS" "Transformers library installed successfully"
        fi
    fi
}

# Check for Swedish TTS model and prepare directories
setup_tts() {
    log_message "blue" "SETUP" "Setting up TTS system..."
    
    # Create TTS model directory
    TTS_DIR="$VENV_DIR/tts_models"
    if [ ! -d "$TTS_DIR" ]; then
        log_message "blue" "SETUP" "Creating TTS models directory..."
        mkdir -p "$TTS_DIR"
    fi
    
    # Create audio directory for TTS output files
    AUDIO_DIR="static/audio"
    if [ ! -d "$AUDIO_DIR" ]; then
        log_message "blue" "SETUP" "Creating audio output directory..."
        mkdir -p "$AUDIO_DIR"
    fi
    
    # Check if we can import required modules for TTS
    if "$VENV_PYTHON" -c "import torch, transformers" &> /dev/null; then
        log_message "blue" "SETUP" "Checking for Swedish TTS model..."
        
        # Try to initialize the model to verify it can be loaded
        # This will download the model if it doesn't exist locally
        log_message "blue" "DOWNLOAD" "Pre-downloading TTS model (this may take a while)..."
        "$VENV_PYTHON" -c "
try:
    from transformers import AutoTokenizer, VitsModel
    print('Downloading tokenizer...')
    tokenizer = AutoTokenizer.from_pretrained('facebook/mms-tts-swe')
    print('Downloading model...')
    model = VitsModel.from_pretrained('facebook/mms-tts-swe')
    print('Model downloaded successfully')
except Exception as e:
    print(f'Error downloading model: {e}')
    exit(1)
" >> "$DEPENDENCY_LOG" 2>&1
        
        if [ $? -ne 0 ]; then
            log_message "yellow" "WARNING" "Failed to download TTS model. Will attempt download at runtime."
        else
            log_message "green" "SUCCESS" "TTS model downloaded successfully"
        fi
    else
        log_message "yellow" "WARNING" "Required TTS modules not available. Model download skipped."
    fi
}

# Check and run database migrations if needed
run_migrations() {
    log_message "blue" "SETUP" "Checking database and migrations..."
    
    # Check if database file exists
    if [ ! -f "$DB_FILE" ]; then
        log_message "yellow" "INFO" "Database file not found. It will be created on first run."
    else
        log_message "green" "INFO" "Database file found: $DB_FILE"
    fi
    
    # Check if migration script exists and run it
    if [ -f "$MIGRATION_SCRIPT" ]; then
        log_message "blue" "MIGRATE" "Running database migrations..."
        
        "$VENV_PYTHON" "$MIGRATION_SCRIPT" >> "$LOG_FILE" 2>&1
        
        if [ $? -ne 0 ]; then
            log_message "yellow" "WARNING" "Database migration failed. Application may not work correctly."
        else
            log_message "green" "SUCCESS" "Database migration completed successfully"
        fi
    else
        log_message "blue" "INFO" "No migration script found. Skipping migrations."
    fi
}

# Start the application with proper error handling
start_application() {
    log_message "green" "START" "Starting GDial system..."
    
    # Check for all possible run scripts
    if [ -f "run_with_logging.sh" ]; then
        chmod +x run_with_logging.sh
        ./run_with_logging.sh
        RUN_EXIT_CODE=$?
    elif [ -f "run.sh" ]; then
        chmod +x run.sh
        ./run.sh
        RUN_EXIT_CODE=$?
    else
        # Fallback if run scripts are not available
        log_message "yellow" "WARNING" "No run script found. Starting application directly..."
        "$VENV_PYTHON" -m uvicorn app.api:app --host 0.0.0.0 --port 8000
        RUN_EXIT_CODE=$?
    fi
    
    # Handle exit code
    if [ $RUN_EXIT_CODE -ne 0 ]; then
        log_message "red" "ERROR" "GDial exited with error code $RUN_EXIT_CODE"
        log_message "yellow" "ACTION" "Check server logs for more details"
        exit $RUN_EXIT_CODE
    else
        log_message "green" "SUCCESS" "GDial completed successfully"
        exit 0
    fi
}

# Function to trap and handle script termination
handle_exit() {
    log_message "yellow" "EXIT" "Script terminated. Cleaning up..."
    
    # Perform any necessary cleanup here
    
    exit 1
}

# Function to manually install missing critical packages
install_missing_packages() {
    log_message "yellow" "REPAIR" "Installing missing critical packages..."
    
    # List of critical packages with versions
    "$VENV_PIP" install apscheduler==3.10.4 fastapi==0.115.2 uvicorn[standard]==0.32.0 sqlmodel==0.0.24 \
                     twilio==9.5.2 httpx==0.27.2 python-multipart==0.0.7 transformers numpy \
                     sympy scipy pydub >> "$DEPENDENCY_LOG" 2>&1
    
    if [ $? -ne 0 ]; then
        log_message "red" "ERROR" "Failed to install critical packages manually."
        return 1
    else
        log_message "green" "SUCCESS" "Critical packages installed manually."
        return 0
    fi
}

# ----- Main Execution Flow -----

# Set up trap for Ctrl+C and other termination signals
trap handle_exit SIGINT SIGTERM

# Print banner
echo -e "${COLOR_BLUE}"
echo "======================================================"
echo "  GDial Advanced Launch Script - v2.0"
echo "  $(date)"
echo "======================================================"
echo -e "${COLOR_RESET}"

# Initialize log file with header
echo "=====================================================" > "$LOG_FILE"
echo "GDial Launch Log - $TIMESTAMP" >> "$LOG_FILE"
echo "=====================================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Run all setup steps in sequence
log_message "green" "START" "Starting GDial setup process..."

check_python
setup_venv
install_dependencies
setup_tts
run_migrations
start_application

# We should not reach here unless there's a bug in the script
log_message "red" "ERROR" "Unexpected end of script"
exit 1