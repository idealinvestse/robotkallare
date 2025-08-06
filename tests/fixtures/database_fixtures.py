"""
Database fixtures for comprehensive test database setup.

This module provides robust database fixtures that ensure all models are properly
registered and tables are created consistently across all tests.
"""
import pytest
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

# Import all models to ensure they're registered with SQLModel metadata
from app.models import (
    OutboxJob, OutboxJobStatus,
    ContactGroupMembership, OutreachCampaignContactLink,
    OutreachCampaign, Contact, PhoneNumber, ContactGroup,
    Message, SmsLog, CallLog, CallRun, User
)

# Import settings models to ensure they're also registered
from app.config.settings_models import (
    SystemSetting, DtmfSetting, SmsSettings, NotificationSettings, SecuritySettings
)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign key constraints for SQLite."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@pytest.fixture(scope="function")
def test_engine():
    """Create a test database engine with in-memory SQLite."""
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,  # Set to True for SQL debugging
        connect_args={"check_same_thread": False}
    )
    return engine


@pytest.fixture(scope="function")
def test_session(test_engine):
    """Create a test database session with all tables created."""
    # Create all tables from SQLModel metadata
    SQLModel.metadata.create_all(test_engine)
    
    with Session(test_engine) as session:
        yield session
        # Cleanup happens automatically when session closes


@pytest.fixture(scope="function")
def clean_test_session(test_engine):
    """Create a clean test session that recreates tables for each test."""
    # Drop all tables first
    SQLModel.metadata.drop_all(test_engine)
    # Create all tables fresh
    SQLModel.metadata.create_all(test_engine)
    
    with Session(test_engine) as session:
        yield session


def create_test_database_with_tables():
    """Utility function to create a test database with all tables."""
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False}
    )
    
    # Ensure all models are imported and registered
    # This is critical for SQLModel metadata to be complete
    from app import models
    from app.config import settings_models
    
    # Create all tables
    SQLModel.metadata.create_all(engine)
    
    return engine


@pytest.fixture(scope="function")
def populated_test_session(test_session):
    """Create a test session with some sample data."""
    # Create sample user
    user = User(
        id="550e8400-e29b-41d4-a716-446655440000",
        username="testuser",
        email="test@example.com"
    )
    test_session.add(user)
    
    # Create sample contact
    contact = Contact(
        id="550e8400-e29b-41d4-a716-446655440001",
        name="Test Contact",
        active=True
    )
    test_session.add(contact)
    
    # Create sample phone number
    phone = PhoneNumber(
        id="550e8400-e29b-41d4-a716-446655440002",
        number="+1234567890",
        contact_id=contact.id,
        active=True
    )
    test_session.add(phone)
    
    # Create sample group
    group = ContactGroup(
        id="550e8400-e29b-41d4-a716-446655440003",
        name="Test Group",
        active=True
    )
    test_session.add(group)
    
    # Create sample message
    message = Message(
        id="550e8400-e29b-41d4-a716-446655440004",
        name="Test Message",
        content="Hello, this is a test message!",
        active=True
    )
    test_session.add(message)
    
    test_session.commit()
    yield test_session
