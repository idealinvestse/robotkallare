"""
Tests for the BurnMessageService class.
"""
import pytest
import uuid
from unittest.mock import Mock, patch, AsyncMock
from sqlmodel import Session
from datetime import datetime, timedelta

from app.services.burn_message_service import BurnMessageService
from app.models import BurnMessage, Contact, PhoneNumber


class TestBurnMessageService:
    """Test suite for BurnMessageService."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def burn_message_service(self, mock_session):
        """Create a BurnMessageService instance with a mock session."""
        return BurnMessageService(mock_session)
    
    @pytest.fixture
    def sample_contact(self):
        """Create a sample contact for testing."""
        contact = Contact(
            id=uuid.uuid4(),
            name="Test Contact",
            email="test@example.com"
        )
        # Add a sample phone number to the contact
        phone = PhoneNumber(
            id=uuid.uuid4(),
            contact_id=contact.id,
            number="+1234567890",
            priority=1
        )
        contact.phone_numbers = [phone]
        return contact
    
    @pytest.fixture
    def sample_phone_numbers(self):
        """Create sample phone numbers for testing."""
        return [
            PhoneNumber(id=uuid.uuid4(), contact_id=uuid.uuid4(), number="+1234567890", priority=1),
        ]
    
    def test_init(self, mock_session):
        """Test BurnMessageService initialization."""
        service = BurnMessageService(mock_session)
        assert service.session == mock_session
        assert service.sms_repository is not None
    
    def test_generate_token(self, burn_message_service):
        """Test token generation."""
        token1 = burn_message_service.generate_token()
        token2 = burn_message_service.generate_token()
        
        # Assertions
        assert isinstance(token1, str)
        assert isinstance(token2, str)
        assert len(token1) > 0
        assert len(token2) > 0
        assert token1 != token2  # Should generate unique tokens
    
    def test_create_burn_message_success(self, burn_message_service):
        """Test successful burn message creation."""
        # Setup mocks
        mock_burn_message = BurnMessage(
            id=uuid.uuid4(),
            token="test_token",
            content="Test content",
            expires_at=datetime.now() + timedelta(hours=24),
            viewed=False
        )
        burn_message_service.session.add = Mock()
        burn_message_service.session.commit = Mock()
        burn_message_service.session.refresh = Mock()
        
        # Test the method
        with patch.object(burn_message_service, 'generate_token', return_value="test_token"):
            result = burn_message_service.create_burn_message("Test content", 24)
        
        # Assertions
        assert isinstance(result, BurnMessage)
        assert result.token == "test_token"
        assert result.content == "Test content"
        burn_message_service.session.add.assert_called_once()
        burn_message_service.session.commit.assert_called_once()
    
    def test_get_burn_message_success(self, burn_message_service):
        """Test successful burn message retrieval."""
        # Setup mock
        mock_burn_message = BurnMessage(
            id=uuid.uuid4(),
            token="test_token",
            content="Test content",
            expires_at=datetime.now() + timedelta(hours=1),
            viewed=False
        )
        burn_message_service.session.exec = Mock()
        burn_message_service.session.exec().first = Mock(return_value=mock_burn_message)
        burn_message_service.session.add = Mock()
        burn_message_service.session.commit = Mock()
        
        # Test the method
        result = burn_message_service.get_burn_message("test_token", mark_as_viewed=True)
        
        # Assertions
        assert isinstance(result, BurnMessage)
        assert result.token == "test_token"
        assert result.viewed is True
        burn_message_service.session.exec().first.assert_called_once()
        burn_message_service.session.add.assert_called_once()
        burn_message_service.session.commit.assert_called_once()
    
    def test_get_burn_message_expired(self, burn_message_service):
        """Test retrieval of expired burn message."""
        # Setup mock for expired message
        mock_burn_message = BurnMessage(
            id=uuid.uuid4(),
            token="test_token",
            content="Test content",
            expires_at=datetime.now() - timedelta(hours=1),  # Expired
            viewed=False
        )
        burn_message_service.session.exec = Mock()
        burn_message_service.session.exec().first = Mock(return_value=mock_burn_message)
        burn_message_service.session.delete = Mock()
        burn_message_service.session.commit = Mock()
        
        # Test the method
        result = burn_message_service.get_burn_message("test_token", mark_as_viewed=True)
        
        # Assertions
        assert result is None
        burn_message_service.session.delete.assert_called_once_with(mock_burn_message)
        burn_message_service.session.commit.assert_called_once()
    
    def test_get_burn_message_not_found(self, burn_message_service):
        """Test retrieval of non-existent burn message."""
        # Setup mock for not found
        burn_message_service.session.exec = Mock()
        burn_message_service.session.exec().first = Mock(return_value=None)
        
        # Test the method
        result = burn_message_service.get_burn_message("nonexistent_token", mark_as_viewed=True)
        
        # Assertions
        assert result is None
        burn_message_service.session.exec().first.assert_called_once()
    
    async def test_send_burn_message_sms_success(self, burn_message_service, sample_contact):
        """Test successful burn message SMS sending."""
        # Setup mocks
        burn_message_service.session.exec = Mock()
        burn_message_service.session.exec().first = Mock(return_value=None)
        
        # Mock the SMS repository methods
        mock_contacts = [sample_contact]
        burn_message_service.sms_repository.get_contacts_by_ids = Mock(return_value=mock_contacts)
        
        mock_burn_message = BurnMessage(
            id=uuid.uuid4(),
            token="test_token",
            content="Burn content",
            expires_at=datetime.now() + timedelta(hours=24),
            viewed=False
        )
        with patch.object(burn_message_service, 'create_burn_message', return_value=mock_burn_message):
            # Mock the SmsService import location
            with patch('app.services.sms_service.SmsService') as mock_sms_service_class:
                mock_sms_service_instance = Mock()
                # Mock the _send_to_contact method to return True (success)
                mock_sms_service_instance._send_to_contact = AsyncMock(return_value=True)
                mock_sms_service_class.return_value = mock_sms_service_instance
                
                # Test the method
                result = await burn_message_service.send_burn_message_sms(
                    message_content="SMS with burn message link",
                    burn_content="Secret content",
                    recipients=[uuid.uuid4()]
                )
                
                # Assertions
                assert result["status"] == "success"
                assert result["sent_count"] == 1
                assert result["failed_count"] == 0
                
                # Test the method
                result = await burn_message_service.send_burn_message_sms(
                    message_content="SMS with burn message link",
                    burn_content="Secret content",
                    recipients=[uuid.uuid4()]
                )
                
                # Assertions
                assert result["status"] == "success"
                assert result["sent_count"] == 1
                assert result["failed_count"] == 0
    
    def test_clean_expired_messages(self, burn_message_service):
        """Test cleaning expired messages."""
        # Setup mocks
        expired_messages = [
            BurnMessage(id=uuid.uuid4(), token="token1", content="content1", 
                       expires_at=datetime.now() - timedelta(hours=1), viewed=False),
            BurnMessage(id=uuid.uuid4(), token="token2", content="content2", 
                       expires_at=datetime.now() - timedelta(hours=2), viewed=True)
        ]
        
        mock_exec_result = Mock()
        mock_exec_result.all = Mock(return_value=expired_messages)
        burn_message_service.session.exec = Mock(return_value=mock_exec_result)
        burn_message_service.session.delete = Mock()
        burn_message_service.session.commit = Mock()
        
        # Test the method
        deleted_count = burn_message_service.clean_expired_messages()
        
        # Assertions
        assert deleted_count == 2
        assert burn_message_service.session.delete.call_count == 2
        burn_message_service.session.commit.assert_called_once()
