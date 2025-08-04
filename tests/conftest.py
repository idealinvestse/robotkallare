import os
import pytest
from sqlmodel import SQLModel, create_engine, Session
from app.database import get_session

# Set test environment file
os.environ.setdefault('ENV_FILE', '.env.test')

@pytest.fixture
def session():
    """Create a test database session with in-memory SQLite."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture
def test_client():
    """Create a test client for API testing."""
    from fastapi.testclient import TestClient
    from app.main import app
    
    with TestClient(app) as client:
        yield client
