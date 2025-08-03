"""
Tests for the CallService class.
"""
import pytest
import uuid
from unittest.mock import Mock, patch, AsyncMock
from sqlmodel import Session
from twilio.base.exceptions import TwilioRestException

from app.services.call_service import CallService
from app.models import Contact, PhoneNumber, CallLog, CallRun


class TestCallService:
    """Test suite for CallService."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_twilio_client(self):
        """Create a mock Twilio client."""
        return Mock()
    
    @pytest.fixture
    def call_service(self, mock_session, mock_twilio_client):
        """Create a CallService instance with mock dependencies."""
        service = CallService(mock_session)
        service.twilio_client = mock_twilio_client
        return service
    
    @pytest.fixture
    def sample_contact(self, sample_phone_numbers):
        """Create a sample contact for testing."""
        contact = Contact(
            id=uuid.uuid4(),
            name="Test Contact",
            email="test@example.com"
        )
        # Associate phone numbers with the contact
        contact.phone_numbers = sample_phone_numbers
        return contact
    
    @pytest.fixture
    def sample_phone_numbers(self):
        """Create sample phone numbers for testing."""
        return [
            PhoneNumber(id=uuid.uuid4(), contact_id=uuid.uuid4(), number="+1234567890", priority=1),
            PhoneNumber(id=uuid.uuid4(), contact_id=uuid.uuid4(), number="+0987654321", priority=2)
        ]
    
    def test_init(self, mock_session):
        """Test CallService initialization."""
        with patch('app.services.call_service.Client') as mock_client:
            service = CallService(mock_session)
            assert service.session == mock_session
            assert service.repository is not None
            assert service.twilio_client is not None
    
    def test_make_twilio_call_success(self, call_service):
        """Test successful Twilio call creation."""
        # Setup mock
        mock_call_instance = Mock()
        mock_call_instance.sid = "CA1234567890"
        call_service.twilio_client.calls.create.return_value = mock_call_instance
        
        # Test the method
        call_sid = call_service.make_twilio_call("+1234567890", uuid.uuid4())
        
        # Assertions
        assert call_sid == "CA1234567890"
        call_service.twilio_client.calls.create.assert_called_once()
    
    def test_make_twilio_call_failure(self, call_service):
        """Test Twilio call creation failure."""
        # Setup mock to raise exception
        call_service.twilio_client.calls.create.side_effect = TwilioRestException(
            status=500, 
            uri="test", 
            msg="Test error"
        )
        
        # Test the method raises exception
        with pytest.raises(TwilioRestException):
            call_service.make_twilio_call("+1234567890", uuid.uuid4())
    
    @patch('app.services.call_service.asyncio.sleep', return_value=None)
    async def test_make_custom_call_success(self, mock_sleep, call_service, sample_contact, sample_phone_numbers):
        """Test successful custom call creation."""
        # Setup mocks
        call_service._wait_for_answer = AsyncMock(return_value=True)
        call_service.repository.get_contacts_by_ids = Mock(return_value=[sample_contact])
        call_service.repository.get_contact_phone_numbers = Mock(return_value=sample_phone_numbers)
        call_service.make_twilio_call = Mock(return_value="CA1234567890")
        call_service.repository.create_call_log = Mock(return_value=Mock(spec=CallLog))
        
        # Test the method
        result = await call_service.make_custom_call(
            contact_id=uuid.uuid4(),
            message_content="Test message"
        )
        
        # Assertions
        assert result["success"] is True
        call_service.make_twilio_call.assert_called_once()
    
    @patch('app.services.call_service.asyncio.sleep', return_value=None)
    async def test_dial_contacts_success(self, mock_sleep, call_service, sample_contact, sample_phone_numbers):
        """Test successful contact dialing."""
        # Setup mocks
        call_service.repository.get_contacts_by_ids = Mock(return_value=[sample_contact])
        call_service.repository.get_contact_phone_numbers = Mock(return_value=sample_phone_numbers)
        call_service.make_twilio_call = Mock(return_value="CA1234567890")
        call_service.repository.create_call_log = Mock(return_value=Mock(spec=CallLog))
        call_service.repository.create_call_run = Mock(return_value=Mock(spec=CallRun))
        
        # Test the method
        result = await call_service.dial_contacts(
            contacts=[uuid.uuid4()],
            message_id=uuid.uuid4()
        )
        
        # Assertions
        assert result["status"] == "success"
        assert result["total_contacts"] == 1
        call_service.make_twilio_call.assert_called_once()
    
    async def test_dial_contacts_with_group(self, call_service, sample_contact, sample_phone_numbers):
        """Test successful group dialing."""
        # Setup mocks
        call_service.repository.get_contacts_by_group_id = Mock(return_value=[sample_contact])
        call_service.repository.get_contact_phone_numbers = Mock(return_value=sample_phone_numbers)
        call_service.make_twilio_call = Mock(return_value="CA1234567890")
        call_service.repository.create_call_log = Mock(return_value=Mock(spec=CallLog))
        call_service.repository.create_call_run = Mock(return_value=Mock(spec=CallRun))
        
        # Test the method
        result = await call_service.dial_contacts(
            group_id=uuid.uuid4(),
            message_id=uuid.uuid4()
        )
        
        # Assertions
        assert result["status"] == "success"
        assert result["total_contacts"] == 1
        call_service.make_twilio_call.assert_called_once()
