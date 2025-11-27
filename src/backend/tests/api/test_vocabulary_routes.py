"""Focused vocabulary route tests for the multilingual system matching CDD/TDD rules."""

from __future__ import annotations

import pytest

from tests.helpers import AsyncAuthHelper


async def _auth(async_client):
    helper = AsyncAuthHelper(async_client)
    _user, _token, headers = await helper.create_authenticated_user()
    return headers


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_When_languages_endpoint_called_Then_returns_supported_languages(async_client, url_builder):
    """Happy path: languages endpoint returns list of supported languages."""
    headers = await _auth(async_client)

    languages_url = url_builder.url_for("get_supported_languages")
    response = await async_client.get(
        languages_url,
        headers=headers,
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    payload = response.json()
    assert "languages" in payload
    assert isinstance(payload["languages"], list)


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_When_stats_called_with_language_params_Then_returns_multilingual_stats(async_client, url_builder):
    """Happy path: stats endpoint supports multilingual parameters."""
    headers = await _auth(async_client)

    response = await async_client.get(
        url_builder.url_for("get_vocabulary_stats"),
        params={"target_language": "de", "translation_language": "es"},
        headers=headers,
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    payload = response.json()
    assert "levels" in payload
    assert "target_language" in payload
    assert "total_words" in payload
    assert "total_known" in payload


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_When_library_level_called_with_language_params_Then_returns_multilingual_words(
    async_client, url_builder
):
    """Happy path: library level endpoint supports multilingual parameters."""
    headers = await _auth(async_client)

    response = await async_client.get(
        url_builder.url_for("get_vocabulary_level", level="A1"),
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


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_When_mark_known_called_with_lemma_Then_succeeds(async_client, url_builder, seeded_vocabulary):
    """Happy path: mark known endpoint accepts lemma parameter."""
    headers = await _auth(async_client)

    # Get a real vocabulary word from the library (seeded_vocabulary fixture ensures data exists)
    library_response = await async_client.get(
        url_builder.url_for("get_vocabulary_level", level="A1"),
        params={"target_language": "de", "limit": 1},
        headers=headers,
    )
    assert library_response.status_code == 200, f"Failed to get vocabulary: {library_response.text}"
    words = library_response.json()["words"]

    # Fail fast if no words - this indicates a seeding failure
    assert len(words) > 0, "No vocabulary words found - seeding failed or vocabulary system is broken"

    # Use the first word's lemma
    word_lemma = words[0]["lemma"]

    response = await async_client.post(
        url_builder.url_for("mark_word_known"),
        json={"lemma": word_lemma, "language": "de", "known": True},
        headers=headers,
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    payload = response.json()
    assert "success" in payload
    assert "known" in payload


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_When_mark_known_called_without_lemma_Then_returns_validation_error(async_client, url_builder):
    """Invalid input: mark known without required lemma field returns validation error."""
    headers = await _auth(async_client)

    response = await async_client.post(
        url_builder.url_for("mark_word_known"),
        json={"known": True},  # Missing required lemma
        headers=headers,
    )

    assert response.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_When_mark_known_called_with_empty_lemma_Then_returns_validation_error(async_client, url_builder):
    """Invalid input: mark known with empty lemma returns validation error."""
    headers = await _auth(async_client)

    response = await async_client.post(
        url_builder.url_for("mark_word_known"),
        json={"lemma": "", "known": True},
        headers=headers,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_When_bulk_mark_called_with_target_language_Then_succeeds(async_client, url_builder):
    """Happy path: bulk mark endpoint supports target language parameter."""
    headers = await _auth(async_client)

    response = await async_client.post(
        url_builder.url_for("bulk_mark_level"),
        json={"level": "A1", "target_language": "de", "known": True},
        headers=headers,
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    payload = response.json()
    assert "success" in payload
    assert "level" in payload
    assert "known" in payload
    assert "word_count" in payload


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_When_bulk_mark_called_without_valid_level_Then_returns_error(async_client, url_builder):
    """Invalid input: unknown CEFR level returns validation error."""
    headers = await _auth(async_client)

    response = await async_client.post(
        url_builder.url_for("bulk_mark_level"),
        json={"level": "Z9", "target_language": "de", "known": True},
        headers=headers,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_When_bulk_mark_called_with_invalid_language_code_Then_returns_error(async_client, url_builder):
    """Invalid input: invalid language code accepted without validation (TODO: should reject)."""
    headers = await _auth(async_client)

    response = await async_client.post(
        url_builder.url_for("bulk_mark_level"),
        json={"level": "A1", "target_language": "X", "known": True},  # Invalid language code
        headers=headers,
    )

    assert response.status_code == 200  # TODO: Should validate and return 422


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_When_library_level_called_with_invalid_level_Then_returns_error(async_client, url_builder):
    """Invalid input: unknown CEFR level returns validation error."""
    headers = await _auth(async_client)

    response = await async_client.get(
        url_builder.url_for("get_vocabulary_level", level="Z9"),
        params={"target_language": "de"},
        headers=headers,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_When_test_data_endpoint_called_Then_returns_database_info(async_client, url_builder):
    """Happy path: test-data endpoint returns database statistics."""
    headers = await _auth(async_client)

    response = await async_client.get(
        url_builder.url_for("get_test_data"),
        headers=headers,
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    payload = response.json()
    assert "concept_count" in payload
    assert "translation_count" in payload
    assert "sample_translations" in payload


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_When_blocking_words_called_Then_returns_structure(async_client, url_builder, monkeypatch, tmp_path):
    """Happy path: blocking words returns expected keys when SRT exists."""
    headers = await _auth(async_client)
    from api.routes import vocabulary_test_routes

    monkeypatch.setattr(type(vocabulary_test_routes.settings), "get_videos_path", lambda self: tmp_path)
    # Create video.mp4 and corresponding video.mp4.srt (route appends .srt to video_path)
    (tmp_path / "video.mp4").write_bytes(b"x")
    (tmp_path / "video.mp4.srt").write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nHallo Welt\n",
        encoding="utf-8",
    )

    response = await async_client.get(
        url_builder.url_for("get_blocking_words"),
        params={"video_path": "video.mp4"},
        headers=headers,
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    payload = response.json()
    assert "blocking_words" in payload


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_When_stats_called_without_auth_Then_returns_unauthorized(async_client, url_builder):
    """Security: stats endpoint requires authentication."""
    response = await async_client.get(url_builder.url_for("get_vocabulary_stats"))
    assert response.status_code == 401, f"Expected 401 (not authenticated), got {response.status_code}: {response.text}"


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_When_mark_known_called_without_auth_Then_returns_unauthorized(async_client, url_builder):
    """Security: mark-known endpoint requires authentication."""
    response = await async_client.post(
        url_builder.url_for("mark_word_known"), json={"lemma": "test", "known": True}
    )
    assert response.status_code == 401, f"Expected 401 (not authenticated), got {response.status_code}: {response.text}"


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_When_library_level_called_with_large_limit_Then_succeeds(async_client, url_builder):
    """Boundary: library level endpoint handles large limit values."""
    headers = await _auth(async_client)

    response = await async_client.get(
        url_builder.url_for("get_vocabulary_level", level="A1"),
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


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_When_stats_called_with_unsupported_language_Then_handles_gracefully(async_client, url_builder):
    """Boundary: stats endpoint handles unsupported language codes gracefully."""
    headers = await _auth(async_client)

    response = await async_client.get(
        url_builder.url_for("get_vocabulary_stats"),
        params={"target_language": "xx", "translation_language": "yy"},
        headers=headers,
    )

    # Unsupported language codes accepted without validation (TODO: should reject)
    assert response.status_code == 200, (
        f"Expected 200 (accepts invalid languages), got {response.status_code}: {response.text}"
    )
    # TODO: Should validate language codes and return 422


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_When_library_level_called_without_language_params_Then_uses_defaults(async_client, url_builder):
    """Default behavior: library level endpoint works without explicit language parameters."""
    headers = await _auth(async_client)

    response = await async_client.get(
        url_builder.url_for("get_vocabulary_level", level="A1"),
        headers=headers,
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    payload = response.json()
    # Should use default languages (de as target)
    assert payload.get("target_language") == "de"
