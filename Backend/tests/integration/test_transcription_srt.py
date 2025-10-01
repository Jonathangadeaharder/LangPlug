"""Integration test ensuring transcription endpoint handles missing service gracefully."""

from __future__ import annotations

import pytest

from tests.auth_helpers import AuthTestHelperAsync


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whentranscribe_fails_without_serviceCalled_ThenSucceeds(async_http_client):
    flow = await AuthTestHelperAsync.register_and_login_async(async_http_client)

    response = await async_http_client.post(
        "/api/process/transcribe",
        json={"video_path": "missing.mp4"},
        headers=flow["headers"],
    )

    # Missing video file should return 404 (not found)
    assert response.status_code == 404, f"Expected 404 (video not found), got {response.status_code}: {response.text}"
