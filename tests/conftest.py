import os
import sys
from pathlib import Path
# Ensure project root is on sys.path so that 'app' package can be imported in tests
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
import pytest
from fastapi.testclient import TestClient

# Set test environment file before any imports
os.environ.setdefault('ENV_FILE', '.env.test')

from app.main import app
from app.database_package import get_session

# Import comprehensive database test fixtures
from tests.fixtures.database_test_fixtures import (
    test_db_manager,
    test_engine,
    test_session,
    populated_test_session,
    get_test_session_override
)

# Import other fixtures
from tests.fixtures.twilio_mocks import mock_twilio_client
from tests.fixtures.tts_mocks import mock_openai_client


@pytest.fixture(scope="function")
def session(test_session):
    """Create a test database session using the comprehensive database fixture."""
    return test_session


@pytest.fixture(scope="function")
def populated_session(populated_test_session):
    """Create a test database session with populated data."""
    return populated_test_session


@pytest.fixture(scope="function")
def client(test_db_manager):
    """Create a test client with overridden database session using the shared engine."""
    # Override the get_session dependency to use our test database manager
    app.dependency_overrides[get_session] = get_test_session_override(test_db_manager)
    
    client = TestClient(app)
    yield client
    
    app.dependency_overrides.clear()
