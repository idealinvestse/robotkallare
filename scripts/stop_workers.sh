#!/bin/bash
# Script to stop GDial workers

# Set current directory to script directory
cd "$(dirname "$0")/.."

# Stop TTS worker
if [ -f logs/tts_worker.pid ]; then
    TTS_PID=$(cat logs/tts_worker.pid)
    echo "Stopping TTS worker (PID: $TTS_PID)..."
    kill $TTS_PID 2>/dev/null || echo "TTS worker not running"
    rm logs/tts_worker.pid
else
    echo "TTS worker PID file not found"
fi

# Stop Call worker
if [ -f logs/call_worker.pid ]; then
    CALL_PID=$(cat logs/call_worker.pid)
    echo "Stopping Call worker (PID: $CALL_PID)..."
    kill $CALL_PID 2>/dev/null || echo "Call worker not running"
    rm logs/call_worker.pid
else
    echo "Call worker PID file not found"
fi

echo "Workers stopped."