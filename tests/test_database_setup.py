"""
Test to verify database setup is working correctly.
This test helps debug database table creation issues.
"""
import pytest
from sqlmodel import SQLModel, create_engine, Session, select

# Import all models to ensure metadata is complete
from app.models import *
from app.config.settings_models import *

def test_database_table_creation():
    """Test that all tables are created correctly."""
    # Create engine
    engine = create_engine("sqlite:///:memory:", echo=True)
    
    # Create all tables
    SQLModel.metadata.create_all(engine)
    
    # Test table creation
    with Session(engine) as session:
        # Test Message table
        message = Message(
            name="Test Message",
            content="Test content",
            is_template=True,
            message_type="voice"
        )
        session.add(message)
        session.commit()
        
        # Verify message was created
        result = session.exec(select(Message).where(Message.name == "Test Message")).first()
        assert result is not None
        assert result.name == "Test Message"
        
        print("SUCCESS: Database tables created and working correctly!")

def test_sqlmodel_metadata():
    """Test that SQLModel metadata contains all expected tables."""
    
    expected_tables = [
        'message', 'contact', 'phonenumber', 'contactgroup',
        'smslog', 'calllog', 'callrun', 'systemsetting'
    ]
    
    actual_tables = list(SQLModel.metadata.tables.keys())
    print(f"Registered tables: {actual_tables}")
    
    for table in expected_tables:
        assert table in actual_tables, f"Table '{table}' not found in metadata"
    
    print("SUCCESS: All expected tables are registered in SQLModel metadata!")
