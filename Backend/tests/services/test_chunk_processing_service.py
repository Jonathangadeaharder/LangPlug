"""Behavior-first tests for `ChunkProcessingService`."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest

from api.models.processing import ProcessingStatus
from core.language_preferences import resolve_language_runtime_settings
from services.processing.chunk_processor import ChunkProcessingError, ChunkProcessingService
from services.translationservice.interface import TranslationResult
from utils.srt_parser import SRTSegment


@pytest.fixture
def service() -> ChunkProcessingService:
    mock_db_session = Mock()
    return ChunkProcessingService(mock_db_session)


@pytest.fixture
def task_progress() -> dict[str, ProcessingStatus]:
    return {}


def _setup_mock_video_path(exists: bool = True, srt_files: list[str] | None = None):
    """Set up mock video path without starting patches - caller manages context."""
    srt_files = srt_files or []
    video_file = Mock()
    video_file.is_absolute.return_value = True  # Make it absolute to avoid Path operations
    video_file.exists.return_value = exists

    # Ensure __truediv__ is properly mocked for path operations
    video_file.__truediv__ = Mock(return_value=video_file)

    # Create a proper mock for parent directory
    parent_mock = Mock()
    # Enable path operations on parent directory
    parent_mock.__truediv__ = Mock(return_value=Mock())

    # Create mock SRT files with proper attributes
    mock_srt_files = []
    for stem in srt_files:
        mock_file = Mock()
        mock_file.stem = stem
        mock_file.name = f"{stem}.srt"
        mock_file.stat = Mock(return_value=Mock(st_size=1024))
        # Ensure the file doesn't contain "_chunk_" to pass the filter
        assert "_chunk_" not in mock_file.name
        mock_srt_files.append(mock_file)

    # Mock the glob method to return our mock files when called with "*.srt"
    def mock_glob(pattern):
        if pattern == "*.srt":
            return mock_srt_files
        return []

    parent_mock.glob = mock_glob
    video_file.parent = parent_mock
    video_file.stem = "episode"

    return video_file


@pytest.mark.skip(
    reason="TODO: Update test for refactored architecture - get_transcription_service no longer exists, use ChunkTranscriptionService"
)
@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenprocess_chunk_happy_pathCalled_ThenSucceeds(service, task_progress, monkeypatch):
    """Happy path: processing completes and records vocabulary and progress."""
    transcription = Mock(is_initialized=True)
    monkeypatch.setattr("services.processing.chunk_processor.get_transcription_service", lambda: transcription)
    # Mock the database user lookup instead of auth service
    mock_user = Mock()
    mock_user.username = "testuser"
    mock_user.id = 1

    # Create a proper AsyncMock for the database session
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=mock_user)
    service.db_session.execute = AsyncMock(return_value=mock_result)

    # Mock JWT authentication
    mock_authenticated_user = Mock()
    mock_authenticated_user.id = 1  # Match the user_id in the test call
    jwt_auth_mock = AsyncMock(return_value=mock_authenticated_user)
    monkeypatch.setattr("services.processing.chunk_processor.jwt_authentication.authenticate", jwt_auth_mock)

    # Mock the subtitle processor instead of get_user_filter_chain
    subtitle_processor = Mock()
    subtitle_processor.process_srt_file = AsyncMock(
        return_value={
            "blocking_words": [Mock(word="schwer")],
            "learning_subtitles": [],
            "statistics": {"segments_parsed": 1},
        }
    )
    monkeypatch.setattr(
        "services.processing.chunk_processor.get_subtitle_processor", lambda db_session: subtitle_processor
    )

    # Create mock SRT segments for testing
    mock_segments = [
        SRTSegment(index=1, start_time=1.0, end_time=4.0, text="Test segment", original_text="Test segment")
    ]

    # Create a Mock class that returns a mock parser instance
    mock_parser_instance = Mock()
    mock_parser_instance.parse_file = Mock(return_value=mock_segments)

    mock_parser_class = Mock()
    mock_parser_class.return_value = mock_parser_instance
    mock_parser_class.save_segments = Mock()  # For static method calls

    monkeypatch.setattr("services.processing.chunk_processor.SRTParser", mock_parser_class)

    # Set up mock video file structure
    video_file = _setup_mock_video_path(srt_files=["episode"])

    # Mock Path to return our mock video file and handle pathlib operations
    def mock_path_constructor(path_str):
        if path_str == "episode.mp4":
            return video_file
        return Mock()

    with (
        patch("services.processing.chunk_processor.Path", side_effect=mock_path_constructor),
        patch.object(service, "_find_matching_srt_file", return_value="episode.srt"),
    ):
        await service.process_chunk(
            task_id="task",
            task_progress=task_progress,
            video_path="episode.mp4",
            start_time=0,
            end_time=5,
            user_id=1,
            session_token="test_token",
        )

    status = task_progress["task"]
    assert status.status == "completed"
    assert status.progress == 100.0
    assert status.vocabulary[0].word == "schwer"
    subtitle_processor.process_srt_file.assert_called_once()


@pytest.mark.skip(reason="TODO: Update test for refactored architecture - get_transcription_service no longer exists")
@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenprocess_chunk_missing_srt_sets_errorCalled_ThenSucceeds(service, task_progress, monkeypatch):
    """Invalid input: when no subtitle file exists, task ends in error state."""
    monkeypatch.setattr(
        "services.processing.chunk_processor.get_transcription_service", lambda: Mock(is_initialized=True)
    )
    # Mock the database user lookup instead of auth service
    mock_user = Mock()
    mock_user.username = "testuser"
    mock_user.id = 1

    # Create a proper AsyncMock for the database session
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=mock_user)
    service.db_session.execute = AsyncMock(return_value=mock_result)

    # Mock the subtitle processor
    subtitle_processor = Mock()
    subtitle_processor.process_file = AsyncMock(return_value={})
    monkeypatch.setattr(
        "services.processing.chunk_processor.get_subtitle_processor", lambda db_session: subtitle_processor
    )

    # Set up mock video file structure with no SRT files
    video_file = _setup_mock_video_path(srt_files=[])

    with patch("services.processing.chunk_processor.Path", return_value=video_file):
        # Test that missing SRT file raises ChunkProcessingError
        with pytest.raises(ChunkProcessingError, match="No SRT file found"):
            await service.process_chunk(
                task_id="test_task",
                task_progress=task_progress,
                video_path="test_video.mp4",
                start_time=0.0,
                end_time=10.0,
                user_id=1,
                session_token=None,
            )


@pytest.mark.skip(reason="TODO: Update test for refactored architecture - get_transcription_service no longer exists")
@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenprocess_chunk_transcription_unavailable_records_errorCalled_ThenSucceeds(
    service, task_progress, monkeypatch
):
    """Boundary: missing transcription service records an error status."""
    monkeypatch.setattr("services.processing.chunk_processor.get_transcription_service", lambda: None)
    # Mock the database user lookup
    mock_user = Mock()
    mock_user.username = "testuser"
    mock_user.id = 1

    # Create a proper AsyncMock for the database session
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=mock_user)
    service.db_session.execute = AsyncMock(return_value=mock_result)

    # Set up mock video file structure
    video_file = _setup_mock_video_path(srt_files=["episode"])

    with patch("services.processing.chunk_processor.Path", return_value=video_file):
        # Test that transcription service unavailable raises ChunkProcessingError
        with pytest.raises(ChunkProcessingError, match="Transcription service"):
            await service.process_chunk(
                task_id="task",
                task_progress=task_progress,
                video_path="episode.mp4",
                start_time=0,
                end_time=5,
                user_id=1,
                session_token=None,
            )


@pytest.mark.skip(
    reason="TODO: Update test for refactored architecture - TranslationServiceFactory not in chunk_processor"
)
@pytest.mark.anyio
@pytest.mark.timeout(30)
@patch("services.processing.chunk_processor.TranslationServiceFactory.create_service")
async def test_Whentranslation_required_ThenUsesSentenceTranslator(create_service, service):
    """Happy path: sentence translations are produced via translation service."""

    translator_calls: list[tuple[list[str], str, str]] = []

    class DummyTranslator:
        service_name = "OPUS-MT"
        is_initialized = True

        def translate_batch(self, texts, source_language, target_language):
            translator_calls.append((list(texts), source_language, target_language))
            return [
                TranslationResult(
                    original_text=text,
                    translated_text=f"{text}::{target_language}",
                    source_language=source_language,
                    target_language=target_language,
                )
                for text in texts
            ]

    create_service.return_value = DummyTranslator()

    segments = [
        SRTSegment(
            index=1, start_time=0.0, end_time=1.0, text="Hallo zusammen", original_text="Hallo zusammen", translation=""
        ),
        SRTSegment(
            index=2, start_time=1.1, end_time=2.0, text="Weiter geht's", original_text="Weiter geht's", translation=""
        ),
    ]

    active_words = [
        [Mock(text="zusammen")],
        [],
    ]

    language_preferences = {
        "native": "es",
        "target": "de",
        "runtime": resolve_language_runtime_settings("es", "de"),
    }

    translations = await service._build_translation_texts(segments, active_words, language_preferences)

    assert translations[0] == "Hallo zusammen::es"
    assert translations[1] == ""
    assert translator_calls == [(["Hallo zusammen"], "de", "es")]
