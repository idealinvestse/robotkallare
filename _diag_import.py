import importlib
import sys
import traceback
import os

print(f"--- Running diagnostic script ---")
print(f"Current working directory: {os.getcwd()}")
print(f"Python executable: {sys.executable}")
print(f"Initial sys.path: {sys.path}")

# Ensure the project root is in the path
project_root = os.getcwd()
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Inserted project root into sys.path: {project_root}")

print(f"Updated sys.path: {sys.path}")
print(f"\nAttempting to import 'app.api'...")

try:
    # Attempt the import
    mod = importlib.import_module('app.api')
    print(f"\nSUCCESS: Successfully imported 'app.api'")
    print(f"Module location: {mod.__file__}")

    # Check for the 'app' attribute
    if hasattr(mod, 'app'):
        print(f"SUCCESS: Found attribute 'app' in the imported module.")
        app_obj = getattr(mod, 'app')
        print(f"Type of 'app' attribute: {type(app_obj)}")
        if app_obj is None:
            print(f"WARNING: 'app' attribute exists but is None.")
        else:
             print(f"Value of 'app' attribute (type check): {app_obj}") # Avoid printing potentially large objects
    else:
        print(f"FAILURE: Attribute 'app' NOT FOUND in the imported module.")
        print(f"Attributes found: {dir(mod)}")

    sys.exit(0) # Success

except Exception as e:
    print(f"\nFAILURE: An exception occurred during import:")
    traceback.print_exc()
    sys.exit(1) # Failure
