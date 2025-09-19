"""
Tests for core.dependencies service availability.
"""
from __future__ import annotations

import pytest
from core import dependencies as deps


@pytest.mark.timeout(30)
def test_Whendatabase_manager_availableCalled_ThenSucceeds():
    """Test that database manager is available through dependency injection"""
    db_manager = deps.get_database_manager()
    # Should return the SQLAlchemy engine without errors
    assert db_manager is not None


@pytest.mark.timeout(30)
def test_Whenauth_service_availableCalled_ThenSucceeds():
    """Test that auth service is available through dependency injection"""
    auth_service = deps.get_auth_service()
    # Should return the FastAPI-Users instance without errors
    assert auth_service is not None


@pytest.mark.timeout(30)
def test_Whentranscription_service_initializationCalled_ThenSucceeds():
    """Test that transcription service can be initialized (may return None if unavailable)"""
    # This should not raise an exception even if service is unavailable
    transcription_service = deps.get_transcription_service()
    # Service may be None if not properly configured, but should not raise an exception
    assert transcription_service is None or hasattr(transcription_service, 'transcribe')

