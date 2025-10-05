"""Integration tests for processing API endpoints."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from core.config import settings
from tests.helpers import AuthTestHelperAsync


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whentranscribe_endpointCalled_ThenReturnstask(async_http_client, monkeypatch, tmp_path):
    flow = await AuthTestHelperAsync.register_and_login_async(async_http_client)

    with patch.object(type(settings), "get_videos_path", return_value=tmp_path):
        video = tmp_path / "episode.mp4"
        video.write_bytes(b"fake")
        subtitle = tmp_path / "episode.srt"
        subtitle.write_text("1\n00:00:00,000 --> 00:00:01,000\nHallo\n\n", encoding="utf-8")

        transcriber = Mock()
        transcriber.is_initialized = True
        transcriber.transcribe.return_value = Mock(segments=[])
        monkeypatch.setattr("api.routes.transcription_routes.get_transcription_service", lambda: transcriber)

        response = await async_http_client.post(
            "/api/process/transcribe",
            json={"video_path": "episode.mp4"},
            headers=flow["headers"],
        )

        # Async processing should return 200 (OK with task started)
        assert (
            response.status_code == 200
        ), f"Expected 200 (async task started), got {response.status_code}: {response.text}"
        assert "task_id" in response.json()


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenprepare_episodeWithoutexisting_video_ThenReturnsError(async_http_client):
    flow = await AuthTestHelperAsync.register_and_login_async(async_http_client)

    response = await async_http_client.post(
        "/api/process/prepare-episode",
        json={"video_path": "missing.mp4"},
        headers=flow["headers"],
    )

    # Invalid video path should return 404 (not found)
    assert response.status_code == 404, f"Expected 404 (video not found), got {response.status_code}: {response.text}"
