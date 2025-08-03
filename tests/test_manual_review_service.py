"""
Tests for the ManualReviewService class.
"""
import pytest
import uuid
from unittest.mock import Mock
from sqlmodel import Session

from app.services.manual_review_service import ManualReviewService
from app.models import OutboxJob


class TestManualReviewService:
    """Test suite for ManualReviewService."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def manual_review_service(self, mock_session):
        """Create a ManualReviewService instance with a mock session."""
        return ManualReviewService(mock_session)
    
    def test_init(self, mock_session):
        """Test ManualReviewService initialization."""
        service = ManualReviewService(mock_session)
        assert service.session == mock_session
        assert service.jobs is not None
        assert service.resolver is not None
    
    def test_list_failed_jobs(self, manual_review_service):
        """Test listing failed jobs."""
        # Setup mocks
        mock_job = Mock(spec=OutboxJob)
        mock_job.id = uuid.uuid4()
        mock_job.service = "sms"
        mock_job.payload = {"to": "+1234567890", "message": "Test message"}
        
        manual_review_service.jobs.fetch_failed = Mock(return_value=[mock_job])
        manual_review_service.resolver.from_payload = Mock(return_value=Mock())
        
        # Test the method
        result = manual_review_service.list_failed_jobs()
        
        # Assertions
        assert len(result) == 1
        assert result[0]["job_id"] == str(mock_job.id)
        assert result[0]["service"] == "sms"
        manual_review_service.jobs.fetch_failed.assert_called_once()
    
    def test_mark_sent_success(self, manual_review_service):
        """Test marking job as sent successfully."""
        # Setup mocks
        job_id = uuid.uuid4()
        mock_job = Mock(spec=OutboxJob)
        manual_review_service.jobs.get_by_id = Mock(return_value=mock_job)
        manual_review_service.jobs.mark_sent = Mock()
        
        # Test the method
        result = manual_review_service.mark_sent(job_id)
        
        # Assertions
        assert result is True
        manual_review_service.jobs.get_by_id.assert_called_once_with(job_id)
        manual_review_service.jobs.mark_sent.assert_called_once_with(mock_job)
    
    def test_mark_sent_not_found(self, manual_review_service):
        """Test marking non-existent job as sent."""
        # Setup mocks
        job_id = uuid.uuid4()
        manual_review_service.jobs.get_by_id = Mock(return_value=None)
        
        # Test the method
        result = manual_review_service.mark_sent(job_id)
        
        # Assertions
        assert result is False
        manual_review_service.jobs.get_by_id.assert_called_once_with(job_id)
    
    def test_mark_failed_success(self, manual_review_service):
        """Test marking job as failed successfully."""
        # Setup mocks
        job_id = uuid.uuid4()
        mock_job = Mock(spec=OutboxJob)
        manual_review_service.jobs.get_by_id = Mock(return_value=mock_job)
        manual_review_service.jobs.mark_failed = Mock()
        
        # Test the method
        result = manual_review_service.mark_failed(job_id)
        
        # Assertions
        assert result is True
        manual_review_service.jobs.get_by_id.assert_called_once_with(job_id)
        manual_review_service.jobs.mark_failed.assert_called_once_with(mock_job)
    
    def test_mark_failed_not_found(self, manual_review_service):
        """Test marking non-existent job as failed."""
        # Setup mocks
        job_id = uuid.uuid4()
        manual_review_service.jobs.get_by_id = Mock(return_value=None)
        
        # Test the method
        result = manual_review_service.mark_failed(job_id)
        
        # Assertions
        assert result is False
        manual_review_service.jobs.get_by_id.assert_called_once_with(job_id)
    
    def test_requeue_success(self, manual_review_service):
        """Test requeueing job successfully."""
        # Setup mocks
        job_id = uuid.uuid4()
        mock_job = Mock(spec=OutboxJob)
        mock_job.status = "failed"
        mock_job.attempts = 3
        manual_review_service.jobs.get_by_id = Mock(return_value=mock_job)
        manual_review_service.session.add = Mock()
        manual_review_service.session.commit = Mock()
        
        # Test the method
        result = manual_review_service.requeue(job_id)
        
        # Assertions
        assert result is True
        assert mock_job.status == "pending"
        assert mock_job.attempts == 0
        manual_review_service.jobs.get_by_id.assert_called_once_with(job_id)
        manual_review_service.session.add.assert_called_once_with(mock_job)
        manual_review_service.session.commit.assert_called_once()
    
    def test_requeue_not_found(self, manual_review_service):
        """Test requeueing non-existent job."""
        # Setup mocks
        job_id = uuid.uuid4()
        manual_review_service.jobs.get_by_id = Mock(return_value=None)
        
        # Test the method
        result = manual_review_service.requeue(job_id)
        
        # Assertions
        assert result is False
        manual_review_service.jobs.get_by_id.assert_called_once_with(job_id)
