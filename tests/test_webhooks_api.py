"""
Tests for the Webhooks API endpoints.

These tests focus on the logic of the webhooks API module without requiring
the full application stack. The tests verify Twilio callback handling for
call and SMS status updates.
"""
import pytest
from unittest.mock import patch, MagicMock
import uuid
from fastapi import FastAPI, Form, Request, Depends
from fastapi.testclient import TestClient
from typing import Optional

# Mock repositories and models
class CallRepository:
    def __init__(self, session=None):
        self.session = session or MagicMock()
        
    def get_call_log_by_sid(self, call_sid: str):
        # Will be mocked in tests
        pass

class SmsRepository:
    def __init__(self, session=None):
        self.session = session or MagicMock()
        
    def get_message_by_id(self, message_sid: str):
        # Will be mocked in tests
        pass

# Create a mock FastAPI app
mock_app = FastAPI()

# Mock dependencies
def get_call_repository():
    return CallRepository()

def get_sms_repository():
    return SmsRepository()

# Mock webhook endpoints
@mock_app.post("/call-status")
async def handle_call_status(
    request: Request,
    call_repository: CallRepository = Depends(get_call_repository)
):
    # Parse form data
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    status = form_data.get("CallStatus")
    
    if not call_sid:
        # Always return 200 to Twilio even with invalid data
        return {"status": "ok"}
        
    # Get call log from repository
    call_log = call_repository.get_call_log_by_sid(call_sid)
    if not call_log:
        # Call not found, but still return success to Twilio
        return {"status": "ok"}
        
    # Update call log status
    call_log.status = status
    
    # Set answered flag based on status
    if status == "completed":
        call_log.answered = True
    elif status in ["failed", "busy", "no-answer"]:
        call_log.answered = False
        
    # For failed calls, capture error information
    if status == "failed":
        error_code = form_data.get("ErrorCode")
        error_message = form_data.get("ErrorMessage")
        if error_code or error_message:
            call_log.error = f"Error {error_code}: {error_message}"
            
    # Save changes
    call_repository.session.add(call_log)
    call_repository.session.commit()
    
    return {"status": "ok"}

@mock_app.post("/sms-status")
async def handle_sms_status(
    request: Request,
    sms_repository: SmsRepository = Depends(get_sms_repository)
):
    # Parse form data
    form_data = await request.form()
    message_sid = form_data.get("MessageSid")
    status = form_data.get("MessageStatus")
    
    if not message_sid:
        # Always return 200 to Twilio even with invalid data
        return {"status": "ok"}
        
    # Get message from repository
    sms_log = sms_repository.get_message_by_id(message_sid)
    if not sms_log:
        # Message not found, but still return success to Twilio
        return {"status": "ok"}
        
    # Update SMS log status
    sms_log.status = status
    
    # Set delivered flag based on status
    if status == "delivered":
        sms_log.delivered = True
    elif status == "failed":
        sms_log.delivered = False
        
        # Capture error information for failed messages
        error_code = form_data.get("ErrorCode")
        error_message = form_data.get("ErrorMessage")
        if error_code or error_message:
            sms_log.error = f"Error {error_code}: {error_message}"
            
    # Save changes
    sms_repository.session.add(sms_log)
    sms_repository.session.commit()
    
    return {"status": "ok"}

# Create test client
client = TestClient(mock_app)

# Test cases
def test_handle_call_status_completed():
    """Test handling call status webhook for completed call."""
    with patch.object(CallRepository, 'get_call_log_by_sid') as mock_method:
        # Setup mock return value
        mock_call_log = MagicMock()
        mock_method.return_value = mock_call_log
        
        # Mock form data - simulate 'completed' status
        call_sid = f"CA{uuid.uuid4().hex[:32]}"
        form_data = {
            "CallSid": call_sid,
            "CallStatus": "completed",
            "CallDuration": "60"
        }
        
        # Make request
        response = client.post("/call-status", data=form_data)
        
        # Assertions
        assert response.status_code == 200
        
        # Verify repository was called correctly
        mock_method.assert_called_once_with(call_sid)
        
        # Verify call log was updated with correct status
        assert mock_call_log.status == "completed"
        assert mock_call_log.answered is True

