"""Tests for WhisperTranscriptionService behavior."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

try:
    from services.transcriptionservice.whisper_implementation import WhisperTranscriptionService
except ModuleNotFoundError:
    pytest.skip("whisper dependency not installed", allow_module_level=True)


@pytest.fixture
def mock_whisper(monkeypatch):
    """Mock whisper model for testing."""
    loader = Mock()
    model = Mock()
    loader.return_value = model
    monkeypatch.setattr(
        "services.transcriptionservice.whisper_implementation.whisper.load_model",
        loader,
    )
    return loader, model


@pytest.mark.timeout(30)
def test_Wheninvalid_model_size_ThenRaisesError():
    """Invalid model size should raise ValueError."""
    with pytest.raises(ValueError):
        WhisperTranscriptionService(model_size="invalid")


@pytest.mark.timeout(30)
def test_Whentranscribe_called_ThenUsesModel(tmp_path, mock_whisper):
    """Transcribe should use the whisper model correctly."""
    loader, model = mock_whisper
    audio_file = tmp_path / "audio.wav"
    audio_file.write_bytes(b"fake audio data")

    model.transcribe.return_value = {
        "text": "hello world",
        "segments": [{"start": 0.0, "end": 2.0, "text": "hello world"}],
    }

    service = WhisperTranscriptionService(model_size="tiny")
    result = service.transcribe(str(audio_file))

    loader.assert_called_once()
    model.transcribe.assert_called_once_with(str(audio_file), language=None, task="transcribe")
    assert result.full_text == "hello world"
    assert result.segments[0].text == "hello world"


@pytest.mark.timeout(30)
def test_Whenvideo_file_provided_ThenExtractsAudio(tmp_path, mock_whisper):
    """Video files should be converted to audio before transcription."""
    _loader, model = mock_whisper
    model.transcribe.return_value = {"text": "video audio", "segments": []}

    service = WhisperTranscriptionService(model_size="tiny")
    extract_mock = Mock(return_value=str(tmp_path / "extracted.wav"))
    service.extract_audio_from_video = extract_mock

    (tmp_path / "extracted.wav").write_bytes(b"extracted audio")

    service.transcribe("video.mp4")

    extract_mock.assert_called_once_with("video.mp4")
