"""
Mock services to prevent slow initialization during tests.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_heavy_services():
    """Automatically mock heavy services to prevent slow initialization"""

    # Mock transcription services (prevents 10+ second Whisper loading)
    mock_transcription = AsyncMock()
    mock_transcription.transcribe_video.return_value = {
        "transcript": "Mock transcript",
        "language": "en",
        "confidence": 0.95,
    }

    # Mock translation services
    mock_translation = AsyncMock()
    mock_translation.translate.return_value = {
        "translated_text": "Mock translation",
        "target_language": "es",
        "confidence": 0.95,
    }

    with (
        patch("core.dependencies.get_transcription_service") as mock_get_transcription,
        patch("core.dependencies.get_translation_service") as mock_get_translation,
    ):
        # Configure mocks to return our fast services
        mock_get_transcription.return_value = mock_transcription
        mock_get_translation.return_value = mock_translation

        yield {"transcription": mock_transcription, "translation": mock_translation}


@pytest.fixture
def mock_file_operations():
    """Mock file system operations for speed"""
    mock_path = Mock()
    mock_path.exists.return_value = True
    mock_path.is_file.return_value = True
    mock_path.stat.return_value.st_size = 1024

    with patch("pathlib.Path") as mock_path_class:
        mock_path_class.return_value = mock_path
        yield mock_path


@pytest.fixture(autouse=True)
def disable_external_connections():
    """Prevent any external network connections during tests"""

    # Only patch requests module for external connections
    # Let httpx work normally for TestClient internal communications
    with patch("requests.get") as mock_requests_get, patch("requests.post") as mock_requests_post:
        # Configure mocks to return fast responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "mocked"}
        mock_response.text = "mocked response"

        mock_requests_get.return_value = mock_response
        mock_requests_post.return_value = mock_response

        yield
