"""Async-first processing contract tests following the protective 80/20 rules."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tests.auth_helpers import AuthTestHelperAsync
from tests.assertion_helpers import assert_dict_response, assert_validation_error_response


async def _auth_headers(async_client) -> dict[str, str]:
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)
    return flow["headers"]


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenFilterSubtitlesCalled_ThenReturnsTaskMetadata(async_client):
    """Happy path: filter-subtitles returns task metadata when video exists."""
    headers = await _auth_headers(async_client)
    payload = {"video_path": "series/S01E01.mp4"}

    mock_settings = Mock()
    mock_settings.get_videos_path.return_value = Path("/videos")
    mock_settings.default_language = "en"

    with (
        patch("api.routes.processing.settings", mock_settings),
        patch("pathlib.Path.exists", return_value=True),
    ):
        response = await async_client.post(
            "/api/process/filter-subtitles", json=payload, headers=headers
        )

    assert_dict_response(response, {200, 202})


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenFilterSubtitlesWithoutVideoPath_ThenRejected(async_client):
    """Invalid input: missing video_path is rejected."""
    headers = await _auth_headers(async_client)

    response = await async_client.post(
        "/api/process/filter-subtitles", json={}, headers=headers
    )

    assert_validation_error_response(response)


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenTranslateSubtitlesCalled_ThenReturnsTask(async_client):
    """Happy path: translating subtitles yields a task id using translation factory."""
    headers = await _auth_headers(async_client)
    payload = {
        "video_path": "series/S01E01.mp4",
        "source_lang": "en",
        "target_lang": "es",
    }

    with (
        patch("services.translationservice.factory.TranslationServiceFactory.create_service") as factory,
        patch("pathlib.Path.exists", return_value=True),
    ):
        mock_service = Mock()
        mock_service.translate.return_value = "task_456"
        factory.return_value = mock_service

        response = await async_client.post(
            "/api/process/translate-subtitles", json=payload, headers=headers
        )

    assert_dict_response(response, {200, 202})


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenTranslateSubtitlesWithoutLanguages_ThenValidationError(async_client):
    """Boundary: missing target language yields validation error."""
    headers = await _auth_headers(async_client)

    response = await async_client.post(
        "/api/process/translate-subtitles",
        json={"video_path": "series/S01E01.mp4", "source_lang": "en"},
        headers=headers,
    )

    assert_validation_error_response(response)
