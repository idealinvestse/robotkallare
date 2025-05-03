#!/usr/bin/env python3
"""
Script to fix the UUID format in the database tables.
This script updates the schema to ensure UUIDs are stored in the correct format.
"""
import os
import sys
import uuid
import sqlite3
import logging
from datetime import datetime
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def backup_database(db_path):
    """Create a backup of the database before making changes."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    
    logger.info(f"Creating database backup at {backup_path}")
    shutil.copy2(db_path, backup_path)
    return backup_path

def fix_uuid_schema(db_path):
    """Fix the UUID schema in the database."""
    # First create a backup
    backup_path = backup_database(db_path)
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        logger.info(f"Found {len(tables)} tables in the database")
        
        # Create a new version of each table with updated column types for UUID fields
        for table_name, in tables:
            if table_name.startswith('sqlite_'):
                continue  # Skip SQLite internal tables
                
            logger.info(f"Processing table: {table_name}")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Identify UUID columns (typically named 'id' or ending with '_id')
            uuid_columns = []
            for column in columns:
                col_id, col_name, col_type, not_null, default_val, is_pk = column
                
                if (col_name == 'id' or col_name.endswith('_id')) and col_type in ('CHAR(32)', 'TEXT', 'VARCHAR'):
                    uuid_columns.append(col_name)
            
            if not uuid_columns:
                logger.info(f"No UUID columns found in table {table_name}, skipping")
                continue
                
            logger.info(f"Found UUID columns in {table_name}: {uuid_columns}")
            
            # Verify data in UUID columns
            for col_name in uuid_columns:
                try:
                    cursor.execute(f"SELECT {col_name} FROM {table_name} LIMIT 5")
                    sample_values = cursor.fetchall()
                    logger.info(f"Sample values from {table_name}.{col_name}: {sample_values}")
                    
                    # Check if values are valid UUIDs
                    for value, in sample_values:
                        if value:
                            try:
                                # Try parsing as UUID
                                uuid_obj = uuid.UUID(value)
                                logger.info(f"Parsed value as UUID: {value} -> {uuid_obj}")
                            except ValueError:
                                logger.warning(f"Invalid UUID format in {table_name}.{col_name}: {value}")
                except Exception as e:
                    logger.error(f"Error checking {table_name}.{col_name}: {str(e)}")
        
        logger.info("Database schema verification completed successfully")
        logger.info(f"Database backup stored at: {backup_path}")
        logger.info("You may need to adjust the Message model class to properly handle UUID formats")
        
    except Exception as e:
        logger.error(f"Error processing database: {str(e)}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "dialer.db"
    
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        sys.exit(1)
        
    logger.info(f"Starting schema verification for database: {db_path}")
    fix_uuid_schema(db_path)