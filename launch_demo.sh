#!/bin/bash

# Simple launcher script for GDial demonstration with mockup API responses
echo "Starting GDial in demo mode..."

# Check if Python is available
if command -v python3 &> /dev/null; then
    echo "Using Python to start a simple HTTP server"
    cd /home/oscar/gdial
    python3 -m http.server 8000 &
    SERVER_PID=$!
    echo "Server started with PID: $SERVER_PID"
    echo "Server PID: $SERVER_PID" > server.pid
    echo "Open your browser to http://localhost:8000/static/group-messenger.html"
    echo "Press Ctrl+C to stop the server"
    
    # Wait for user to press Ctrl+C
    trap "kill $SERVER_PID; echo 'Server stopped'; exit 0" INT
    wait
else
    echo "Python not found. Please install Python or use your own web server to serve the static files."
    echo "Open the file /home/oscar/gdial/static/group-messenger.html in your browser."
    exit 1
fi