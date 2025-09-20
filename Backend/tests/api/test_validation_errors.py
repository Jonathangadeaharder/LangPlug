"""Validation error contract tests following the 80/20 guideline."""
from __future__ import annotations

import pytest

from tests.auth_helpers import AuthTestHelperAsync


@pytest.mark.anyio
@pytest.mark.timeout(30)
@pytest.mark.parametrize(
    "endpoint, payload",
    [
        ("/api/vocabulary/mark-known", {}),
        ("/api/vocabulary/library/bulk-mark", {}),
        ("/api/process/translate-subtitles", {}),
        ("/api/process/filter-subtitles", {}),
    ],
)
async def test_WhenEndpointsRequireMandatoryFields_ThenValidates(async_http_client, endpoint: str, payload: dict):
    """Invalid input: missing mandatory fields results in 422 validation errors."""
    auth = await AuthTestHelperAsync.register_and_login_async(async_http_client)

    response = await async_http_client.post(endpoint, json=payload, headers=auth["headers"])

    assert response.status_code == 422
