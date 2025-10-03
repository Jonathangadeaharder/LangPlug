"""
Minimal functional tests for AI services using real models.
Each test should complete in under 10 seconds using smallest models.
"""

import os
import tempfile

import pytest

from services.transcriptionservice.factory import get_transcription_service
from services.translationservice.factory import TranslationServiceFactory


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("SKIP_HEAVY_AI_TESTS") == "1", reason="Skipping AI model tests - set SKIP_HEAVY_AI_TESTS=0 to run"
)
def test_whisper_tiny_hello_world():
    """Minimal whisper-tiny transcription test."""
    service = get_transcription_service("whisper-tiny")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        # Minimal 1-second silent WAV
        f.write(
            b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
        )
        f.flush()
        temp_path = f.name
    try:
        result = service.transcribe(temp_path, language="en")
        assert result is not None
    finally:
        try:
            os.unlink(temp_path)
        except (FileNotFoundError, PermissionError):
            pass  # File already deleted or still in use


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("SKIP_HEAVY_AI_TESTS") == "1", reason="Skipping AI model tests - set SKIP_HEAVY_AI_TESTS=0 to run"
)
def test_opus_de_es_hello_world():
    """Minimal OPUS Helsinki translation test."""
    service = TranslationServiceFactory.create_service("opus-de-es")
    result = service.translate("Hallo", source_lang="de", target_lang="es")
    assert result is not None
    assert result.translated_text != "Hallo"  # Should translate German to Spanish


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("SKIP_HEAVY_AI_TESTS") == "1", reason="Skipping AI model tests - set SKIP_HEAVY_AI_TESTS=0 to run"
)
def test_nllb_distilled_hello_world():
    """Minimal NLLB distilled translation test."""
    service = TranslationServiceFactory.create_service("nllb-distilled-600m")
    result = service.translate("Hello", source_lang="en", target_lang="es")
    assert result is not None
    assert result.translated_text != "Hello"  # Should translate English to Spanish


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("SKIP_HEAVY_AI_TESTS") == "1", reason="Skipping AI model tests - set SKIP_HEAVY_AI_TESTS=0 to run"
)
def test_parakeet_tiny_hello_world():
    """Minimal Parakeet (NeMo) transcription test."""
    try:
        service = get_transcription_service("parakeet-ctc-0.6b")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            # Minimal 1-second silent WAV
            f.write(
                b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
            )
            f.flush()
            temp_path = f.name
        try:
            result = service.transcribe(temp_path, language="en")
            assert result is not None
        finally:
            try:
                os.unlink(temp_path)
            except (FileNotFoundError, PermissionError):
                pass  # File already deleted or still in use
    except ImportError:
        pytest.skip("NeMo toolkit not installed")
