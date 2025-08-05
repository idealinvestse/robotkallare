"""Test fixtures for GDial backend tests."""

from .twilio_mocks import (
    mock_twilio_client,
    mock_twilio_call,
    mock_twilio_message,
    mock_twilio_exception,
    failing_twilio_client,
    MockTwilioClient,
    MockTwilioCall,
    MockTwilioMessage
)

from .tts_mocks import (
    mock_openai_client,
    failing_openai_client,
    temp_audio_dir,
    mock_audio_file,
    mock_tts_settings,
    MockOpenAIClient,
    MockFailingOpenAIClient,
    create_mock_tts_settings
)

__all__ = [
    # Twilio mocks
    'mock_twilio_client',
    'mock_twilio_call', 
    'mock_twilio_message',
    'mock_twilio_exception',
    'failing_twilio_client',
    'MockTwilioClient',
    'MockTwilioCall',
    'MockTwilioMessage',
    # TTS mocks
    'mock_openai_client',
    'failing_openai_client',
    'temp_audio_dir',
    'mock_audio_file',
    'mock_tts_settings',
    'MockOpenAIClient',
    'MockFailingOpenAIClient',
    'create_mock_tts_settings'
]
