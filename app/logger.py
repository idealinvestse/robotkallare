import logging
import os
import sys

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
log_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'

# Get root logger
logger = logging.getLogger("app") # Use a specific name for the app's logger
logger.setLevel(log_level)

# Avoid adding multiple handlers if the logger already has them
if not logger.handlers:
    # Console Handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(stream_handler)

    # Optional: File Handler (Uncomment if needed)
    # try:
    #     file_handler = logging.FileHandler("gdial.log")
    #     file_handler.setFormatter(logging.Formatter(log_format))
    #     logger.addHandler(file_handler)
    # except PermissionError:
    #     logger.warning("Could not open gdial.log for writing. Check permissions.")

# Example usage:
# from app.logger import logger
# logger.info("This is an info message.")
# logger.warning("This is a warning.")
