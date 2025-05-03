#!/bin/bash
# Script to start GDial workers

# Set current directory to script directory
cd "$(dirname "$0")/.."

# Activate virtual environment
source venv/bin/activate

# Create necessary log directories
mkdir -p logs

# Start TTS worker
echo "Starting TTS worker..."
python app/workers/tts_worker.py >> logs/tts_worker.log 2>&1 &
TTS_PID=$!
echo $TTS_PID > logs/tts_worker.pid

# Start Call worker
echo "Starting Call worker..."
python app/workers/call_worker.py >> logs/call_worker.log 2>&1 &
CALL_PID=$!
echo $CALL_PID > logs/call_worker.pid

echo "Workers started. PIDs:"
echo "TTS Worker: $TTS_PID"
echo "Call Worker: $CALL_PID"
echo "To stop workers, run: ./scripts/stop_workers.sh"