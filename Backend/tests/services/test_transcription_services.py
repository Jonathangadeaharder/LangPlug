"""Transcription service interface tests."""

from __future__ import annotations

import pytest

from services.transcriptionservice.factory import get_transcription_service


@pytest.mark.timeout(30)
def test_Whenservice_factory_called_ThenReturnsService():
    """Service factory should return a service instance or None if unavailable."""
    service = get_transcription_service("whisper-tiny")
    if service is not None:
        assert hasattr(service, "transcribe"), "Service missing transcribe method"


@pytest.mark.timeout(30)
def test_Wheninvalid_service_requested_ThenReturnsNone():
    """Service factory should raise ValueError for invalid service names."""
    with pytest.raises(ValueError, match="Unknown transcription service"):
        get_transcription_service("invalid-service-name")
