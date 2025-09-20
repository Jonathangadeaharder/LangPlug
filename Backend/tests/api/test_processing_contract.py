"""Processing contract tests aligned with the CDD/TDD guidelines."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tests.auth_helpers import AuthTestHelper
from tests.assertion_helpers import assert_task_response, assert_validation_error_response, assert_auth_error_response


def _auth_headers(client) -> dict[str, str]:
    """Register and login using the shared helper to obtain auth headers."""
    flow = AuthTestHelper.register_and_login(client)
    return flow["headers"]


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenTranscribeCalledWithValidPath_ThenReturnsTaskIdentifier(async_http_client, client):
    """Happy path: /process/transcribe yields a task identifier for async work."""
    headers = _auth_headers(client)
    payload = {"video_path": "series/S01E01.mp4"}

    mock_settings = Mock()
    mock_settings.get_videos_path.return_value = Path("/videos")
    mock_settings.default_language = "en"

    with (
        patch("api.routes.processing.settings", mock_settings),
        patch("api.routes.processing.get_transcription_service") as get_transcription,
        patch("pathlib.Path.exists", return_value=True),
    ):
        mock_service = Mock()
        mock_service.transcribe.return_value = "task_123"
        get_transcription.return_value = mock_service

        response = await async_http_client.post(
            "/api/process/transcribe", json=payload, headers=headers
        )

    assert_task_response(response)
@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenTranscribeCalledWithoutVideoPath_ThenReturnsValidationError(async_http_client, client):
    """Invalid input: missing video_path fails FastAPI validation."""
    headers = _auth_headers(client)

    response = await async_http_client.post(
        "/api/process/transcribe", json={}, headers=headers
    )

    assert_validation_error_response(response, "video_path")




@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenChunkCalledWithInvertedTimeRange_ThenRejectsWithValidationError(async_http_client, client):
    """Boundary: start_time greater than end_time is rejected with validation error."""
    headers = _auth_headers(client)
    payload = {"video_path": "series/S01E01.mp4", "start_time": 30.0, "end_time": 10.0}

    response = await async_http_client.post("/api/process/chunk", json=payload, headers=headers)

    assert_validation_error_response(response)
@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenProcessingCalledWithoutAuth_ThenReturns401(async_http_client):
    """Invalid input: calling processing endpoints without auth returns 401."""
    response = await async_http_client.post("/api/process/transcribe",
                                      json={"video_path": "series/S01E01.mp4"})

    assert_auth_error_response(response)


