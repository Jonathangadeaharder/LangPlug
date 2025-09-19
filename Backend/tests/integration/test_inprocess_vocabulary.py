"""Integration tests for vocabulary endpoints with minimal mocking."""
from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest

from tests.auth_helpers import AuthTestHelperAsync


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenvocabulary_statsCalled_ThenReturnslevels(async_client, monkeypatch):
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)

    fake_service = Mock()
    fake_service.get_vocabulary_stats = AsyncMock(return_value={"A1": {"total_words": 2}})
    fake_service.get_user_known_words = AsyncMock(return_value=set())
    
    with patch("api.routes.vocabulary.VocabularyPreloadService", return_value=fake_service):
        response = await async_client.get(
            "/api/vocabulary/library/stats", headers=flow["headers"]
        )

        assert response.status_code == 200
        assert response.json()["levels"]["A1"]["total_words"] == 2


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenbulk_mark_level_uses_serviceCalled_ThenSucceeds(async_client, monkeypatch):
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)

    fake_service = Mock()
    fake_service.bulk_mark_level_known = AsyncMock(return_value=3)
    
    with patch("api.routes.vocabulary.VocabularyPreloadService", return_value=fake_service):
        response = await async_client.post(
            "/api/vocabulary/library/bulk-mark",
            json={"level": "A1", "known": True},
            headers=flow["headers"],
        )

        assert response.status_code == 200
        fake_service.bulk_mark_level_known.assert_called_once()
