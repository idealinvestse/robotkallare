"""Tests for the refactored DialerService."""
import pytest
import uuid
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.services.dialer_service import DialerService
from app.models import Contact, Message, CallRun, PhoneNumber


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.refresh = Mock()
    session.get = Mock()
    return session


@pytest.fixture
def dialer_service(mock_session):
    """Create DialerService instance with mocked dependencies."""
    return DialerService(mock_session)


@pytest.fixture
def sample_contact():
    """Sample contact for testing."""
    contact = Contact(
        id=uuid.uuid4(),
        name="Test User",
        email="test@example.com"
    )
    contact.phone_numbers = [
        PhoneNumber(
            id=uuid.uuid4(),
            number="+46701234567",
            priority=1,
            contact_id=contact.id
        )
    ]
    return contact


@pytest.fixture
def sample_message():
    """Sample message for testing."""
    return Message(
        id=uuid.uuid4(),
        name="Test Message",
        content="This is a test message",
        message_type="voice",
        is_template=True
    )


class TestDialerService:
    """Test cases for DialerService."""
    
    @pytest.mark.asyncio
    async def test_start_call_run_success(self, dialer_service, mock_session, sample_message):
        """Test successful call run creation."""
        # Arrange
        contacts = [uuid.uuid4(), uuid.uuid4()]
        call_run_name = "Test Call Run"
        
        # Mock call run creation
        mock_call_run = CallRun(
            id=uuid.uuid4(),
            name=call_run_name,
            status="in_progress",
            total_calls=len(contacts)
        )
        mock_session.refresh.side_effect = lambda obj: setattr(obj, 'id', mock_call_run.id)
        
        # Mock the worker function
        with patch('app.workers.call_worker.dial_contacts_worker') as mock_worker:
            mock_worker.return_value = AsyncMock()
            
            # Act
            result = await dialer_service.start_call_run(
                contacts=contacts,
                message=sample_message,
                name=call_run_name
            )
        
        # Assert
        assert result["status"] == "initiated"
        assert result["total_calls"] == len(contacts)
        assert result["call_run_id"] is not None
        
        mock_session.add.assert_called()
        mock_session.commit.assert_called()
        mock_worker.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_call_run_with_message_content(self, dialer_service, mock_session):
        """Test call run with message content instead of Message object."""
        # Arrange
        contacts = [uuid.uuid4()]
        message_content = Mock()
        message_content.content = "Test message content"
        
        # Mock temporary message creation
        temp_message = Message(
            id=uuid.uuid4(),
            name="Temp-Test Call Run",
            content="Test message content",
            is_template=False,
            message_type="voice"
        )
        mock_session.refresh.side_effect = lambda obj: setattr(obj, 'id', temp_message.id)
        
        with patch('app.workers.call_worker.dial_contacts_worker') as mock_worker:
            mock_worker.return_value = AsyncMock()
            
            # Act
            result = await dialer_service.start_call_run(
                contacts=contacts,
                message=message_content,
                name="Test Call Run"
            )
        
        # Assert
        assert result["status"] == "initiated"
        assert mock_session.add.call_count >= 2  # CallRun + temporary Message
    
    @pytest.mark.asyncio
    async def test_start_call_run_error_handling(self, dialer_service, mock_session):
        """Test error handling in start_call_run."""
        # Arrange
        contacts = [uuid.uuid4()]
        mock_session.commit.side_effect = Exception("Database error")
        
        # Act
        result = await dialer_service.start_call_run(
            contacts=contacts,
            message=None,
            name="Test Call Run"
        )
        
        # Assert
        assert result["status"] == "error"
        assert result["call_run_id"] is None
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_dial_contact_success(self, dialer_service, mock_session, sample_contact, sample_message):
        """Test successful contact dialing."""
        # Arrange
        contact_id = sample_contact.id
        message_id = sample_message.id
        
        # Mock repository methods
        with patch.object(dialer_service.contact_repository, 'get_contact_with_phones') as mock_get_contact:
            mock_get_contact.return_value = sample_contact
            mock_session.get.return_value = sample_message
            
            with patch('app.workers.call_worker.dial_single_contact_worker') as mock_worker:
                mock_worker.return_value = True
                
                # Act
                result = await dialer_service.dial_contact(contact_id, message_id)
        
        # Assert
        assert result is True
        mock_get_contact.assert_called_once_with(contact_id)
        mock_session.get.assert_called_once_with(Message, message_id)
        mock_worker.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_dial_contact_contact_not_found(self, dialer_service, mock_session):
        """Test dialing when contact is not found."""
        # Arrange
        contact_id = uuid.uuid4()
        message_id = uuid.uuid4()
        
        with patch.object(dialer_service.contact_repository, 'get_contact_with_phones') as mock_get_contact:
            mock_get_contact.return_value = None
            
            # Act
            result = await dialer_service.dial_contact(contact_id, message_id)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_dial_contact_message_not_found(self, dialer_service, mock_session, sample_contact):
        """Test dialing when message is not found."""
        # Arrange
        contact_id = sample_contact.id
        message_id = uuid.uuid4()
        
        with patch.object(dialer_service.contact_repository, 'get_contact_with_phones') as mock_get_contact:
            mock_get_contact.return_value = sample_contact
            mock_session.get.return_value = None
            
            # Act
            result = await dialer_service.dial_contact(contact_id, message_id)
        
        # Assert
        assert result is False
    
    def test_get_call_run_stats(self, dialer_service):
        """Test getting call run statistics."""
        # Arrange
        call_run_id = uuid.uuid4()
        expected_stats = {"total_calls": 10, "answered_calls": 8, "failed_calls": 2}
        
        with patch.object(dialer_service.call_repository, 'get_call_run_stats') as mock_get_stats:
            mock_get_stats.return_value = expected_stats
            
            # Act
            result = dialer_service.get_call_run_stats(call_run_id)
        
        # Assert
        assert result == expected_stats
        mock_get_stats.assert_called_once_with(call_run_id)
    
    def test_update_call_run_status_success(self, dialer_service, mock_session):
        """Test successful call run status update."""
        # Arrange
        call_run_id = uuid.uuid4()
        new_status = "completed"
        
        mock_call_run = CallRun(id=call_run_id, status="in_progress")
        mock_session.get.return_value = mock_call_run
        
        # Act
        result = dialer_service.update_call_run_status(call_run_id, new_status)
        
        # Assert
        assert result is True
        assert mock_call_run.status == new_status
        assert isinstance(mock_call_run.updated_at, datetime)
        mock_session.add.assert_called_once_with(mock_call_run)
        mock_session.commit.assert_called_once()
    
    def test_update_call_run_status_not_found(self, dialer_service, mock_session):
        """Test call run status update when call run not found."""
        # Arrange
        call_run_id = uuid.uuid4()
        mock_session.get.return_value = None
        
        # Act
        result = dialer_service.update_call_run_status(call_run_id, "completed")
        
        # Assert
        assert result is False
    
    def test_update_call_run_status_error(self, dialer_service, mock_session):
        """Test error handling in call run status update."""
        # Arrange
        call_run_id = uuid.uuid4()
        mock_call_run = CallRun(id=call_run_id, status="in_progress")
        mock_session.get.return_value = mock_call_run
        mock_session.commit.side_effect = Exception("Database error")
        
        # Act
        result = dialer_service.update_call_run_status(call_run_id, "completed")
        
        # Assert
        assert result is False


@pytest.mark.integration
class TestDialerServiceIntegration:
    """Integration tests for DialerService."""
    
    @pytest.mark.asyncio
    async def test_full_call_run_workflow(self, async_session_fixture):
        """Test complete call run workflow with real database."""
        # This would be an integration test with a real database
        # Implementation would depend on your test database setup
        pass
    
    @pytest.mark.asyncio
    async def test_concurrent_call_runs(self, async_session_fixture):
        """Test handling of concurrent call runs."""
        # Test concurrent access patterns
        pass
