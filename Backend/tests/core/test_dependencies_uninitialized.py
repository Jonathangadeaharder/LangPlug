"""Core dependency availability tests."""

from __future__ import annotations

import pytest

from core import dependencies as deps


@pytest.mark.timeout(30)
def test_Whendatabase_manager_requested_ThenReturnsInstance():
    """Database manager should be available through dependency injection."""
    db_manager = deps.get_database_manager()
    assert db_manager is not None


@pytest.mark.timeout(30)
def test_Whenauth_service_requested_ThenReturnsInstance():
    """Auth service should be available through dependency injection."""
    auth_service = deps.get_auth_service()
    assert auth_service is not None


@pytest.mark.timeout(30)
def test_Whentranscription_service_requested_ThenReturnsInstanceOrNone():
    """Transcription service should return instance or None if unavailable."""
    transcription_service = deps.get_transcription_service()
    if transcription_service is not None:
        assert hasattr(transcription_service, "transcribe")
