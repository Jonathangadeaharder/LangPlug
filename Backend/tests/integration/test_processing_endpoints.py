"""Integration tests for processing API endpoints."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from core.config import settings
from tests.auth_helpers import AuthTestHelperAsync


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whentranscribe_endpointCalled_ThenReturnstask(async_client, monkeypatch, tmp_path):
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)

    with patch.object(type(settings), "get_videos_path", return_value=tmp_path):
        video = tmp_path / "episode.mp4"
        video.write_bytes(b"fake")
        subtitle = tmp_path / "episode.srt"
        subtitle.write_text(
            "1\n00:00:00,000 --> 00:00:01,000\nHallo\n\n", encoding="utf-8"
        )

        transcriber = Mock()
        transcriber.is_initialized = True
        transcriber.transcribe.return_value = Mock(segments=[])
        monkeypatch.setattr(
            "api.routes.processing.get_transcription_service", lambda: transcriber
        )

        response = await async_client.post(
            "/api/process/transcribe",
            json={"video_path": "episode.mp4"},
            headers=flow["headers"],
        )

        assert response.status_code in {200, 202}
        assert "task_id" in response.json()


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenprepare_episodeWithoutexisting_video_ThenReturnsError(async_client):
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)

    response = await async_client.post(
        "/api/process/prepare-episode",
        json={"video_path": "missing.mp4"},
        headers=flow["headers"],
    )

    assert response.status_code in {404, 422}
