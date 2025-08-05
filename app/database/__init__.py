"""Database configuration and session management."""
from sqlmodel import SQLModel, create_engine, Session
from app.config import get_settings
import logging

# Get settings with fallback for testing
try:
    settings = get_settings()
    database_url = getattr(settings, 'DATABASE_URL', 'sqlite:///./gdial.db')
except Exception as e:
    logging.warning(f"Settings loading failed: {e}. Using fallback database configuration.")
    database_url = 'sqlite:///./gdial.db'

engine = create_engine(database_url, echo=False)

def get_session():
    """Get database session."""
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    """Create database tables from SQLModel metadata."""
    try:
        SQLModel.metadata.create_all(engine)
        logging.info("Database tables created/verified successfully")
    except Exception as e:
        logging.error(f"Failed to create database tables: {e}")
        raise

__all__ = ['get_session', 'engine', 'create_db_and_tables']
