"""
Comprehensive TTS and OpenAI mocks for testing.

This module provides reusable TTS and OpenAI client mocks that can be used across all tests
to ensure consistent behavior and reduce test failures.
"""
import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path


class MockOpenAIResponse:
    """Mock OpenAI TTS response object."""
    
    def __init__(self, content=b"fake_audio_data"):
        self.content = content
    
    def stream_to_file(self, file_path):
        """Mock streaming audio data to file."""
        with open(file_path, 'wb') as f:
            f.write(self.content)


class MockOpenAIClient:
    """Mock OpenAI client for TTS testing."""
    
    def __init__(self):
        self.audio = Mock()
        self.speech = Mock()
        self._setup_audio_mock()
    
    def _setup_audio_mock(self):
        """Setup audio mock with realistic behavior."""
        # Mock successful TTS generation
        mock_response = MockOpenAIResponse()
        self.audio.speech.create.return_value = mock_response


class MockFailingOpenAIClient:
    """Mock OpenAI client that simulates failures."""
    
    def __init__(self):
        self.audio = Mock()
        self.speech = Mock()
        self._setup_failing_audio_mock()
    
    def _setup_failing_audio_mock(self):
        """Setup audio mock that fails."""
        # Simulate API key error
        from openai import AuthenticationError
        self.audio.speech.create.side_effect = AuthenticationError("Invalid API key")


@pytest.fixture
def mock_openai_client():
    """Fixture providing a mock OpenAI client."""
    return MockOpenAIClient()


@pytest.fixture
def failing_openai_client():
    """Fixture providing a failing OpenAI client."""
    return MockFailingOpenAIClient()


@pytest.fixture
def temp_audio_dir(tmp_path):
    """Fixture providing a temporary audio directory for tests."""
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    return audio_dir


@pytest.fixture
def mock_audio_file(temp_audio_dir):
    """Fixture providing a mock audio file."""
    audio_file = temp_audio_dir / "test_audio.mp3"
    audio_file.write_bytes(b"fake_audio_data")
    return audio_file


def create_mock_tts_settings():
    """Create mock TTS settings for testing."""
    return {
        'OPENAI_API_KEY': 'test_api_key',
        'OPENAI_TTS_MODEL': 'tts-1',
        'VOICE': 'alloy',
        'AUDIO_DIR': 'static/audio'
    }


@pytest.fixture
def mock_tts_settings():
    """Fixture providing mock TTS settings."""
    return create_mock_tts_settings()
