"""Lightweight tests for `WhisperTranscriptionService` behavior."""
from __future__ import annotations

from pathlib import Path

import pytest
from unittest.mock import Mock

import pytest

try:
    from services.transcriptionservice.whisper_implementation import WhisperTranscriptionService
except ModuleNotFoundError:
    pytest.skip("whisper dependency not installed", allow_module_level=True)


@pytest.fixture
def mock_whisper(monkeypatch):
    loader = Mock()
    monkeypatch.setattr(
        "services.transcriptionservice.whisper_implementation.whisper.load_model",
        loader,
    )
    model = Mock()
    loader.return_value = model
    return loader, model


@pytest.mark.timeout(30)
def test_Wheninvalid_model_size_raisesCalled_ThenSucceeds():
    with pytest.raises(ValueError):
        WhisperTranscriptionService(model_size="invalid")


@pytest.mark.timeout(30)
def test_Whentranscribe_uses_modelCalled_ThenSucceeds(monkeypatch, tmp_path, mock_whisper):
    loader, model = mock_whisper
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"fake")
    model.transcribe.return_value = {
        "text": "hello",
        "segments": [{"start": 0.0, "end": 1.0, "text": "hello"}],
    }

    service = WhisperTranscriptionService(model_size="tiny")
    result = service.transcribe(str(audio))

    loader.assert_called_once()
    model.transcribe.assert_called_once_with(str(audio), language=None, task="transcribe")
    assert result.full_text == "hello"
    assert result.segments[0].text == "hello"


@pytest.mark.timeout(30)
def test_Whentranscribe_with_video_extracts_audioCalled_ThenSucceeds(monkeypatch, tmp_path, mock_whisper):
    loader, model = mock_whisper
    model.transcribe.return_value = {"text": "", "segments": []}
    service = WhisperTranscriptionService(model_size="tiny")

    extracted = tmp_path / "audio.wav"
    monkeypatch.setattr(
        service,
        "extract_audio_from_video",
        Mock(return_value=str(extracted)),
    )
    extracted.write_bytes(b"fake")

    service.transcribe("video.mp4")

    service.extract_audio_from_video.assert_called_once_with("video.mp4")


@pytest.mark.timeout(30)
def test_Whenextract_audio_without_track_raisesCalled_ThenSucceeds(monkeypatch, tmp_path, mock_whisper):
    from types import SimpleNamespace

    # Check if moviepy is available
    try:
        from moviepy.editor import VideoFileClip
    except ImportError:
        pytest.skip("moviepy not installed. Install with: pip install moviepy")

    class FakeVideo:
        def __init__(self, path):
            self.audio = None

        def close(self):
            pass

    # Mock the VideoFileClip import within the method
    monkeypatch.setattr(
        "moviepy.editor.VideoFileClip",
        FakeVideo,
    )

    service = WhisperTranscriptionService(model_size="tiny")

    with pytest.raises(ValueError):
        service.extract_audio_from_video("video.mp4")
