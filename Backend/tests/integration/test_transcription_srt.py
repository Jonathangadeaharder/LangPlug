"""Integration test ensuring transcription endpoint handles missing service gracefully."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from tests.auth_helpers import AuthTestHelperAsync


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whentranscribe_fails_without_serviceCalled_ThenSucceeds(async_http_client):
    flow = await AuthTestHelperAsync.register_and_login_async(async_http_client)

    # Mock transcription service to return None (unavailable)
    with patch("api.routes.transcription_routes.get_transcription_service", return_value=None):
        response = await async_http_client.post(
            "/api/process/transcribe",
            json={"video_path": "missing.mp4"},
            headers=flow["headers"],
        )

        # When transcription service is not available, should return 422 before checking video
        assert (
            response.status_code == 422
        ), f"Expected 422 (service not available), got {response.status_code}: {response.text}"
        assert "Transcription service is not available" in response.json()["detail"]
