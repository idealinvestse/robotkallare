import pytest
import uuid
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure the app module can be found if tests are run from the root
import sys
if str(Path.cwd()) not in sys.path:
    sys.path.insert(0, str(Path.cwd()))

from app.tts.openai import generate_audio_openai, OUTPUT_FORMATS

# Use a dedicated test audio directory relative to the test file
TEST_AUDIO_DIR = Path(__file__).parent / "_test_output/tts_audio"

@pytest.fixture(scope="session", autouse=True)
def manage_test_audio_dir():
    """Create the test audio directory before tests run and clean up after."""
    TEST_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Created test audio dir: {TEST_AUDIO_DIR}")
    yield
    print(f"Cleaning up test audio dir: {TEST_AUDIO_DIR}")
    # Basic cleanup - remove files created during tests in this dir
    for item in TEST_AUDIO_DIR.iterdir():
        if item.is_file():
            try:
                item.unlink()
                print(f"  Removed test file: {item.name}")
            except OSError as e:
                print(f"  Error removing {item.name}: {e}")
    # Optionally remove the dir itself if empty
    try:
        TEST_AUDIO_DIR.rmdir()
        print(f"Removed test audio dir: {TEST_AUDIO_DIR}")
    except OSError as e:
        print(f"Could not remove test audio dir (might not be empty): {e}")

# Mock the AUDIO_DIR constant within the tts.openai module for all tests in this file
@pytest.fixture(autouse=True)
def mock_audio_dir_constant(monkeypatch):
    monkeypatch.setattr("app.tts.openai.AUDIO_DIR", TEST_AUDIO_DIR)

@pytest.fixture
def mock_openai_client(monkeypatch):
    """Mock the OpenAI client and its audio generation method."""
    # Ensure API key is set for the duration of the test using this fixture
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-fixture")
    
    with patch("app.tts.openai.OpenAI", autospec=True) as mock_client_constructor:
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        # Simulate the response object having a .content attribute with bytes
        mock_response.content = b"fake_audio_bytes_for_test"
        mock_client_instance.audio.speech.create.return_value = mock_response
        mock_client_constructor.return_value = mock_client_instance
        yield mock_client_instance

# Test successful generation (e.g., MP3)
def test_generate_audio_openai_success_mp3(mock_openai_client):
    """Test successful MP3 audio generation."""
    text = "Hello world"
    file_id = str(uuid.uuid4())
    output_format = "mp3"
    voice = "alloy"
    
    expected_path = TEST_AUDIO_DIR / f"{file_id}.{output_format}"
    if expected_path.exists(): expected_path.unlink() # Clean slate

    actual_path = generate_audio_openai(text, output_format=output_format, file_id=file_id, voice=voice)
    
    assert actual_path == expected_path
    assert expected_path.exists()
    assert expected_path.read_bytes() == b"fake_audio_bytes_for_test"
    
    mock_openai_client.audio.speech.create.assert_called_once_with(
        model="tts-1", # Check default model if not overridden by env var
        voice=voice,
        input=text,
        format=output_format
    )

# Test successful generation for WAV format
def test_generate_audio_openai_success_wav(mock_openai_client):
    """Test successful WAV audio generation."""
    text = "Hello in WAV"
    file_id = str(uuid.uuid4())
    output_format = "wav"
    
    expected_path = TEST_AUDIO_DIR / f"{file_id}.{output_format}"
    if expected_path.exists(): expected_path.unlink()

    actual_path = generate_audio_openai(text, output_format=output_format, file_id=file_id)
    
    assert actual_path == expected_path
    assert expected_path.exists()
    assert expected_path.read_bytes() == b"fake_audio_bytes_for_test"
    
    mock_openai_client.audio.speech.create.assert_called_once_with(
        model="tts-1",
        voice="alloy", # Check default voice
        input=text,
        format=output_format
    )

# Test case where API key is missing
def test_generate_audio_openai_no_api_key(monkeypatch):
    """Test generation fails if OPENAI_API_KEY is not set."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = generate_audio_openai("test text")
    assert result is None

# Test case with empty input text
def test_generate_audio_openai_empty_text(mock_openai_client):
    """Test generation fails for empty text input."""
    result = generate_audio_openai("")
    assert result is None
    mock_openai_client.audio.speech.create.assert_not_called()

# Test case with an unsupported output format
def test_generate_audio_openai_unsupported_format(mock_openai_client):
    """Test generation fails when an unsupported output format is requested."""
    result = generate_audio_openai("test text", output_format="ogg") # ogg is typically not supported by OpenAI TTS
    assert result is None
    mock_openai_client.audio.speech.create.assert_not_called()

# Test case simulating an error from the OpenAI API call
def test_generate_audio_openai_api_error(mock_openai_client):
    """Test handling of an exception raised by the OpenAI client."""
    mock_openai_client.audio.speech.create.side_effect = Exception("Simulated API Error")
    
    result = generate_audio_openai("test text")
    assert result is None
    # Ensure the API was actually called before the exception occurred
    mock_openai_client.audio.speech.create.assert_called_once()

# Test case for generating file with default UUID
def test_generate_audio_openai_default_file_id(mock_openai_client):
    """Test generation uses a default UUID if file_id is not provided."""
    text = "Default ID test"
    output_format = "mp3"
    
    # Patch uuid.uuid4 to control the generated ID for assertion
    test_uuid = uuid.uuid4()
    with patch('app.tts.openai.uuid.uuid4', return_value=test_uuid):
        actual_path = generate_audio_openai(text, output_format=output_format)

    expected_path = TEST_AUDIO_DIR / f"{test_uuid}.{output_format}"
    assert actual_path == expected_path
    assert expected_path.exists()
    assert expected_path.read_bytes() == b"fake_audio_bytes_for_test"
    
    # Verify API call parameters (ensure default voice is used)
    mock_openai_client.audio.speech.create.assert_called_once_with(
        model="tts-1",
        voice="alloy", # Check default voice
        input=text,
        format=output_format
    )