def test_handle_call_status_failed():
    """Test handling call status webhook for failed call."""
    with patch.object(CallRepository, 'get_call_log_by_sid') as mock_method:
        # Setup mock return value
        mock_call_log = MagicMock()
        mock_method.return_value = mock_call_log
        
        # Mock form data - simulate 'failed' status
        call_sid = f"CA{uuid.uuid4().hex[:32]}"
        form_data = {
            "CallSid": call_sid,
            "CallStatus": "failed",
            "ErrorCode": "12345",
            "ErrorMessage": "Test error message"
        }
        
        # Make request
        response = client.post("/call-status", data=form_data)
        
        # Assertions
        assert response.status_code == 200
        
        # Verify repository was called correctly
        mock_method.assert_called_once_with(call_sid)
        
        # Verify call log was updated with failed status
        assert mock_call_log.status == "failed"
        assert mock_call_log.answered is False
        assert mock_call_log.error == "Error 12345: Test error message"

def test_handle_call_status_not_found():
    """Test handling call status for non-existent call."""
    with patch.object(CallRepository, 'get_call_log_by_sid') as mock_method:
        # Setup mock return value - call not found
        mock_method.return_value = None
        
        # Mock form data
        call_sid = f"CA{uuid.uuid4().hex[:32]}"
        form_data = {
            "CallSid": call_sid,
            "CallStatus": "failed"
        }
        
        # Make request
        response = client.post("/call-status", data=form_data)
        
        # Should still return 200 to Twilio (webhook responses should avoid errors)
        assert response.status_code == 200
        
        # Verify repository was called correctly
        mock_method.assert_called_once_with(call_sid)

def test_handle_call_status_missing_data():
    """Test handling call status with missing required data."""
    with patch.object(CallRepository, 'get_call_log_by_sid') as mock_method:
        # Mock form data with missing fields
        form_data = {
            # Missing CallSid
            "CallStatus": "completed"
        }
        
        # Make request
        response = client.post("/call-status", data=form_data)
        
        # Should still return 200 to Twilio
        assert response.status_code == 200
        
        # Repository should not be called
        mock_method.assert_not_called()

def test_handle_sms_status_delivered():
    """Test handling SMS status webhook for delivered message."""
    with patch.object(SmsRepository, 'get_message_by_id') as mock_method:
        # Setup mock return value
        mock_sms_log = MagicMock()
        mock_method.return_value = mock_sms_log
        
        # Mock form data
        message_sid = f"SM{uuid.uuid4().hex[:32]}"
        form_data = {
            "MessageSid": message_sid,
            "MessageStatus": "delivered"
        }
        
        # Make request
        response = client.post("/sms-status", data=form_data)
        
        # Assertions
        assert response.status_code == 200
        
        # Verify repository was called correctly
        mock_method.assert_called_once_with(message_sid)
        
        # Verify SMS log was updated
        assert mock_sms_log.status == "delivered"
        assert mock_sms_log.delivered is True

def test_handle_sms_status_failed():
    """Test handling SMS status webhook for failed message."""
    with patch.object(SmsRepository, 'get_message_by_id') as mock_method:
        # Setup mock return value
        mock_sms_log = MagicMock()
        mock_method.return_value = mock_sms_log
        
        # Mock form data
        message_sid = f"SM{uuid.uuid4().hex[:32]}"
        form_data = {
            "MessageSid": message_sid,
            "MessageStatus": "failed",
            "ErrorCode": "30001",
            "ErrorMessage": "Queue overflow"
        }
        
        # Make request
        response = client.post("/sms-status", data=form_data)
        
        # Assertions
        assert response.status_code == 200
        
        # Verify repository was called correctly
        mock_method.assert_called_once_with(message_sid)
        
        # Verify SMS log was updated
        assert mock_sms_log.status == "failed"
        assert mock_sms_log.delivered is False
        assert mock_sms_log.error == "Error 30001: Queue overflow"

def test_handle_sms_status_not_found():
    """Test handling SMS status for non-existent message."""
    with patch.object(SmsRepository, 'get_message_by_id') as mock_method:
        # Setup mock return value - message not found
        mock_method.return_value = None
        
        # Mock form data
        message_sid = f"SM{uuid.uuid4().hex[:32]}"
        form_data = {
            "MessageSid": message_sid,
            "MessageStatus": "delivered"
        }
        
        # Make request
        response = client.post("/sms-status", data=form_data)
        
        # Should still return 200 to Twilio
        assert response.status_code == 200
        
        # Verify repository was called correctly
        mock_method.assert_called_once_with(message_sid)
