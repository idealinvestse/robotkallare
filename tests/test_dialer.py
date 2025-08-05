import pytest
from sqlmodel import Session
from app.dialer import DialerService, dial_contacts, make_manual_call
from app.models import CallLog, Contact, PhoneNumber
from datetime import datetime
import uuid
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_dialer_service_initialization(session: Session):
    """Test that DialerService can be initialized properly."""
    dialer_service = DialerService(session)
    assert dialer_service is not None
    assert dialer_service.session == session

@pytest.mark.asyncio
async def test_make_manual_call_with_mock(session: Session):
    """Test make_manual_call function with mocked dependencies."""
    contact_id = uuid.uuid4()
    message_id = uuid.uuid4()
    
    # Mock the call service to avoid actual Twilio calls
    with patch('app.dialer.CallService') as mock_call_service:
        mock_instance = AsyncMock()
        mock_call_service.return_value = mock_instance
        mock_instance.make_manual_call.return_value = {"status": "success", "call_sid": "test-sid"}
        
        result = await make_manual_call(contact_id, message_id)
        
        assert result is not None
        mock_instance.make_manual_call.assert_called_once_with(
            contact_id=contact_id,
            message_id=message_id,
            phone_id=None,
            call_run_id=None
        )
