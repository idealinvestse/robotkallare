"""Simple tests for DialerService to verify refactored implementation."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from sqlmodel import Session

from app.services.dialer_service import DialerService


class TestDialerServiceSimple:
    """Simple test cases for DialerService."""
    
    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def dialer_service(self, mock_session):
        """Create DialerService instance with mocked session."""
        with patch('app.services.dialer_service.TwilioCallService'):
            return DialerService(session=mock_session)
    
    def test_init(self, mock_session):
        """Test DialerService initialization."""
        with patch('app.services.dialer_service.TwilioCallService'):
            service = DialerService(session=mock_session)
            assert service.session == mock_session
            assert hasattr(service, 'twilio_service')
    
    def test_available_methods(self, dialer_service):
        """Test that expected methods are available."""
        expected_methods = [
            'start_call_run',
            'dial_contact',
            'get_call_run_stats',
            'update_call_run_status'
        ]
        
        for method in expected_methods:
            assert hasattr(dialer_service, method), f"Method {method} not found"
    
    def test_service_has_dependencies(self, dialer_service, mock_session):
        """Test that service has access to dependencies."""
        assert dialer_service.session == mock_session
        assert hasattr(dialer_service, 'twilio_service')
        assert hasattr(dialer_service, 'call_repository')
        assert hasattr(dialer_service, 'contact_repository')
    
    def test_service_methods_callable(self, dialer_service):
        """Test that service methods are callable."""
        # These should not raise AttributeError
        assert callable(getattr(dialer_service, 'start_call_run'))
        assert callable(getattr(dialer_service, 'dial_contact'))
        assert callable(getattr(dialer_service, 'get_call_run_stats'))
        assert callable(getattr(dialer_service, 'update_call_run_status'))
    
    @pytest.mark.asyncio
    async def test_async_methods_available(self, dialer_service):
        """Test that async methods are available and callable."""
        # Check if methods are async
        import asyncio
        
        # These methods should be async
        async_methods = ['start_call_run', 'dial_contact']
        
        for method_name in async_methods:
            method = getattr(dialer_service, method_name)
            assert asyncio.iscoroutinefunction(method), f"Method {method_name} should be async"
