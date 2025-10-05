"""Behavior-first tests for `ChunkProcessingService`."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from api.models.processing import ProcessingStatus
from services.processing.chunk_processor import ChunkProcessingService


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
