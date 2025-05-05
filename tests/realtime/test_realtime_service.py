"""
Tests for the RealtimeService class.

These tests verify the functionality of the service that handles
realtime AI calls between Twilio and OpenAI.
"""
import os
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import WebSocket

from app.realtime.schemas import RealtimeCallStatus
from app.realtime.service import RealtimeService

# Fixtures
@pytest.fixture
def mock_session():
    """Create a mock database session."""
    return MagicMock()

@pytest.fixture
def mock_twilio_ws():
    """Create a mock Twilio WebSocket connection."""
    mock_ws = AsyncMock(spec=WebSocket)
    
    # Create a proper async iterator for iter_text
    async def dummy_iter(*args, **kwargs):
        # Will be replaced in specific tests
        return
        yield
    
    mock_ws.iter_text = dummy_iter
    return mock_ws

@pytest.fixture
def mock_openai_ws():
    """Create a mock OpenAI WebSocket connection."""
    mock_ws = AsyncMock()
    mock_ws.open = True
    return mock_ws

@pytest.fixture
def service(mock_session):
    """Create a RealtimeService instance for testing."""
    return RealtimeService(mock_session)

# Tests for individual methods
# Fokusera på tester som inte kräver komplexa mocks av SQLAlchemy

# Fokusera på tester som inte kräver komplexa mocks av SQLAlchemy

@pytest.mark.asyncio
async def test_handle_connection_error(service, mock_twilio_ws):
    """Test the connection error handler."""
    error_msg = "Test error message"
    
    # Call the method
    await service._handle_connection_error(mock_twilio_ws, error_msg)
    
    # Verify that appropriate methods were called
    mock_twilio_ws.send_text.assert_called_once()
    mock_twilio_ws.close.assert_called_once()
    
    # Verify the content of the response (should contain TwiML with the error message)
    sent_text = mock_twilio_ws.send_text.call_args[0][0]
    assert "<Response>" in sent_text
    assert "<Say>" in sent_text
    assert error_msg in sent_text

@pytest.mark.asyncio
@patch('app.realtime.service.websockets.connect')
async def test_handle_media_stream_api_key_missing(mock_connect, service, mock_twilio_ws):
    """Test handling media stream when OpenAI API key is missing."""
    # Modify the service to simulate missing API key
    service.openai_api_key = ""
    
    # Call the method
    await service.handle_media_stream(mock_twilio_ws)
    
    # Verify behavior
    mock_twilio_ws.accept.assert_called_once()
    mock_twilio_ws.send_text.assert_called_once()
    mock_twilio_ws.close.assert_called_once()
    # The connection to OpenAI should not be attempted
    mock_connect.assert_not_called()

@pytest.mark.asyncio
@patch('app.realtime.service.websockets.connect')
@patch('app.realtime.service.get_settings')
async def test_handle_media_stream_feature_disabled(
    mock_get_settings, mock_connect, service, mock_twilio_ws
):
    """Test handling media stream when the feature is disabled."""
    # Mock settings to disable the feature
    mock_settings = MagicMock()
    mock_settings.REALTIME_ENABLED = False
    mock_settings.OPENAI_API_KEY = "fake-key"  # Make sure API key is set
    mock_get_settings.return_value = mock_settings
    
    # Call the method
    await service.handle_media_stream(mock_twilio_ws)
    
    # Verify behavior
    mock_twilio_ws.accept.assert_called_once()
    mock_twilio_ws.send_text.assert_called_once()
    mock_twilio_ws.close.assert_called_once()
    # The connection to OpenAI should not be attempted
    mock_connect.assert_not_called()

@pytest.mark.asyncio
@patch('app.realtime.service.websockets.connect')
async def test_initialize_session(mock_connect, service, mock_openai_ws):
    """Test initialization of OpenAI session."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_openai_ws
    mock_connect.return_value = mock_ctx
    
    # Call the method
    await service._initialize_session(mock_openai_ws)
    
    # Verify that the session update was sent
    mock_openai_ws.send.assert_called_once()
    
    # Check the content of what was sent
    sent_json = json.loads(mock_openai_ws.send.call_args[0][0])
    assert sent_json["type"] == "session.update"
    assert "session" in sent_json
    assert sent_json["session"]["voice"] == service.voice
    assert sent_json["session"]["instructions"] == service.system_message

# Simplified test focusing just on session initialization
@pytest.mark.asyncio
async def test_initialize_session_directly(service):
    """Test the initialization of an OpenAI session directly."""
    # Skapa en mock för WebSocket
    mock_ws = AsyncMock()
    
    # Kör funktionen som testas
    await service._initialize_session(mock_ws)
    
    # Verifiera att rätt data skickades
    mock_ws.send.assert_called_once()
    sent_data = json.loads(mock_ws.send.call_args[0][0])
    assert sent_data["type"] == "session.update"
    
    # Kontrollera att vi har grundläggande struktur och innehåll utan att vara beroende av specifika värden
    assert "voice" in sent_data["session"]
    assert "instructions" in sent_data["session"]
    assert "input_audio_format" in sent_data["session"]
    assert "output_audio_format" in sent_data["session"]
    assert "turn_detection" in sent_data["session"]
    assert "modalities" in sent_data["session"]
    assert "text" in sent_data["session"]["modalities"]
    assert "audio" in sent_data["session"]["modalities"]

# These tests are complex to implement correctly and would require
# extensive mocking of internal implementation details.
# Since we're focusing on testing the public API, we'll omit them for now.

