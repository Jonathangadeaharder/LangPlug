"""Thin integration around `run_chunk_processing` to ensure orchestration works."""
from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from api.routes.processing import run_chunk_processing
from core.config import settings


class _Context:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenrun_chunk_processing_successCalled_ThenSucceeds(monkeypatch, tmp_path):
    task_progress = {}
    video_path = tmp_path / "episode.mp4"
    video_path.write_bytes(b"fake")
    subtitle_path = tmp_path / "episode.srt"
    subtitle_path.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nHallo Welt\n\n", encoding="utf-8"
    )

    with patch.object(type(settings), "get_videos_path", return_value=tmp_path):
        transcription = Mock(is_initialized=True)
        transcription.transcribe.return_value = Mock(segments=[])
        monkeypatch.setattr(
            "api.routes.processing.get_transcription_service", lambda: transcription
        )
        # Mock subtitle processor
        from unittest.mock import AsyncMock
        subtitle_processor = Mock()
        subtitle_processor.process_file = AsyncMock(return_value={"blocking_words": [], "learning_subtitles": [], "statistics": {}})
        monkeypatch.setattr(
            "core.dependencies.get_subtitle_processor",
            lambda: subtitle_processor
        )

        # Mock JWT authentication
        from unittest.mock import AsyncMock
        mock_authenticated_user = Mock()
        mock_authenticated_user.id = 1  # Match the user_id in the test call
        jwt_auth_mock = AsyncMock(return_value=mock_authenticated_user)
        monkeypatch.setattr("services.processing.chunk_processor.jwt_authentication.authenticate", jwt_auth_mock)
        
        # Mock database session and user
        from database.models import User
        
        mock_user = User(id=1, username="testuser", email="test@example.com")
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        
        mock_db_session = AsyncMock()
        mock_db_session.execute.return_value = mock_result
        
        async def mock_get_async_session():
            yield mock_db_session
            
        monkeypatch.setattr(
            "core.database.get_async_session",
            mock_get_async_session
        )

        await run_chunk_processing(
            video_path=str(video_path),
            start_time=0,
            end_time=5,
            task_id="task",
            task_progress=task_progress,
            user_id=1,
            session_token="test_token",  # Provide session token
        )

        assert task_progress["task"].status == "completed"
        
        # Ensure all async operations are completed
        await asyncio.sleep(0)


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenrun_chunk_processing_missing_subtitleCalled_ThenSucceeds(monkeypatch, tmp_path):
    task_progress = {}
    video_path = tmp_path / "episode.mp4"
    video_path.write_bytes(b"fake")

    with patch.object(type(settings), "get_videos_path", return_value=tmp_path):
        await run_chunk_processing(
            video_path=str(video_path),
            start_time=0,
            end_time=5,
            task_id="task",
            task_progress=task_progress,
            user_id=1,
        )

    assert task_progress["task"].status == "error"
    
    # Ensure all async operations are completed
    await asyncio.sleep(0)
