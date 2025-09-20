"""
Simple transcription service tests using real audio file
Tests interface compliance and basic functionality
"""

import os
import logging
from pathlib import Path
import pytest

from services.transcriptionservice.factory import get_transcription_service

logger = logging.getLogger(__name__)

# Path to test audio file
TEST_AUDIO_FILE = Path(__file__).parent.parent / "data" / "hallo_welt.wav"


class TestTranscriptionServices:
    """Test transcription services with real audio"""

    @pytest.mark.timeout(30)
    def test_Whenaudio_file_existsCalled_ThenSucceeds(self):
        """Verify the test audio file exists"""
        assert TEST_AUDIO_FILE.exists(), f"Test audio file not found: {TEST_AUDIO_FILE}"
        assert TEST_AUDIO_FILE.stat().st_size > 0, "Test audio file is empty"

    @pytest.mark.timeout(120)  # 2 minute timeout for model loading
    def test_Whenwhisper_tiny_transcriptionCalled_ThenSucceeds(self):
        """Test Whisper tiny model transcription"""
        if not TEST_AUDIO_FILE.exists():
            pytest.skip("Test audio file not found")

        # Get Whisper service
        service = get_transcription_service("whisper-tiny")
        assert service is not None, "Failed to create whisper-tiny service"

        # Test transcription
        result = service.transcribe(str(TEST_AUDIO_FILE), language="de")

        # Basic interface validation
        assert result is not None, "Transcription result is None"
        assert hasattr(result, 'full_text'), "Result missing full_text"
        assert hasattr(result, 'segments'), "Result missing segments"
        assert hasattr(result, 'language'), "Result missing language"

        # Content validation - should contain some German text
        text = result.full_text.strip().lower()
        assert len(text) > 0, "Transcribed text is empty"

        # Log result for manual inspection
        logger.info(f"Whisper transcription: '{result.full_text}'")
        logger.info(f"Language detected: {result.language}")
        logger.info(f"Metadata: {result.metadata}")

        # Basic reasonableness check - German audio should produce some text
        # that might relate to "Hallo Welt" or at least contain German-like words
        assert len(text.split()) >= 1, "Transcription too short"

    @pytest.mark.timeout(120)  # 2 minute timeout for model loading
    @pytest.mark.skipif(True, reason="Parakeet requires NeMo which may not be installed")
    def test_Whenparakeet_transcriptionCalled_ThenSucceeds(self):
        """Test Parakeet transcription (English-focused, may not work well with German)"""
        if not TEST_AUDIO_FILE.exists():
            pytest.skip("Test audio file not found")

        try:
            # Get Parakeet service
            service = get_transcription_service("parakeet-tdt-0.6b")
            assert service is not None, "Failed to create parakeet service"

            # Test transcription (Note: Parakeet is English-focused)
            result = service.transcribe(str(TEST_AUDIO_FILE), language="en")

            # Basic interface validation
            assert result is not None, "Transcription result is None"
            assert hasattr(result, 'full_text'), "Result missing full_text"
            assert hasattr(result, 'segments'), "Result missing segments"

            # Log result
            logger.info(f"Parakeet transcription: '{result.full_text}'")
            logger.info(f"Metadata: {result.metadata}")

            # Basic check
            text = result.full_text.strip()
            assert len(text) > 0, "Transcribed text is empty"

        except ImportError as e:
            pytest.skip(f"NeMo not available: {e}")

    @pytest.mark.timeout(30)
    def test_Whentranscription_service_interfaceCalled_ThenSucceeds(self):
        """Test that transcription services implement the correct interface"""
        # Test service creation without initialization
        whisper_service = get_transcription_service("whisper-tiny")
        assert whisper_service is not None

        # Test interface methods exist
        assert hasattr(whisper_service, 'transcribe')
        assert hasattr(whisper_service, 'transcribe_with_timestamps')
        assert hasattr(whisper_service, 'is_initialized')
        assert hasattr(whisper_service, 'service_name')
        assert hasattr(whisper_service, 'cleanup')

        # Test service name
        assert isinstance(whisper_service.service_name, str)
        assert len(whisper_service.service_name) > 0

        logger.info(f"Service name: {whisper_service.service_name}")
        logger.info(f"Is initialized: {whisper_service.is_initialized}")


if __name__ == "__main__":
    # Simple command line test runner
    logging.basicConfig(level=logging.INFO)

    test_class = TestTranscriptionServices()

    print("=== Testing Transcription Services ===")

    try:
        test_class.test_audio_file_exists()
        print("✅ Audio file exists")
    except Exception as e:
        print(f"❌ Audio file test failed: {e}")

    try:
        test_class.test_transcription_service_interface()
        print("✅ Service interface test passed")
    except Exception as e:
        print(f"❌ Interface test failed: {e}")

    try:
        test_class.test_whisper_tiny_transcription()
        print("✅ Whisper transcription test passed")
    except Exception as e:
        print(f"❌ Whisper test failed: {e}")

    print("=== Test Complete ===")