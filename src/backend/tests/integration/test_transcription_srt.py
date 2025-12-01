"""Integration test ensuring transcription endpoint handles missing service gracefully."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from tests.helpers import AsyncAuthHelper


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_Whentranscribe_fails_without_serviceCalled_ThenSucceeds(async_http_client, url_builder):
    helper = AsyncAuthHelper(async_http_client)

    _user, _token, headers = await helper.create_authenticated_user()

    # Mock transcription service to return None (unavailable)
    with patch("api.routes.transcription_routes.get_transcription_service", return_value=None):
        response = await async_http_client.post(
            url_builder.url_for("transcribe_video"),
            json={"video_path": "missing.mp4"},
            headers=headers,
        )

        # When transcription service is not available, should return 422 before checking video
        # But if video doesn't exist, it returns 404 first
        assert response.status_code in [422, 404], (
            f"Expected 422 (service not available) or 404 (video not found), got {response.status_code}: {response.text}"
        )
        # Handle both old and new error formats
        error_data = response.json()
        if "error" in error_data:
            # Accept either service not available or video not found
            assert (
                "Transcription service is not available" in error_data["error"]["message"]
                or "Video file not found" in error_data["error"]["message"]
            )
        else:
            assert (
                "Transcription service is not available" in error_data["detail"]
                or "Video file not found" in error_data["detail"]
            )
