import os
import logging
import sqlite3
from sqlmodel import SQLModel, create_engine, Session

# Initialize with default database URL
# This will be overridden during app startup based on environment
database_url = 'sqlite:///./gdial.db'
engine = None

def init_database_engine():
    """Initialize the database engine based on environment configuration."""
    global engine, database_url
    
    # Check if we're running in a test environment first
    # Load environment variables from .env.test file if it exists
    env_file = os.environ.get('ENV_FILE', '.env')
    if env_file == '.env.test' and os.path.exists('.env.test'):
        # Load environment variables from .env.test
        from dotenv import load_dotenv
        load_dotenv('.env.test')
        database_url = os.environ.get('DATABASE_URL', 'sqlite:///:memory:')
        logging.info(f"Using test database URL from .env.test: {database_url}")
    else:
        # For non-test environments, load settings normally
        try:
            from app.config import get_settings
            settings = get_settings()
            database_url = getattr(settings, 'DATABASE_URL', 'sqlite:///./gdial.db')
        except Exception as e:
            logging.warning(f"Settings loading failed: {e}. Using fallback database configuration.")
            database_url = 'sqlite:///./gdial.db'
    
    # Handle SQLite threading issues
    if database_url.startswith('sqlite://'):
        engine = create_engine(database_url, echo=False, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(database_url, echo=False)
    return engine

def add_column_if_not_exists(table_name, column_name, column_type):
    """Add a column to the database if it doesn't exist"""
    try:
        db_path = database_url.replace("sqlite:///", "")
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
    # Initialize the database engine if not already done
    init_database_engine()
    
    # Update schema if needed for existing tables
    # For in-memory databases, always create tables
    # For file-based databases, check if file exists
    db_path = database_url.replace("sqlite:///:memory:", "").replace("sqlite:///./", "").replace("sqlite:///", "")
    if database_url.startswith("sqlite:///:memory:") or os.path.exists(db_path):
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
    


def get_session():
    # Ensure engine is initialized before use
    global engine
    if engine is None:
        engine = init_database_engine()
    with Session(engine) as session:
        yield session
