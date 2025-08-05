"""Database configuration and session management."""
# Import the database functions without triggering circular imports
import logging
from sqlmodel import Session, SQLModel
from app.database import get_session, create_db_and_tables, init_database_engine

# Handle engine import carefully to avoid circular dependencies
try:
    from app.database import engine
except ImportError:
    # If there's a circular import issue, set engine to None
    # It will be initialized properly during app startup
    engine = None

# For backward compatibility, re-export these functions
__all__ = ['get_session', 'engine', 'create_db_and_tables', 'init_database_engine']

# Get settings with fallback for testing
try:
    settings = get_settings()
    database_url = getattr(settings, 'DATABASE_URL', 'sqlite:///./gdial.db')
except Exception as e:
    logging.warning(f"Settings loading failed: {e}. Using fallback database configuration.")
    database_url = 'sqlite:///./gdial.db'

def get_session():
    """Get database session."""
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    """Create database tables from SQLModel metadata."""
    try:
        # Initialize the database engine if not already done
        init_database_engine()
        SQLModel.metadata.create_all(engine)
        logging.info("Database tables created/verified successfully")
    except Exception as e:
        logging.error(f"Failed to create database tables: {e}")
        raise
