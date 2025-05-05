import os
import logging
import sqlite3
from sqlmodel import SQLModel, create_engine, Session
from app.config import get_settings

settings = get_settings()
engine = create_engine(settings.SQLITE_DB, echo=False)

def add_column_if_not_exists(table_name, column_name, column_type):
    """Add a column to the database if it doesn't exist"""
    try:
        db_path = settings.SQLITE_DB.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if column_name not in column_names:
            logging.info(f"Adding column {column_name} to {table_name}")
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
            conn.commit()
            logging.info(f"Added column {column_name} to {table_name}")
        
        conn.close()
    except Exception as e:
        logging.error(f"Error adding column {column_name} to {table_name}: {e}")

def create_db_and_tables() -> None:
    # Update schema if needed for existing tables
    db_path = settings.SQLITE_DB.replace("sqlite:///", "")
    if os.path.exists(db_path):
        # Add new columns to existing tables
        # CallLog table
        add_column_if_not_exists("calllog", "custom_message_log_id", "TEXT")
        add_column_if_not_exists("calllog", "scheduled_message_id", "TEXT")
        add_column_if_not_exists("calllog", "call_run_id", "TEXT")
        
        # SmsLog table
        add_column_if_not_exists("smslog", "retry_count", "INTEGER DEFAULT 0")
        add_column_if_not_exists("smslog", "retry_at", "TIMESTAMP")
        add_column_if_not_exists("smslog", "is_retry", "BOOLEAN DEFAULT 0")
        add_column_if_not_exists("smslog", "custom_message_log_id", "TEXT")
        add_column_if_not_exists("smslog", "scheduled_message_id", "TEXT")
        
        # Contact table
        add_column_if_not_exists("contact", "email", "VARCHAR")
        add_column_if_not_exists("contact", "notes", "VARCHAR")
    
    # Create all tables including new ones
    SQLModel.metadata.create_all(engine)
    
    # Verify RealtimeCall table columns - added 2025-05-04
    add_column_if_not_exists("realtimecall", "metadata", "JSON")
    add_column_if_not_exists("realtimecall", "duration_seconds", "INTEGER")

def get_session():
    with Session(engine) as session:
        yield session
