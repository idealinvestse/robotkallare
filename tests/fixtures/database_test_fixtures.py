"""
Comprehensive database test fixtures that ensure TestClient and sessions share the same engine.

This module provides a robust solution to the database table creation issue by ensuring
that both the FastAPI TestClient and test sessions use the same SQLite engine instance.
"""
import pytest
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3
from contextlib import contextmanager

# Import all models to ensure SQLModel metadata is complete
from app.models import *
from app.config.settings_models import *


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign key constraints for SQLite."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


class TestDatabaseManager:
    """Manages test database lifecycle and ensures consistent engine usage."""
    
    def __init__(self):
        self.engine = None
        self._session_count = 0
    
    def create_engine(self):
        """Create a test database engine with all tables."""
        if self.engine is None:
            self.engine = create_engine(
                "sqlite:///:memory:",
                echo=False,
                connect_args={"check_same_thread": False}
            )
            
            # Ensure all models are imported and registered
            import app.models
            import app.config.settings_models
            
            # Create all tables from SQLModel metadata
            SQLModel.metadata.create_all(self.engine)
        
        return self.engine
    
    @contextmanager
    def get_session(self):
        """Get a database session from the shared engine."""
        if self.engine is None:
            self.create_engine()
        
        with Session(self.engine) as session:
            self._session_count += 1
            try:
                yield session
            finally:
                self._session_count -= 1
    
    def reset(self):
        """Reset the database manager."""
        if self.engine:
            self.engine.dispose()
        self.engine = None
        self._session_count = 0


# Global test database manager instance
_test_db_manager = TestDatabaseManager()


@pytest.fixture(scope="function")
def test_db_manager():
    """Provide the test database manager."""
    _test_db_manager.reset()
    yield _test_db_manager
    _test_db_manager.reset()


@pytest.fixture(scope="function")
def test_engine(test_db_manager):
    """Create a test database engine with all tables created."""
    return test_db_manager.create_engine()


@pytest.fixture(scope="function")
def test_session(test_db_manager):
    """Create a test database session."""
    with test_db_manager.get_session() as session:
        yield session


@pytest.fixture(scope="function")
def populated_test_session(test_db_manager):
    """Create a test session with sample data."""
    with test_db_manager.get_session() as session:
        # Create sample user
        user = User(
            id="550e8400-e29b-41d4-a716-446655440000",
            username="testuser",
            email="test@example.com"
        )
        session.add(user)
        
        # Create sample contact
        contact = Contact(
            id="550e8400-e29b-41d4-a716-446655440001",
            name="Test Contact",
            active=True
        )
        session.add(contact)
        
        # Create sample phone number
        phone = PhoneNumber(
            id="550e8400-e29b-41d4-a716-446655440002",
            number="+1234567890",
            contact_id=contact.id,
            active=True
        )
        session.add(phone)
        
        # Create sample group
        group = ContactGroup(
            id="550e8400-e29b-41d4-a716-446655440003",
            name="Test Group",
            active=True
        )
        session.add(group)
        
        # Create sample message
        message = Message(
            id="550e8400-e29b-41d4-a716-446655440004",
            name="Test Message",
            content="Hello, this is a test message!",
            active=True
        )
        session.add(message)
        
        session.commit()
        yield session


def get_test_session_override(test_db_manager):
    """Create a session override function for FastAPI dependency injection."""
    def _get_session():
        with test_db_manager.get_session() as session:
            yield session
    return _get_session
