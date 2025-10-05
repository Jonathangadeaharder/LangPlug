"""Integration tests for vocabulary endpoints with minimal mocking."""

from __future__ import annotations

import pytest

from tests.helpers import AuthTestHelperAsync


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenvocabulary_statsCalled_ThenReturnslevels(async_client, url_builder, seeded_vocabulary):
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)

    # seeded_vocabulary fixture ensures we have test data available
    response = await async_client.get(
        url_builder.url_for("get_vocabulary_stats"), params={"target_language": "de"}, headers=flow["headers"]
    )

    # Integration test should verify actual behavior, not accept any outcome
    assert response.status_code == 200, f"Expected success but got {response.status_code}: {response.text}"

    json_response = response.json()
    # Verify the expected response structure
    assert "levels" in json_response
    assert "target_language" in json_response
    assert "total_words" in json_response
    assert json_response["target_language"] == "de"
    assert isinstance(json_response["total_words"], int)
    # With seeded_vocabulary, we should have at least 20 words
    assert (
        json_response["total_words"] >= 20
    ), f"Expected at least 20 words from seeded_vocabulary, got {json_response['total_words']}"


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenbulk_mark_level_uses_serviceCalled_ThenSucceeds(async_client, url_builder, seeded_vocabulary):
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)

    # seeded_vocabulary fixture ensures we have A1 level words to mark
    response = await async_client.post(
        url_builder.url_for("bulk_mark_level"),
        json={"level": "A1", "target_language": "de", "known": True},
        headers=flow["headers"],
    )

    # Test that the endpoint works correctly with expected success
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    json_response = response.json()
    assert "success" in json_response
    assert "level" in json_response
    assert "word_count" in json_response
    # With seeded_vocabulary, we should have marked at least 10 A1 words
    assert json_response["word_count"] >= 10, f"Expected at least 10 A1 words marked, got {json_response['word_count']}"
