"""
Tests for the OutreachService class.
"""
import pytest
import uuid
from unittest.mock import Mock, patch, AsyncMock
from sqlmodel import Session
from datetime import datetime

from app.services.outreach_service import OutreachService
from app.publisher import QueuePublisher
from app.models import Contact, PhoneNumber, OutreachCampaign


class TestOutreachService:
    """Test suite for OutreachService."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_queue_publisher(self):
        """Create a mock queue publisher."""
        return Mock(spec=QueuePublisher)
    
    @pytest.fixture
    def outreach_service(self, mock_session, mock_queue_publisher):
        """Create an OutreachService instance with mock dependencies."""
        return OutreachService(mock_session, mock_queue_publisher)
    
    @pytest.fixture
    def sample_contact(self):
        """Create a sample contact for testing."""
        contact = Contact(
            id=uuid.uuid4(),
            name="Test Contact",
            email="test@example.com"
        )
        # Add phone numbers to the contact for testing
        contact.phone_numbers = [
            PhoneNumber(number="+1234567890", priority=1)
        ]
        return contact
    
    @pytest.fixture
    def sample_phone_numbers(self):
        """Create sample phone numbers for testing."""
        return [
            PhoneNumber(id=uuid.uuid4(), contact_id=uuid.uuid4(), number="+1234567890", priority=1),
            PhoneNumber(id=uuid.uuid4(), contact_id=uuid.uuid4(), number="+0987654321", priority=2)
        ]
    
    def test_init(self, mock_session, mock_queue_publisher):
        """Test OutreachService initialization."""
        service = OutreachService(mock_session, mock_queue_publisher)
        assert service.session == mock_session
        assert service.contact_repo is not None
        assert service.group_repo is not None
        assert service.message_repo is not None
        assert service.outreach_repo is not None
        assert service.queue_publisher == mock_queue_publisher
    
    async def test_initiate_outreach_with_contact_ids_tts(self, outreach_service, sample_contact):
        """Test successful outreach initiation with contact IDs using TTS mode."""
        # Setup mocks
        contact_id = uuid.uuid4()
        message_id = uuid.uuid4()
        
        outreach_service.contact_repo.get_contacts_by_ids = Mock(return_value=[sample_contact])
        outreach_service.message_repo.get_message_by_id = Mock(return_value=Mock())
        outreach_service.contact_repo.get_contact_phone_numbers = Mock(return_value=[
            PhoneNumber(number="+1234567890", priority=1)
        ])
        
        mock_campaign = OutreachCampaign(
            id=uuid.uuid4(),
            name="Test Campaign",
            description="Test Description",
            message_id=message_id,
            target_group_id=None,
            target_contact_count=1,
            queued_contact_count=0,
            status="pending",
            initiated_by_user_id=None,
            created_at=datetime.now()
        )
        outreach_service.outreach_repo.create_campaign = Mock(return_value=mock_campaign)
        
        # Test the method
        result = await outreach_service.initiate_outreach(
            message_id=message_id,
            contact_ids=[contact_id],
            campaign_name="Test Campaign",
            description="Test Description",
            call_mode="tts"
        )
        
        # Assertions
        assert isinstance(result, OutreachCampaign)
        assert result.id == mock_campaign.id
        assert result.name == "Test Campaign"
        outreach_service.contact_repo.get_contacts_by_ids.assert_called_once()
        outreach_service.outreach_repo.create_campaign.assert_called_once()
    
    async def test_initiate_outreach_with_group_id_tts(self, outreach_service, sample_contact):
        """Test successful outreach initiation with group ID using TTS mode."""
        # Setup mocks
        group_id = uuid.uuid4()
        message_id = uuid.uuid4()
        
        outreach_service.group_repo.get_contacts_by_group_id = Mock(return_value=[sample_contact])
        outreach_service.message_repo.get_message_by_id = Mock(return_value=Mock())
        outreach_service.contact_repo.get_contact_phone_numbers = Mock(return_value=[
            PhoneNumber(number="+1234567890", priority=1)
        ])
        
        mock_campaign = OutreachCampaign(
            id=uuid.uuid4(),
            name="Test Campaign",
            description="Test Description",
            message_id=message_id,
            target_group_id=group_id,
            target_contact_count=1,
            queued_contact_count=0,
            status="pending",
            initiated_by_user_id=None,
            created_at=datetime.now()
        )
        outreach_service.outreach_repo.create_campaign = Mock(return_value=mock_campaign)
        
        # Test the method
        result = await outreach_service.initiate_outreach(
            message_id=message_id,
            group_id=group_id,
            campaign_name="Test Campaign",
            description="Test Description",
            call_mode="tts"
        )
        
        # Assertions
        assert isinstance(result, OutreachCampaign)
        assert result.id == mock_campaign.id
        outreach_service.group_repo.get_contacts_by_group_id.assert_called_once()
        outreach_service.outreach_repo.create_campaign.assert_called_once()
    
    async def test_initiate_outreach_with_contact_ids_realtime_ai(self, outreach_service, sample_contact):
        """Test successful outreach initiation with contact IDs using realtime AI mode."""
        # Setup mocks
        contact_id = uuid.uuid4()
        
        outreach_service.contact_repo.get_contacts_by_ids = Mock(return_value=[sample_contact])
        outreach_service.contact_repo.get_contact_phone_numbers = Mock(return_value=[
            PhoneNumber(number="+1234567890", priority=1)
        ])
        
        mock_campaign = OutreachCampaign(
            id=uuid.uuid4(),
            name="Test Campaign",
            description="Test Description",
            message_id=None,
            target_group_id=None,
            target_contact_count=1,
            queued_contact_count=0,
            status="pending",
            initiated_by_user_id=None,
            created_at=datetime.now()
        )
        outreach_service.outreach_repo.create_campaign = Mock(return_value=mock_campaign)
        
        # Test the method
        result = await outreach_service.initiate_outreach(
            contact_ids=[contact_id],
            campaign_name="Test Campaign",
            description="Test Description",
            call_mode="realtime_ai"
        )
        
        # Assertions
        assert isinstance(result, OutreachCampaign)
        assert result.id == mock_campaign.id
        outreach_service.contact_repo.get_contacts_by_ids.assert_called_once()
        outreach_service.outreach_repo.create_campaign.assert_called_once()
    
    async def test_initiate_outreach_validation_error(self, outreach_service):
        """Test outreach initiation with validation error."""
        # Test without required parameters
        with pytest.raises(ValueError, match="Either group_id or contact_ids must be provided"):
            await outreach_service.initiate_outreach(
                message_id=uuid.uuid4(),
                campaign_name="Test Campaign",
                call_mode="tts"
            )
    
    async def test_initiate_outreach_message_validation_error(self, outreach_service):
        """Test outreach initiation with message validation error."""
        # Test with TTS mode but no message_id
        with pytest.raises(ValueError, match="message_id is required unless call_mode is realtime_ai"):
            await outreach_service.initiate_outreach(
                contact_ids=[uuid.uuid4()],
                campaign_name="Test Campaign",
                call_mode="tts"
            )
