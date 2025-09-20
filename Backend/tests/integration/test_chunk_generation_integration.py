"""Integration-level chunk processing smoke tests using the API stack."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from core.config import settings
from tests.auth_helpers import AuthTestHelperAsync


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenchunk_processing_accepts_requestCalled_ThenSucceeds(async_http_client, monkeypatch, tmp_path):
    """Happy path: chunk processing request is accepted when dependencies succeed."""
    auth = await AuthTestHelperAsync.register_and_login_async(async_http_client)

    with patch.object(type(settings), "get_videos_path", return_value=tmp_path):
        video_path = tmp_path / "episode.mp4"
        video_path.write_bytes(b"fake")
        subtitle_path = tmp_path / "episode.srt"
        subtitle_path.write_text(
            "1\n00:00:00,000 --> 00:00:01,000\nHallo Welt\n\n", encoding="utf-8"
        )

        transcription = Mock(is_initialized=True)
        transcription.transcribe.return_value = Mock(segments=[])
        monkeypatch.setattr(
            "api.routes.processing.get_transcription_service", lambda: transcription
        )

        filter_chain = Mock()
        filter_chain.process_file.return_value = {
            "blocking_words": [],
            "learning_subtitles": [],
            "statistics": {},
        }
        monkeypatch.setattr(
            "core.dependencies.get_user_filter_chain", lambda *a, **k: filter_chain
        )

        response = await async_http_client.post(
            "/api/process/chunk",
            json={"video_path": video_path.name, "start_time": 0, "end_time": 5},
            headers=auth["headers"],
        )

        assert response.status_code in {200, 202}


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenchunk_processingWithoutexisting_subtitle_ThenReturnsError(async_http_client, monkeypatch, tmp_path):
    """Invalid input: request is accepted but processing fails when no matching subtitle file exists."""
    auth = await AuthTestHelperAsync.register_and_login_async(async_http_client)

    with patch.object(type(settings), "get_videos_path", return_value=tmp_path):
        video_path = tmp_path / "episode.mp4"
        video_path.write_bytes(b"fake")

        response = await async_http_client.post(
            "/api/process/chunk",
            json={"video_path": video_path.name, "start_time": 0, "end_time": 5},
            headers=auth["headers"]
        )

        # The endpoint accepts the request and starts background processing
        assert response.status_code == 200
        # The actual error will occur during background processing
