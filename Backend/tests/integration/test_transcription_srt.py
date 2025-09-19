"""Integration test ensuring transcription endpoint handles missing service gracefully."""
from __future__ import annotations

import pytest

from tests.auth_helpers import AuthTestHelperAsync


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whentranscribe_fails_without_serviceCalled_ThenSucceeds(async_client):
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)

    response = await async_client.post(
        "/api/process/transcribe",
        json={"video_path": "missing.mp4"},
        headers=flow["headers"],
    )

    assert response.status_code in {404, 422}
