"""Integration checks for vocabulary endpoints."""
from __future__ import annotations

import pytest

from tests.auth_helpers import AuthTestHelperAsync


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenmark_known_endpointCalled_ThenSucceeds(async_client):
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)

    response = await async_client.post(
        "/api/vocabulary/mark-known",
        json={"word": "sein", "known": True},
        headers=flow["headers"],
    )

    assert response.status_code == 200


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenlibrary_levelWithoutvalid_code_ThenReturnsError(async_client):
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)

    response = await async_client.get(
        "/api/vocabulary/library/Z9", headers=flow["headers"]
    )

    assert response.status_code in {400, 404, 422}
