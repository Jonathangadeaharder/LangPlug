"""Behavior-driven tests for `AuthenticatedUserVocabularyService`."""
from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest

from services.dataservice.authenticated_user_vocabulary_service import (
    AuthenticatedUserVocabularyService,
    InsufficientPermissionsError,
)


@dataclass
class DummyUser:
    id: int
    username: str
    is_admin: bool = False


@pytest.fixture
def service(monkeypatch):
    svc = AuthenticatedUserVocabularyService(db_session=AsyncMock())
    svc.vocab_service = AsyncMock()
    return svc


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenget_known_words_allows_self_accessCalled_ThenSucceeds(service):
    """Happy path: users can read their own known words."""
    requesting = DummyUser(id=1, username="alice")
    service.vocab_service.get_known_words.return_value = {"hallo"}

    words = await service.get_known_words(requesting, str(requesting.id))

    assert words == {"hallo"}
    service.vocab_service.get_known_words.assert_called_once_with(str(requesting.id), "en")


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenmark_word_learned_blocks_other_usersCalled_ThenSucceeds(service):
    """Invalid scenario: non-admin cannot modify another user's vocabulary."""
    requesting = DummyUser(id=1, username="alice")

    with pytest.raises(InsufficientPermissionsError):
        await service.mark_word_learned(requesting, "2", "word", "en")

    service.vocab_service.mark_word_learned.assert_not_called()


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenadmin_can_update_any_userCalled_ThenSucceeds(service):
    """Boundary: admins bypass the access restriction."""
    requesting = DummyUser(id=99, username="admin", is_admin=True)
    service.vocab_service.set_learning_level.return_value = True

    success = await service.set_learning_level(requesting, "2", "B1")

    assert success is True
    service.vocab_service.set_learning_level.assert_called_once_with("2", "B1")
