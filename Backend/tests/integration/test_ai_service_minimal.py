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
        result = service.transcribe(f.name, language="en")
        assert result is not None
        os.unlink(f.name)


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("SKIP_HEAVY_AI_TESTS") == "1", reason="Skipping AI model tests - set SKIP_HEAVY_AI_TESTS=0 to run"
)
def test_opus_de_es_hello_world():
    """Minimal OPUS Helsinki translation test."""
    service = TranslationServiceFactory.create_service("opus-de-es")
    result = service.translate("Hallo", source_language="de", target_language="es")
    assert result is not None
    assert result != "Hallo"  # Should translate German to Spanish


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("SKIP_HEAVY_AI_TESTS") == "1", reason="Skipping AI model tests - set SKIP_HEAVY_AI_TESTS=0 to run"
)
def test_nllb_distilled_hello_world():
    """Minimal NLLB distilled translation test."""
    service = TranslationServiceFactory.create_service("nllb-distilled-600m")
    result = service.translate("Hello", source_language="en", target_language="es")
    assert result is not None
    assert result != "Hello"  # Should translate English to Spanish


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
            result = service.transcribe(f.name, language="en")
            assert result is not None
            os.unlink(f.name)
    except ImportError:
        pytest.skip("NeMo toolkit not installed")
