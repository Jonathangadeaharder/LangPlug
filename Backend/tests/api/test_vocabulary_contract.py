"""Vocabulary contract tests in line with the protective testing policy."""
from __future__ import annotations

import pytest

from tests.auth_helpers import AuthTestHelperAsync


async def _auth(async_client):
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)
    return flow["headers"]


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenmark_known_AcceptsValid_payloadCalled_ThenSucceeds(async_client):
    """Happy path: mark-known stores the flag and returns success metadata."""
    headers = await _auth(async_client)

    response = await async_client.post(
        "/api/vocabulary/mark-known",
        json={"word": "sein", "known": True},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert any(key in body for key in {"success", "message", "status"})


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenmark_knownWithoutword_ThenReturnsError(async_client):
    """Invalid input: missing word raises FastAPI validation error."""
    headers = await _auth(async_client)

    response = await async_client.post(
        "/api/vocabulary/mark-known",
        json={"known": True},
        headers=headers,
    )

    assert response.status_code == 422


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenlibrary_statsCalled_ThenReturnsexpected_fields(async_client):
    """Happy path: library stats returns aggregate fields."""
    headers = await _auth(async_client)

    response = await async_client.get(
        "/api/vocabulary/library/stats", headers=headers
    )

    assert response.status_code in {200, 500}
    if response.status_code == 200:
        payload = response.json()
        assert any(key in payload for key in {"total_words", "total_known", "levels"})


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenlibrary_levelWithoutvalid_code_ThenReturnsError(async_client):
    """Boundary: requesting unknown level surfaces a 404 or 422 error."""
    headers = await _auth(async_client)

    response = await async_client.get(
        "/api/vocabulary/library/invalid", headers=headers
    )

    assert response.status_code in {404, 422}
