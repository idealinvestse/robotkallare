#!/usr/bin/env python
"""
Database migration script for GDial

This script updates the database schema to match the current models,
preserving existing data where possible.
"""

import os
import sqlite3
import sys
import logging
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

# Database file
DB_FILE = "dialer.db"
BACKUP_DB = f"dialer.db.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def backup_database():
    """Create a backup of the database before making changes"""
    if os.path.exists(DB_FILE):
        logger.info(f"Creating backup of database to {BACKUP_DB}")
        shutil.copy2(DB_FILE, BACKUP_DB)
        return True
    else:
        logger.error(f"Database file {DB_FILE} not found")
        return False

def get_table_info(conn, table_name):
    """Get column information for a table"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return cursor.fetchall()

def alter_dtmf_settings_table(conn):
    """Add new columns to the dtmfsetting table"""
    logger.info("Migrating dtmfsetting table...")
    
    # Get current columns
    current_columns = [col[1] for col in get_table_info(conn, "dtmfsetting")]
    
    # New columns to add with their default values
    new_columns = {
        "repeat_message_digit": "'0'",
        "confirm_receipt_digit": "'1'",
        "request_callback_digit": "'8'",
        "transfer_to_live_agent_digit": "'9'",
        "dtmf_menu_style": "'standard'",
        "inter_digit_timeout": "3",
        "allow_message_skip": "1"
    }
    
    # Add each missing column
    for column, default in new_columns.items():
        if column not in current_columns:
            try:
                logger.info(f"Adding column {column} to dtmfsetting table")
                conn.execute(f"ALTER TABLE dtmfsetting ADD COLUMN {column} DEFAULT {default}")
            except sqlite3.Error as e:
                logger.error(f"Error adding column {column}: {e}")
    
    conn.commit()
    logger.info("dtmfsetting table migration complete")

def alter_sms_settings_table(conn):
    """Add new columns to the smssettings table"""
    logger.info("Migrating smssettings table...")
    
    # Get current columns
    current_columns = [col[1] for col in get_table_info(conn, "smssettings")]
    
    # New columns to add with their default values
    new_columns = {
        "sms_rate_limit_per_second": "10",
        "allow_opt_out": "1",
        "opt_out_keyword": "'STOP'",
        "delivery_report_timeout": "60",
        "fail_silently": "1",
        "sms_retry_strategy": "'exponential'",
        "sms_url_shortener": "0",
        "international_sms_enabled": "0"
    }
    
    # Add each missing column
    for column, default in new_columns.items():
        if column not in current_columns:
            try:
                logger.info(f"Adding column {column} to smssettings table")
                conn.execute(f"ALTER TABLE smssettings ADD COLUMN {column} DEFAULT {default}")
            except sqlite3.Error as e:
                logger.error(f"Error adding column {column}: {e}")
    
    conn.commit()
    logger.info("smssettings table migration complete")

def alter_notification_settings_table(conn):
    """Add new columns to the notificationsettings table"""
    logger.info("Migrating notificationsettings table...")
    
    # Get current columns
    current_columns = [col[1] for col in get_table_info(conn, "notificationsettings")]
    
    # New columns to add with their default values
    new_columns = {
        "alert_sound_enabled": "1",
        "webhook_url": "NULL",
        "usage_report_frequency": "'weekly'",
        "emergency_escalation_threshold": "15",
        "admin_phone_numbers": "NULL"
    }
    
    # Add each missing column
    for column, default in new_columns.items():
        if column not in current_columns:
            try:
                logger.info(f"Adding column {column} to notificationsettings table")
                if default == "NULL":
                    conn.execute(f"ALTER TABLE notificationsettings ADD COLUMN {column}")
                else:
                    conn.execute(f"ALTER TABLE notificationsettings ADD COLUMN {column} DEFAULT {default}")
            except sqlite3.Error as e:
                logger.error(f"Error adding column {column}: {e}")
    
    conn.commit()
    logger.info("notificationsettings table migration complete")

def create_security_settings_table(conn):
    """Create the securitysettings table if it doesn't exist"""
    logger.info("Creating securitysettings table...")
    
    # Check if table exists
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='securitysettings'")
    if cursor.fetchone():
        logger.info("securitysettings table already exists")
        return
    
    try:
        conn.execute("""
        CREATE TABLE securitysettings (
            id TEXT PRIMARY KEY,
            force_https INTEGER DEFAULT 1,
            sensitive_data_masking INTEGER DEFAULT 1,
            auto_logout_inactive_min INTEGER DEFAULT 30,
            max_login_attempts INTEGER DEFAULT 5,
            password_expiry_days INTEGER DEFAULT 90,
            api_rate_limit INTEGER DEFAULT 100,
            audit_log_retention_days INTEGER DEFAULT 365,
            ip_whitelist TEXT,
            allowed_origins TEXT,
            extra_settings TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Insert default record
        import uuid
        conn.execute("""
        INSERT INTO securitysettings (
            id, force_https, sensitive_data_masking, auto_logout_inactive_min,
            max_login_attempts, password_expiry_days, api_rate_limit, audit_log_retention_days,
            created_at, updated_at
        ) VALUES (?, 1, 1, 30, 5, 90, 100, 365, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (str(uuid.uuid4()),))
        
        conn.commit()
        logger.info("securitysettings table created with default settings")
    except sqlite3.Error as e:
        logger.error(f"Error creating securitysettings table: {e}")

def run_migration():
    """Run the database migration"""
    logger.info("Starting database migration...")
    
    # Backup the database
    if not backup_database():
        logger.error("Migration aborted: Could not backup the database")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_FILE)
        
        # Run migrations
        alter_dtmf_settings_table(conn)
        alter_sms_settings_table(conn)
        alter_notification_settings_table(conn)
        create_security_settings_table(conn)
        
        # Close connection
        conn.close()
        
        logger.info("Database migration completed successfully")
        return True
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    try:
        success = run_migration()
        if success:
            print("Database migration completed successfully.")
            print(f"A backup of the original database was created at {BACKUP_DB}")
            sys.exit(0)
        else:
            print("Database migration failed. See log for details.")
            print(f"You can restore from the backup at {BACKUP_DB}")
            sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        print(f"An unexpected error occurred: {e}")
        print(f"You can restore from the backup at {BACKUP_DB}")
        sys.exit(1)