#!/usr/bin/env python

import logging
import sqlite3
import os
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

DB_PATH = "dialer.db"

def backup_database():
    """Create a backup of the database."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{DB_PATH}.backup_{timestamp}"
    try:
        with open(DB_PATH, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        logger.info(f"Created backup of database to {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to backup database: {e}")
        return False

def create_custom_data_column():
    """Add the custom_data column to both CallRun and CallLog tables."""
    conn = sqlite3.connect(DB_PATH)
    try:
        # First check if the column already exists in CallRun
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(callrun)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "custom_data" not in columns:
            logger.info("Adding custom_data column to callrun table...")
            conn.execute("ALTER TABLE callrun ADD COLUMN custom_data JSON")
            logger.info("custom_data column added to callrun table")
        else:
            logger.info("custom_data column already exists in callrun table")
            
        # Check if the column already exists in CallLog
        cursor.execute("PRAGMA table_info(calllog)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "custom_data" not in columns:
            logger.info("Adding custom_data column to calllog table...")
            conn.execute("ALTER TABLE calllog ADD COLUMN custom_data JSON")
            logger.info("custom_data column added to calllog table")
        else:
            logger.info("custom_data column already exists in calllog table")
            
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error adding custom_data columns: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """Main function to run the migration."""
    logger.info("Starting custom_data column migration...")
    
    # Backup the database first
    if not backup_database():
        logger.error("Failed to backup database. Aborting migration.")
        return False
    
    # Add the custom_data column
    if not create_custom_data_column():
        logger.error("Failed to add custom_data columns. Aborting migration.")
        return False
    
    logger.info("Migration completed successfully")
    return True

if __name__ == "__main__":
    if main():
        print("Database migration completed successfully.")
        print(f"A backup of the original database was created at {DB_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    else:
        print("Database migration failed. Please check the logs.")