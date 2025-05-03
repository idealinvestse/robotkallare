#!/bin/bash

# Update all references to static files in HTML and JS files
find static -type f \( -name "*.html" -o -name "*.js" -o -name "*.css" \) -exec sed -i 's|/static/|/ringbot/static/|g' {} \;

# Also update the audio file path in api.py
sed -i 's|"/audio/|"/ringbot/audio/|g' app/api.py