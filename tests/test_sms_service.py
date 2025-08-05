"""
Tests for the SmsService class.
"""
import pytest
import uuid
from unittest.mock import Mock, patch
from sqlmodel import Session
from twilio.base.exceptions import TwilioRestException

from app.services.sms_service import SmsService
from app.models import Message, Contact, PhoneNumber, SmsLog
from tests.fixtures.twilio_mocks import MockTwilioClient, failing_twilio_client


class TestSmsService:
    """Test suite for SmsService."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_twilio_client(self):
        """Create a mock Twilio client."""
        return MockTwilioClient()
    
    @pytest.fixture
    def sms_service(self, mock_session, mock_twilio_client):
        """Create an SmsService instance with mock dependencies."""
        service = SmsService(mock_session)
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
        """Test SmsService initialization."""
        service = SmsService(mock_session)
        assert service.session == mock_session
        assert service.repository is not None
        assert service.twilio_client is not None
    
    def test_send_sms_success(self, sms_service):
        """Test successful SMS sending."""
        # Setup mock
        mock_message = Mock()
        mock_message.sid = "SM1234567890"
        sms_service.twilio_client.messages.create.return_value = mock_message
        
        # Test the method
        result = sms_service.send_sms("+1234567890", "Test message")
        
        # Assertions
        assert result == "SM1234567890"
        sms_service.twilio_client.messages.create.assert_called_once()
    
    def test_send_sms_failure(self, sms_service):
        """Test SMS sending failure."""
        # Setup mock to raise exception
        sms_service.twilio_client.messages.create.side_effect = TwilioRestException(
            status=500, 
            uri="test", 
            msg="Test error"
        )
        
        # Test the method
        with pytest.raises(TwilioRestException):
            sms_service.send_sms("+1234567890", "Test message")
        
        # Assertions
        sms_service.twilio_client.messages.create.assert_called_once()
    
    async def test_send_message_to_contacts_success(self, sms_service, sample_contact, sample_phone_numbers):
        """Test successful SMS sending to contacts."""
        # Setup mocks
        mock_message = Mock(spec=Message)
        mock_message.name = "Test Message"
        mock_message.message_type = "sms"
        sms_service.repository.get_message_by_id = Mock(return_value=mock_message)
        sms_service.repository.get_contacts_by_ids = Mock(return_value=[sample_contact])
        sms_service.repository.get_contact_phone_numbers = Mock(return_value=sample_phone_numbers)
        sms_service.send_sms = Mock(return_value="SM1234567890")
        sms_service.repository.create_sms_log = Mock(return_value=Mock(spec=SmsLog))
    
        # Test the method
        result = await sms_service.send_message_to_contacts(
            message_id=uuid.uuid4(),
            contact_ids=[uuid.uuid4()]
        )
        
        # Assertions
        assert result["sent_count"] == 1
        assert result["failed_count"] == 0
        sms_service.send_sms.assert_called_once()
    
    async def test_send_message_to_contacts_failure(self, sms_service, sample_contact, sample_phone_numbers):
        """Test SMS sending failure to contacts."""
        # Setup mocks
        mock_message = Mock(spec=Message)
        mock_message.name = "Test Message"
        mock_message.message_type = "sms"
        sms_service.repository.get_message_by_id = Mock(return_value=mock_message)
        sms_service.repository.get_contacts_by_ids = Mock(return_value=[sample_contact])
        sms_service.repository.get_contact_phone_numbers = Mock(return_value=sample_phone_numbers)
        
        # Simulate failure in send_sms by raising TwilioRestException
        from twilio.base.exceptions import TwilioRestException
        sms_service.send_sms = Mock(side_effect=TwilioRestException(400, "Test error"))
        sms_service.repository.create_sms_log = Mock(return_value=Mock(spec=SmsLog))
    
        # Test the method
        result = await sms_service.send_message_to_contacts(
            message_id=uuid.uuid4(),
            contact_ids=[uuid.uuid4()]
        )
        
        # Assertions
        assert result["sent_count"] == 0
        assert result["failed_count"] == 1
        # send_sms should be called for each phone number (2 times in this case)
        assert sms_service.send_sms.call_count == 2
    
    async def test_send_message_to_group_success(self, sms_service, sample_contact, sample_phone_numbers):
        """Test successful SMS sending to a group."""
        # Setup mocks
        mock_message = Mock(spec=Message)
        mock_message.name = "Test Message"
        mock_message.message_type = "sms"
        sms_service.repository.get_message_by_id = Mock(return_value=mock_message)
        sms_service.repository.get_contacts_by_group_id = Mock(return_value=[sample_contact])
        sms_service.repository.get_contact_phone_numbers = Mock(return_value=sample_phone_numbers)
        sms_service.send_sms = Mock(return_value="SM1234567890")
        sms_service.repository.create_sms_log = Mock(return_value=Mock(spec=SmsLog))
    
        # Test the method
        result = await sms_service.send_message_to_contacts(
            message_id=uuid.uuid4(),
            group_id=uuid.uuid4()
        )
        
        # Assertions
        assert result["sent_count"] == 1
        assert result["failed_count"] == 0
        sms_service.send_sms.assert_called_once()
