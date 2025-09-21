"""Behavior-first tests for `ChunkProcessingService`."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from api.models.processing import ProcessingStatus
from services.processing.chunk_processor import ChunkProcessingError, ChunkProcessingService


@pytest.fixture
def service() -> ChunkProcessingService:
    mock_db_session = Mock()
    return ChunkProcessingService(mock_db_session)


@pytest.fixture
def task_progress() -> dict[str, ProcessingStatus]:
    return {}


def _mock_video_path(patcher, exists: bool = True, srt_files: list[str] | None = None):
    srt_files = srt_files or []
    path_mock = patcher.start()
    video_file = Mock()
    video_file.is_absolute.return_value = False
    video_file.exists.return_value = exists
    
    # Create a proper mock for parent directory
    parent_mock = Mock()
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
    
    path_mock.return_value = video_file
    return video_file


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
    subtitle_processor.process_srt_file = AsyncMock(return_value={
        "blocking_words": [Mock(word="schwer")],
        "learning_subtitles": [],
        "statistics": {"segments_parsed": 1},
    })
    monkeypatch.setattr("services.processing.chunk_processor.get_subtitle_processor", lambda db_session: subtitle_processor)
    mock_parser = Mock(parse_file=Mock(return_value=[]), save_segments=Mock())
    monkeypatch.setattr("services.processing.chunk_processor.SRTParser", lambda *args, **kwargs: mock_parser)

    path_patch = patch("services.processing.chunk_processor.Path")
    # Also patch the _find_matching_srt_file method directly to return a valid path
    srt_patch = patch.object(service, '_find_matching_srt_file', return_value="episode.srt")
    video_file = _mock_video_path(path_patch, srt_files=["episode"])
    with path_patch, srt_patch:
        await service.process_chunk(
            task_id="task",
            task_progress=task_progress,
            video_path="episode.mp4",
            start_time=0,
            end_time=5,
            user_id=1,
            session_token="test_token"
        )

    status = task_progress["task"]
    assert status.status == "completed"
    assert status.progress == 100.0
    assert status.vocabulary[0].word == "schwer"
    subtitle_processor.process_srt_file.assert_called_once()


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenprocess_chunk_missing_srt_sets_errorCalled_ThenSucceeds(service, task_progress, monkeypatch):
    """Invalid input: when no subtitle file exists, task ends in error state."""
    monkeypatch.setattr("services.processing.chunk_processor.get_transcription_service", lambda: Mock(is_initialized=True))
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
    monkeypatch.setattr("services.processing.chunk_processor.get_subtitle_processor", lambda db_session: subtitle_processor)

    path_patch = patch("services.processing.chunk_processor.Path")
    _mock_video_path(path_patch, srt_files=[])
    with path_patch:
        # Test that missing SRT file raises ChunkProcessingError
        with pytest.raises(ChunkProcessingError, match="No SRT file found"):
            await service.process_chunk(
                task_id="test_task",
                task_progress=task_progress,
                video_path="test_video.mp4",
                start_time=0.0,
                end_time=10.0,
                user_id=1,
                session_token="test_token"
            )


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenprocess_chunk_transcription_unavailable_records_errorCalled_ThenSucceeds(service, task_progress, monkeypatch):
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
    
    path_patch = patch("services.processing.chunk_processor.Path")
    _mock_video_path(path_patch, srt_files=["episode"])
    with path_patch:
        # Test that transcription service unavailable raises ChunkProcessingError
        with pytest.raises(ChunkProcessingError, match="Transcription service"):
            await service.process_chunk(
                task_id="task",
                task_progress=task_progress,
                video_path="episode.mp4",
                start_time=0,
                end_time=5,
                user_id=1,
                session_token="test_token"
            )
