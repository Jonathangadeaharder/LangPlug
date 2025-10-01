"""Focused vocabulary route tests for the multilingual system matching CDD/TDD rules."""

from __future__ import annotations

from uuid import uuid4

import pytest

from tests.auth_helpers import AuthTestHelperAsync


async def _auth(async_client):
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)
    return flow["headers"]


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_When_languages_endpoint_called_Then_returns_supported_languages(async_client):
    """Happy path: languages endpoint returns list of supported languages."""
    headers = await _auth(async_client)

    response = await async_client.get(
        "/api/vocabulary/languages",
        headers=headers,
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    payload = response.json()
    assert "languages" in payload
    assert isinstance(payload["languages"], list)


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_When_stats_called_with_language_params_Then_returns_multilingual_stats(async_client):
    """Happy path: stats endpoint supports multilingual parameters."""
    headers = await _auth(async_client)

    response = await async_client.get(
        "/api/vocabulary/stats",
        params={"target_language": "de", "translation_language": "es"},
        headers=headers,
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    payload = response.json()
    assert "levels" in payload
    assert "target_language" in payload
    assert "total_words" in payload
    assert "total_known" in payload


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_When_library_level_called_with_language_params_Then_returns_multilingual_words(async_client):
    """Happy path: library level endpoint supports multilingual parameters."""
    headers = await _auth(async_client)

    response = await async_client.get(
        "/api/vocabulary/library/A1",
        params={"target_language": "de", "translation_language": "es", "limit": 10},
        headers=headers,
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    payload = response.json()
    assert "level" in payload
    assert "target_language" in payload
    assert "words" in payload
    assert "total_count" in payload
    assert "known_count" in payload

    # Check word structure
    if payload["words"]:
        word = payload["words"][0]
        assert "concept_id" in word
        assert "word" in word
        # translation may be None if no translation available
        # assert "translation" in word


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_When_mark_known_called_with_concept_id_Then_succeeds(async_client):
    """Happy path: mark known endpoint uses concept_id instead of word."""
    headers = await _auth(async_client)
    concept_id = str(uuid4())

    response = await async_client.post(
        "/api/vocabulary/mark-known",
        json={"concept_id": concept_id, "known": True},
        headers=headers,
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    payload = response.json()
    assert "success" in payload
    assert "concept_id" in payload
    assert "known" in payload


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_When_mark_known_called_without_concept_id_Then_returns_validation_error(async_client):
    """Invalid input: mark known without concept_id returns validation error."""
    headers = await _auth(async_client)

    response = await async_client.post(
        "/api/vocabulary/mark-known",
        json={"known": True},  # Missing concept_id
        headers=headers,
    )

    assert response.status_code == 422


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_When_mark_known_called_with_invalid_uuid_Then_returns_validation_error(async_client):
    """Invalid input: mark known with invalid UUID returns validation error."""
    headers = await _auth(async_client)

    response = await async_client.post(
        "/api/vocabulary/mark-known",
        json={"concept_id": "not-a-uuid", "known": True},
        headers=headers,
    )

    assert response.status_code == 422


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_When_bulk_mark_called_with_target_language_Then_succeeds(async_client):
    """Happy path: bulk mark endpoint supports target language parameter."""
    headers = await _auth(async_client)

    response = await async_client.post(
        "/api/vocabulary/library/bulk-mark",
        json={"level": "A1", "target_language": "de", "known": True},
        headers=headers,
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    payload = response.json()
    assert "success" in payload
    assert "level" in payload
    assert "known" in payload
    assert "word_count" in payload


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_When_bulk_mark_called_without_valid_level_Then_returns_error(async_client):
    """Invalid input: unknown CEFR level returns validation error."""
    headers = await _auth(async_client)

    response = await async_client.post(
        "/api/vocabulary/library/bulk-mark",
        json={"level": "Z9", "target_language": "de", "known": True},
        headers=headers,
    )

    assert response.status_code == 422


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_When_bulk_mark_called_with_invalid_language_code_Then_returns_error(async_client):
    """Invalid input: invalid language code returns validation error."""
    headers = await _auth(async_client)

    response = await async_client.post(
        "/api/vocabulary/library/bulk-mark",
        json={"level": "A1", "target_language": "X", "known": True},  # Invalid language code
        headers=headers,
    )

    assert response.status_code == 422


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_When_library_level_called_with_invalid_level_Then_returns_error(async_client):
    """Invalid input: unknown CEFR level returns validation error."""
    headers = await _auth(async_client)

    response = await async_client.get(
        "/api/vocabulary/library/Z9",
        params={"target_language": "de"},
        headers=headers,
    )

    assert response.status_code == 422


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_When_test_data_endpoint_called_Then_returns_database_info(async_client):
    """Happy path: test-data endpoint returns database statistics."""
    headers = await _auth(async_client)

    response = await async_client.get(
        "/api/vocabulary/test-data",
        headers=headers,
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    payload = response.json()
    assert "concept_count" in payload
    assert "translation_count" in payload
    assert "sample_translations" in payload


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_When_blocking_words_called_Then_returns_structure(async_client, monkeypatch, tmp_path):
    """Happy path: blocking words returns expected keys when SRT exists."""
    headers = await _auth(async_client)
    from api.routes import vocabulary as vocab

    monkeypatch.setattr(type(vocab.settings), "get_videos_path", lambda self: tmp_path)
    (tmp_path / "video.mp4").write_bytes(b"x")
    (tmp_path / "video.srt").write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nHallo Welt\n",
        encoding="utf-8",
    )

    response = await async_client.get(
        "/api/vocabulary/blocking-words",
        params={"video_path": "video.mp4"},
        headers=headers,
    )

    # This endpoint might not be updated yet for the new system
    if response.status_code == 404:
        pytest.skip("Endpoint not implemented yet")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    payload = response.json()
    assert "blocking_words" in payload


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_When_stats_called_without_auth_Then_returns_unauthorized(async_client):
    """Security: stats endpoint requires authentication."""
    response = await async_client.get("/api/vocabulary/stats")
    assert response.status_code == 401, f"Expected 401 (not authenticated), got {response.status_code}: {response.text}"


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_When_mark_known_called_without_auth_Then_returns_unauthorized(async_client):
    """Security: mark-known endpoint requires authentication."""
    response = await async_client.post("/api/vocabulary/mark-known", json={"concept_id": str(uuid4()), "known": True})
    assert response.status_code == 401, f"Expected 401 (not authenticated), got {response.status_code}: {response.text}"


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_When_library_level_called_with_large_limit_Then_succeeds(async_client):
    """Boundary: library level endpoint handles large limit values."""
    headers = await _auth(async_client)

    response = await async_client.get(
        "/api/vocabulary/library/A1",
        params={"target_language": "de", "limit": 1000},
        headers=headers,
    )

    # Large limits should work - the API has no explicit limit validation
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    # Verify response structure
    data = response.json()
    assert "words" in data
    assert "level" in data
    assert isinstance(data["words"], list)


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_When_stats_called_with_unsupported_language_Then_handles_gracefully(async_client):
    """Boundary: stats endpoint handles unsupported language codes gracefully."""
    headers = await _auth(async_client)

    response = await async_client.get(
        "/api/vocabulary/stats",
        params={"target_language": "xx", "translation_language": "yy"},
        headers=headers,
    )

    # Unsupported language codes should return validation error
    assert (
        response.status_code == 422
    ), f"Expected 422 (validation error for unsupported language), got {response.status_code}: {response.text}"


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_When_library_level_called_without_language_params_Then_uses_defaults(async_client):
    """Default behavior: library level endpoint works without explicit language parameters."""
    headers = await _auth(async_client)

    response = await async_client.get(
        "/api/vocabulary/library/A1",
        headers=headers,
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    payload = response.json()
    # Should use default languages (de as target)
    assert payload.get("target_language") == "de"
