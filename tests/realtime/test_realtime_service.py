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

@pytest.mark.asyncio
async def test_log_call_start(service, mock_session):
    """Test logging the start of a realtime call."""
    from uuid import UUID
    from app.models import RealtimeCall
    
    # Mock the database operations
    mock_realtime_call = MagicMock(spec=RealtimeCall)
    mock_realtime_call.id = UUID('12345678-1234-5678-1234-567812345678')
    mock_session.add = MagicMock()
    mock_session.commit = MagicMock()
    mock_session.refresh = MagicMock()
    
    # Create a service instance with the mock session
    service_with_mock = RealtimeService(mock_session)
    
    # Call the method
    call_sid = "CA1234567890abcdef1234567890abcdef"
    result = await service_with_mock.log_call_start(call_sid)
    
    # Verify database operations
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()
    
    # Verify the result is a UUID
    assert isinstance(result, UUID)

@pytest.mark.asyncio
async def test_log_call_start_with_metadata(service, mock_session):
    """Test logging the start of a realtime call with metadata."""
    from uuid import UUID
    from app.models import RealtimeCall
    
    # Mock the database operations
    mock_realtime_call = MagicMock(spec=RealtimeCall)
    mock_realtime_call.id = UUID('12345678-1234-5678-1234-567812345678')
    mock_session.add = MagicMock()
    mock_session.commit = MagicMock()
    mock_session.refresh = MagicMock()
    
    # Create a service instance with the mock session
    service_with_mock = RealtimeService(mock_session)
    
    # Call the method with metadata
    call_sid = "CA1234567890abcdef1234567890abcdef"
    meta_str = '{"campaign_id": "123e4567-e89b-12d3-a456-426614174000", "contact_id": "123e4567-e89b-12d3-a456-426614174001"}'
    result = await service_with_mock.log_call_start(call_sid, meta_str)
    
    # Verify database operations
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()
    
    # Verify the result is a UUID
    assert isinstance(result, UUID)

@pytest.mark.asyncio
async def test_update_call_status_success(service, mock_session):
    """Test successfully updating the status of a realtime call."""
    from app.models import RealtimeCall
    from app.realtime.schemas import RealtimeCallStatus
    from sqlmodel import select
    
    # Mock the database query result
    mock_call = MagicMock(spec=RealtimeCall)
    mock_call.status = None
    mock_call.started_at = None
    mock_session.exec.return_value.first.return_value = mock_call
    mock_session.commit = MagicMock()
    
    # Create a service instance with the mock session
    service_with_mock = RealtimeService(mock_session)
    
    # Call the method
    call_sid = "CA1234567890abcdef1234567890abcdef"
    status = RealtimeCallStatus.CONNECTED
    result = await service_with_mock.update_call_status(call_sid, status)
    
    # Verify database operations
    mock_session.exec.return_value.first.assert_called_once()
    mock_session.commit.assert_called_once()
    
    # Verify the result
    assert result is True
    assert mock_call.status == status.value

@pytest.mark.asyncio
async def test_update_call_status_not_found(service, mock_session):
    """Test updating the status of a realtime call that doesn't exist."""
    from app.realtime.schemas import RealtimeCallStatus
    from sqlmodel import select
    
    # Mock the database query result to return None
    mock_session.exec.return_value.first.return_value = None
    mock_session.commit = MagicMock()
    
    # Create a service instance with the mock session
    service_with_mock = RealtimeService(mock_session)
    
    # Call the method
    call_sid = "CA1234567890abcdef1234567890abcdef"
    status = RealtimeCallStatus.CONNECTED
    result = await service_with_mock.update_call_status(call_sid, status)
    
    # Verify database operations
    mock_session.exec.return_value.first.assert_called_once()
    mock_session.commit.assert_not_called()
    
    # Verify the result
    assert result is False

@pytest.mark.asyncio
async def test_update_call_status_completed(service, mock_session):
    """Test updating the status of a realtime call to completed."""
    from datetime import datetime, timedelta
    from app.models import RealtimeCall
    from app.realtime.schemas import RealtimeCallStatus
    from sqlmodel import select
    
    # Mock the database query result
    mock_call = MagicMock(spec=RealtimeCall)
    mock_call.status = None
    mock_call.started_at = datetime.utcnow() - timedelta(seconds=30)
    mock_session.exec.return_value.first.return_value = mock_call
    mock_session.commit = MagicMock()
    
    # Create a service instance with the mock session
    service_with_mock = RealtimeService(mock_session)
    
    # Call the method
    call_sid = "CA1234567890abcdef1234567890abcdef"
    status = RealtimeCallStatus.COMPLETED
    result = await service_with_mock.update_call_status(call_sid, status)
    
    # Verify database operations
    mock_session.exec.return_value.first.assert_called_once()
    mock_session.commit.assert_called_once()
    
    # Verify the result and that duration was calculated
    assert result is True
    assert mock_call.status == status.value
    assert mock_call.ended_at is not None
    assert mock_call.duration_seconds is not None

@pytest.mark.asyncio
async def test_send_initial_prompt_with_custom_prompt(service):
    """Test sending a custom initial prompt to OpenAI."""
    # Mock WebSocket connection
    mock_ws = AsyncMock()
    
    # Call the method with a custom prompt
    custom_prompt = "Hello, this is a custom prompt for testing."
    await service.send_initial_prompt(mock_ws, custom_prompt)
    
    # Verify that two messages were sent
    assert mock_ws.send.call_count == 2
    
    # Check the first message (conversation item creation)
    first_call_args = mock_ws.send.call_args_list[0][0][0]
    first_message = json.loads(first_call_args)
    assert first_message["type"] == "conversation.item.create"
    assert first_message["item"]["type"] == "message"
    assert first_message["item"]["role"] == "user"
    assert custom_prompt in first_call_args
    
    # Check the second message (response creation)
    second_call_args = mock_ws.send.call_args_list[1][0][0]
    second_message = json.loads(second_call_args)
    assert second_message["type"] == "response.create"

@pytest.mark.asyncio
async def test_send_initial_prompt_with_default_prompt(service):
    """Test sending the default initial prompt to OpenAI."""
    # Mock WebSocket connection
    mock_ws = AsyncMock()
    
    # Call the method without a prompt (should use default)
    await service.send_initial_prompt(mock_ws)
    
    # Verify that two messages were sent
    assert mock_ws.send.call_count == 2
    
    # Check the first message (conversation item creation)
    first_call_args = mock_ws.send.call_args_list[0][0][0]
    first_message = json.loads(first_call_args)
    assert first_message["type"] == "conversation.item.create"
    assert first_message["item"]["type"] == "message"
    assert first_message["item"]["role"] == "user"
    
    # Check the second message (response creation)
    second_call_args = mock_ws.send.call_args_list[1][0][0]
    second_message = json.loads(second_call_args)
    assert second_message["type"] == "response.create"

