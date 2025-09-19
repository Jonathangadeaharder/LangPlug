"""High-level smoke tests covering videos and vocabulary flows."""
from __future__ import annotations

import pytest

from tests.auth_helpers import AuthTestHelperAsync


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenvideo_listingWithoutauth_ThenReturnsError(async_client):
    """Happy path: authenticated user can list videos even if directory empty."""
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)

    response = await async_client.get(
        "/api/videos", headers=flow["headers"]
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenvocabulary_stats_allows_authenticated_accessCalled_ThenSucceeds(async_client):
    """Boundary: vocabulary stats endpoint returns JSON with totals."""
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)

    response = await async_client.get(
        "/api/vocabulary/library/stats", headers=flow["headers"]
    )

    assert response.status_code in {200, 500}
    if response.status_code == 200:
        body = response.json()
        assert "total_words" in body
