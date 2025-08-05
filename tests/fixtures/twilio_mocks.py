"""
Comprehensive Twilio mocks for testing.

This module provides reusable Twilio client mocks that can be used across all tests
to ensure consistent behavior and reduce test failures.
"""
import pytest
from unittest.mock import Mock, MagicMock
from twilio.base.exceptions import TwilioRestException


class MockTwilioCall:
    """Mock Twilio call object."""
    
    def __init__(self, sid="CA1234567890123456789012345678901234", status="queued"):
        self.sid = sid
        self.status = status
        self.to = "+1234567890"
        self.from_ = "+0987654321"
        self.duration = None
        self.price = None
        self.date_created = None
        self.date_updated = None


class MockTwilioMessage:
    """Mock Twilio message object."""
    
    def __init__(self, sid="SM1234567890123456789012345678901234", status="queued"):
        self.sid = sid
        self.status = status
        self.to = "+1234567890"
        self.from_ = "+0987654321"
        self.body = "Test message"
        self.price = None
        self.date_created = None
        self.date_updated = None


class MockTwilioClient:
    """Comprehensive mock Twilio client."""
    
    def __init__(self):
        self.calls = Mock()
        self.messages = Mock()
        self._setup_calls_mock()
        self._setup_messages_mock()
    
    def _setup_calls_mock(self):
        """Setup calls mock with realistic behavior."""
        # Mock successful call creation
        mock_call = MockTwilioCall()
        self.calls.create.return_value = mock_call
        
        # Mock call retrieval
        self.calls.get.return_value = mock_call
        
        # Mock call listing
        self.calls.list.return_value = [mock_call]
    
    def _setup_messages_mock(self):
        """Setup messages mock with realistic behavior."""
        # Mock successful message creation
        mock_message = MockTwilioMessage()
        self.messages.create.return_value = mock_message
        
        # Mock message retrieval
        self.messages.get.return_value = mock_message
        
        # Mock message listing
        self.messages.list.return_value = [mock_message]


@pytest.fixture
def mock_twilio_client():
    """Fixture providing a comprehensive mock Twilio client."""
    return MockTwilioClient()


@pytest.fixture
def mock_twilio_call():
    """Fixture providing a mock Twilio call object."""
    return MockTwilioCall()


@pytest.fixture
def mock_twilio_message():
    """Fixture providing a mock Twilio message object."""
    return MockTwilioMessage()


@pytest.fixture
def mock_twilio_exception():
    """Fixture providing a mock Twilio exception."""
    return TwilioRestException(
        status=400,
        uri="/test",
        msg="Test error",
        code=20001
    )


def create_failing_twilio_client():
    """Create a Twilio client mock that simulates failures."""
    client = MockTwilioClient()
    
    # Make calls fail
    client.calls.create.side_effect = TwilioRestException(
        status=400,
        uri="/calls",
        msg="Call failed",
        code=20001
    )
    
    # Make messages fail
    client.messages.create.side_effect = TwilioRestException(
        status=400,
        uri="/messages",
        msg="Message failed",
        code=20001
    )
    
    return client


@pytest.fixture
def failing_twilio_client():
    """Fixture providing a Twilio client that simulates failures."""
    return create_failing_twilio_client()
