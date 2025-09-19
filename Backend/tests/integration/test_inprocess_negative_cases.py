"""Negative-path integration checks for uploads and processing."""
from __future__ import annotations

import pytest

from tests.auth_helpers import AuthTestHelperAsync


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_processing_chunk_missing_video_returns_404(async_client):
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)

    response = await async_client.post(
        "/api/process/chunk",
        json={"video_path": "missing.mp4", "start_time": 0, "end_time": 5},
        headers=flow["headers"],
    )

    assert response.status_code in {404, 422}


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenvocabulary_mark_knownWithoutpayload_ThenReturnsError(async_client):
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)

    response = await async_client.post(
        "/api/vocabulary/mark-known",
        json={},
        headers=flow["headers"],
    )

    assert response.status_code == 422
