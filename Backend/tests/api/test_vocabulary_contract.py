"""Vocabulary contract tests in line with the protective testing policy."""

from __future__ import annotations

from uuid import uuid4

import pytest

from tests.auth_helpers import AuthTestHelperAsync


async def _auth(async_client):
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)
    return flow["headers"]


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenmark_known_AcceptsValid_payloadCalled_ThenSucceeds(async_http_client):
    """Happy path: mark-known stores the flag and returns success metadata."""
    headers = await _auth(async_http_client)
    concept_id = str(uuid4())

    response = await async_http_client.post(
        "/api/vocabulary/mark-known",
        json={"concept_id": concept_id, "known": True},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert any(key in body for key in ("success", "message", "status"))


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenmark_knownWithoutconcept_id_ThenReturnsError(async_http_client):
    """Invalid input: missing concept_id raises FastAPI validation error."""
    headers = await _auth(async_http_client)

    response = await async_http_client.post(
        "/api/vocabulary/mark-known",
        json={"known": True},
        headers=headers,
    )

    assert response.status_code == 422


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenvocabulary_statsCalled_ThenReturnsexpected_fields(async_http_client):
    """Happy path: vocabulary stats returns aggregate fields with multilingual support."""
    headers = await _auth(async_http_client)

    response = await async_http_client.get(
        "/api/vocabulary/stats", params={"target_language": "de", "translation_language": "es"}, headers=headers
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    payload = response.json()
    assert any(key in payload for key in ("total_words", "total_known", "levels", "target_language"))


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenlibrary_levelWithoutvalid_code_ThenReturnsError(async_http_client):
    """Boundary: requesting unknown level surfaces a 404 or 422 error."""
    headers = await _auth(async_http_client)

    response = await async_http_client.get(
        "/api/vocabulary/library/invalid", params={"target_language": "de"}, headers=headers
    )

    # Invalid level parameter should return 422 (validation error)
    assert (
        response.status_code == 422
    ), f"Expected 422 (validation error for invalid level), got {response.status_code}: {response.text}"


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenlanguages_endpointCalled_ThenReturnsSupported_languages(async_http_client):
    """Happy path: languages endpoint returns list of supported languages."""
    headers = await _auth(async_http_client)

    response = await async_http_client.get(
        "/api/vocabulary/languages",
        headers=headers,
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    payload = response.json()
    assert "languages" in payload
    assert isinstance(payload["languages"], list)


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenbulk_mark_WithValid_level_ThenSucceeds(async_http_client):
    """Happy path: bulk mark endpoint works with valid level and language."""
    headers = await _auth(async_http_client)

    response = await async_http_client.post(
        "/api/vocabulary/library/bulk-mark",
        json={"level": "A1", "target_language": "de", "known": True},
        headers=headers,
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    payload = response.json()
    assert any(key in payload for key in ("success", "level", "word_count"))


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenbulk_mark_WithInvalid_level_ThenReturnsError(async_http_client):
    """Invalid input: bulk mark with invalid level returns validation error."""
    headers = await _auth(async_http_client)

    response = await async_http_client.post(
        "/api/vocabulary/library/bulk-mark",
        json={"level": "Z9", "target_language": "de", "known": True},
        headers=headers,
    )

    assert response.status_code == 422


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenmark_known_WithInvalid_uuid_ThenReturnsError(async_http_client):
    """Invalid input: mark known with invalid UUID returns validation error."""
    headers = await _auth(async_http_client)

    response = await async_http_client.post(
        "/api/vocabulary/mark-known",
        json={"concept_id": "not-a-uuid", "known": True},
        headers=headers,
    )

    assert response.status_code == 422
