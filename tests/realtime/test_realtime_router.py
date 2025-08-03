"""
Tests for realtime router endpoints.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from sqlmodel import Session

from app.realtime.router import router


@pytest.fixture
def app():
    """Create a FastAPI app instance with the realtime router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create a TestClient for the app."""
    return TestClient(app)


@pytest.fixture
def mock_session():
    """Mock database session."""
    return MagicMock(spec=Session)


@patch('app.realtime.router.get_settings')
@patch('app.realtime.router.VoiceResponse')
def test_handle_incoming_call(mock_voice_response, mock_get_settings, client, mock_session):
    """Test the /incoming-call endpoint."""
    # Mock settings
    mock_settings = MagicMock()
    mock_settings.OPENAI_API_KEY = "test-key"
    mock_get_settings.return_value = mock_settings
    
    # Mock TwiML response
    mock_response = MagicMock()
    mock_response.__str__ = MagicMock(return_value="<Response><Say>Hello</Say></Response>")
    mock_voice_response.return_value = mock_response
    
    # Test GET request
    response = client.get("/realtime/incoming-call")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"
    
    # Test POST request
    response = client.post("/realtime/incoming-call")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"


@patch('app.realtime.router.get_settings')
def test_handle_incoming_call_with_metadata(mock_get_settings, client, mock_session):
    """Test the /incoming-call endpoint with metadata."""
    # Mock settings
    mock_settings = MagicMock()
    mock_settings.OPENAI_API_KEY = "test-key"
    mock_get_settings.return_value = mock_settings
    
    # Mock TwiML classes
    with patch('app.realtime.router.VoiceResponse') as mock_voice_response, \
         patch('app.realtime.router.Connect') as mock_connect:
        
        # Mock response objects
        mock_response = MagicMock()
        mock_response.__str__ = MagicMock(return_value="<Response><Say>Hello</Say><Connect><Stream url=\"wss://testhost/realtime/media-stream?meta=testdata\"/></Connect></Response>")
        mock_voice_response.return_value = mock_response
        
        mock_connect_instance = MagicMock()
        mock_connect.return_value = mock_connect_instance
        
        # Test with metadata
        response = client.get("/realtime/incoming-call?call_meta=testdata")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/xml"


@patch('app.realtime.router.RealtimeService')
def test_handle_media_stream(mock_realtime_service, client, mock_session):
    """Test the /media-stream WebSocket endpoint."""
    # Mock the RealtimeService
    mock_service_instance = AsyncMock()
    mock_realtime_service.return_value = mock_service_instance
    
    # Test WebSocket connection (this will fail in test client but we can verify the service was called)
    try:
        with client.websocket_connect("/realtime/media-stream"):
            pass
    except RuntimeError:
        # TestClient doesn't support WebSocket properly, but we can still verify our code was called
        pass
    
    # Verify that RealtimeService was instantiated with the session
    mock_realtime_service.assert_called_once_with(mock_session)
    
    # Verify that handle_media_stream was called
    mock_service_instance.handle_media_stream.assert_called_once()
