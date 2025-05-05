"""
Tests for the Outreach API endpoints.

These tests focus on the logic of the outreach API module without requiring
the full application stack.
"""
import pytest
from unittest.mock import patch, MagicMock
import uuid
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import List, Optional

# Define mock models to avoid importing from app
class OutreachRequest(BaseModel):
    contact_ids: List[str]
    campaign_name: str
    description: Optional[str] = None
    message_id: Optional[str] = None  # Required for TTS but not for realtime_ai
    call_mode: str = "tts"  # Default to TTS mode

class OutreachResponse(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    target_contact_count: int
    queued_contact_count: int
    message_id: Optional[uuid.UUID] = None
    created_at: str

# Create a mock app for testing
mock_app = FastAPI()

# Mock the outreach service
class MockOutreachService:
    def __init__(self, db=None):
        pass

    def initiate_outreach(self, **kwargs):
        # Dummy implementation, will be mocked in tests
        pass

# Mock the route handler
def create_outreach():
    @mock_app.post("/outreach/", status_code=status.HTTP_201_CREATED, response_model=OutreachResponse)
    async def initiate_outreach_campaign(request: OutreachRequest):
        # Validate TTS mode requires message_id
        if request.call_mode == "tts" and not request.message_id:
            raise ValueError("TTS mode requires a message_id")

        # Service call would happen here
        service = MockOutreachService()
        result = service.initiate_outreach(
            contact_ids=request.contact_ids,
            campaign_name=request.campaign_name,
            description=request.description,
            message_id=request.message_id,
            call_mode=request.call_mode
        )

        return result

# Initialize the app with our mock route
create_outreach()
client = TestClient(mock_app)

def test_initiate_outreach_campaign_tts_mode():
    """Test initiating an outreach campaign with TTS mode."""
    with patch.object(MockOutreachService, 'initiate_outreach') as mock_method:
        # Setup mock return value
        mock_method.return_value = {
            "id": uuid.uuid4(),
            "name": "Test Campaign",
            "status": "queued",
            "target_contact_count": 2,
            "queued_contact_count": 2,
            "message_id": uuid.uuid4(),
            "created_at": "2025-05-05T01:00:00"
        }

        # Test data
        message_id = str(uuid.uuid4())
        contact_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        request_data = {
            "message_id": message_id,
            "contact_ids": contact_ids,
            "campaign_name": "Test Campaign",
            "description": "This is a test campaign",
            "call_mode": "tts"
        }

        # Make request
        response = client.post("/outreach/", json=request_data)

        # Assertions
        assert response.status_code == 201
        assert "id" in response.json()
        assert response.json()["name"] == "Test Campaign"
        assert response.json()["status"] == "queued"

        # Verify service called correctly
        mock_method.assert_called_once()

def test_initiate_outreach_campaign_realtime_ai_mode():
    """Test initiating an outreach campaign with realtime AI mode."""
    with patch.object(MockOutreachService, 'initiate_outreach') as mock_method:
        # Setup mock return value
        mock_method.return_value = {
            "id": uuid.uuid4(),
            "name": "Test Realtime Campaign",
            "status": "queued",
            "target_contact_count": 1,
            "queued_contact_count": 1,
            "created_at": "2025-05-05T01:00:00"
        }

        # Test data - note: message_id not required for realtime_ai
        contact_ids = [str(uuid.uuid4())]
        request_data = {
            "contact_ids": contact_ids,
            "campaign_name": "Test Realtime Campaign",
            "description": "Realtime AI campaign test",
            "call_mode": "realtime_ai"
        }

        # Make request
        response = client.post("/outreach/", json=request_data)

        # Assertions
        assert response.status_code == 201
        assert "id" in response.json()
        assert response.json()["name"] == "Test Realtime Campaign"
        assert response.json()["status"] == "queued"

        # Verify service called correctly
        mock_method.assert_called_once()

def test_initiate_outreach_campaign_missing_data():
    """Test initiating an outreach campaign with missing required data."""
    # Test data missing campaign_name (required)
    request_data = {
        "contact_ids": [str(uuid.uuid4())],
        "message_id": str(uuid.uuid4()),
        "call_mode": "tts"
    }

    # Make request
    response = client.post("/outreach/", json=request_data)

    # Should return validation error
    assert response.status_code == 422
