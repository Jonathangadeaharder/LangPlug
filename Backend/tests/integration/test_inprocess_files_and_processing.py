"""Integration tests for file processing workflows."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from core.config import settings
from tests.auth_helpers import AuthTestHelperAsync


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenFilterSubtitlesWithoutexisting_file_ThenRejected(async_client, monkeypatch, tmp_path):
    """Invalid input: filter-subtitles fails when subtitle file absent."""
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)

    with patch.object(type(settings), "get_videos_path", return_value=tmp_path):
        response = await async_client.post(
            "/api/process/filter-subtitles",
            json={"video_path": "missing.mp4"},
            headers=flow["headers"],
        )

        assert response.status_code == 422


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whentranslate_subtitles_happy_pathCalled_ThenSucceeds(async_client, monkeypatch, tmp_path):
    """Happy path: translate-subtitles succeeds when services are available."""
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)

    with patch.object(type(settings), "get_videos_path", return_value=tmp_path):
        subtitle = tmp_path / "episode.srt"
        subtitle.write_text("1\n00:00:00,000 --> 00:00:01,000\nHallo\n\n", encoding="utf-8")
        video = tmp_path / "episode.mp4"
        video.write_bytes(b"fake")

        translator = Mock()
        translator.is_initialized = True
        translator.translate_batch.return_value = []
        monkeypatch.setattr("api.routes.processing.get_translation_service", lambda: translator)
        monkeypatch.setattr(
            "api.routes.processing.get_transcription_service",
            lambda: Mock(is_initialized=True, transcribe=Mock(return_value=Mock(segments=[]))),
        )

        response = await async_client.post(
            "/api/process/translate-subtitles",
            json={
                "video_path": "episode.mp4",
                "source_lang": "de",
                "target_lang": "en",
            },
            headers=flow["headers"],
        )

        # Async processing should return 202 (Accepted)
        assert (
            response.status_code == 202
        ), f"Expected 202 (async accepted), got {response.status_code}: {response.text}"
