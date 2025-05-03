#!/usr/bin/env python3
import re
import os

# Define the path to the API file
api_file_path = "/home/oscar/gdial/app/api.py"

# Read the API file
with open(api_file_path, 'r') as f:
    api_content = f.read()

# Function to optimize route handling
def optimize_routes(content):
    # Pattern to find pairs of duplicated routes (/path and /ringbot/path)
    pattern = r'@app\.get\("/(.*?)"\)\nasync def ([^:]+).*?return FileResponse\("([^"]+)"\).*?@app\.get\("/ringbot/\1"\)\nasync def ringbot_\2.*?return FileResponse\("\3"\)'
    
    # Replace with optimized route pattern
    replacement = r'@app.get("/\\1")\n@app.get("/ringbot/\\1")\nasync def \\2:\n    """Serve the \\1 page."""\n    return FileResponse("\\3")'
    
    # Apply regex replacement
    optimized_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    return optimized_content

# Apply optimization
optimized_api = optimize_routes(api_content)

# Write to a new file for review
with open("/home/oscar/gdial/app/api_optimized.py", 'w') as f:
    f.write(optimized_api)

print("Optimization complete. New file created at: /home/oscar/gdial/app/api_optimized.py")