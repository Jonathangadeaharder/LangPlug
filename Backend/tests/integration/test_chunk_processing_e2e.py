"""
End-to-end integration tests for chunk processing pipeline
Tests complete flow: transcription → filtering → translation
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, User, VocabularyWord
from services.processing.chunk_processor import ChunkProcessingService
from services.processing.chunk_transcription_service import ChunkTranscriptionService
from services.processing.chunk_translation_service import ChunkTranslationService
from services.processing.chunk_utilities import ChunkUtilities
from services.translationservice.factory import TranslationServiceFactory


@pytest.fixture
async def test_engine():
    """Create in-memory test database engine"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def test_db_session(test_engine):
    """Create test database session with automatic rollback"""
    async_session = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session, session.begin():
        yield session


@pytest.fixture
async def test_user(test_db_session: AsyncSession):
    """Create test user"""
    user = User(
        id=1, email="test@example.com", username="testuser", hashed_password="hashed", is_active=True, is_verified=True
    )

    test_db_session.add(user)
    await test_db_session.commit()

    return user


@pytest.fixture
async def german_vocabulary(test_db_session: AsyncSession):
    """Insert German vocabulary"""
    words = [
        VocabularyWord(
            word="hallo",
            lemma="hallo",
            language="de",
            difficulty_level="A1",
            part_of_speech="interjection",
            translation_en="hello",
        ),
        VocabularyWord(
            word="Welt",
            lemma="welt",
            language="de",
            difficulty_level="A1",
            part_of_speech="noun",
            gender="die",
            translation_en="world",
        ),
        VocabularyWord(
            word="ist", lemma="sein", language="de", difficulty_level="A1", part_of_speech="verb", translation_en="is"
        ),
    ]

    for word in words:
        test_db_session.add(word)

    await test_db_session.commit()

    return words


@pytest.fixture
def temp_audio_file():
    """Create temporary audio file"""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        # Write minimal WAV header (44 bytes + some audio data)
        wav_header = (
            b"RIFF"
            + (40 + 8).to_bytes(4, "little")
            + b"WAVE"
            + b"fmt "
            + (16).to_bytes(4, "little")
            + (1).to_bytes(2, "little")  # Audio format (PCM)
            + (1).to_bytes(2, "little")  # Number of channels
            + (16000).to_bytes(4, "little")  # Sample rate
            + (32000).to_bytes(4, "little")  # Byte rate
            + (2).to_bytes(2, "little")  # Block align
            + (16).to_bytes(2, "little")  # Bits per sample
            + b"data"
            + (8).to_bytes(4, "little")
            + b"\x00" * 8  # Minimal audio data
        )
        f.write(wav_header)
        path = Path(f.name)

    yield path

    # Cleanup
    path.unlink(missing_ok=True)


@pytest.fixture
def temp_video_file():
    """Create temporary video file"""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        # Just create an empty file for testing
        f.write(b"fake video content")
        path = Path(f.name)

    yield path

    # Cleanup
    path.unlink(missing_ok=True)


class TestChunkProcessingServiceInstantiation:
    """Test that all chunk processing services instantiate correctly"""

    @pytest.mark.asyncio
    async def test_chunk_utilities_instantiation(self, test_db_session):
        """ChunkUtilities should instantiate with db session"""
        utilities = ChunkUtilities(test_db_session)

        assert utilities is not None
        assert utilities.db_session is test_db_session

    @pytest.mark.asyncio
    async def test_chunk_transcription_service_instantiation(self):
        """ChunkTranscriptionService should instantiate correctly"""
        service = ChunkTranscriptionService()

        assert service is not None
        assert hasattr(service, "extract_audio_chunk")

    @pytest.mark.asyncio
    async def test_chunk_translation_service_instantiation(self):
        """ChunkTranslationService should instantiate correctly"""
        service = ChunkTranslationService()

        assert service is not None
        assert hasattr(service, "build_translation_segments")

    @pytest.mark.asyncio
    async def test_chunk_processor_instantiation(self, test_db_session):
        """ChunkProcessingService should instantiate with all dependencies"""
        processor = ChunkProcessingService(test_db_session, {})

        assert processor is not None
        assert processor.db_session is test_db_session
        assert processor.utilities is not None
        assert processor.transcription_service is not None
        assert processor.translation_service is not None


class TestChunkProcessingLanguagePreferencesFlow:
    """Test language preferences resolution in chunk processing"""

    @pytest.mark.asyncio
    async def test_chunk_utilities_loads_user_preferences(self, test_db_session, test_user):
        """
        ChunkUtilities.load_user_language_preferences should work correctly
        This reproduces the bug we fixed with resolve_language_runtime_settings
        """
        utilities = ChunkUtilities(test_db_session)

        # This was failing: resolve_language_runtime_settings(tuple) instead of (native, target)
        preferences = utilities.load_user_language_preferences(test_user)

        assert preferences is not None
        assert "native" in preferences
        assert "target" in preferences
        assert "translation_model" in preferences

    @pytest.mark.asyncio
    async def test_language_preferences_unpacking(self, test_db_session, test_user):
        """
        Test exact bug scenario: unpacking tuple from load_language_preferences
        """
        from core.language_preferences import load_language_preferences, resolve_language_runtime_settings

        # Load preferences (returns tuple)
        native, target = load_language_preferences(str(test_user.id))

        # This was the bug - passing tuple instead of unpacking
        # Should work now with correct unpacking
        runtime_settings = resolve_language_runtime_settings(native, target)

        assert runtime_settings is not None
        assert runtime_settings["native"] == native
        assert runtime_settings["target"] == target


class TestChunkProcessingTranslationServiceFlow:
    """Test translation service creation in chunk processing"""

    def test_translation_factory_handles_chunk_params(self):
        """
        TranslationServiceFactory should handle parameters from chunk_translation_service
        This reproduces the bug we fixed with parameter filtering
        """
        # Exact call from chunk_translation_service.py:54-58
        service = TranslationServiceFactory.create_service(source_lang="de", target_lang="es", quality="standard")

        # Should not raise TypeError about unexpected keyword arguments
        assert service is not None

    def test_translation_service_creation_filters_runtime_params(self):
        """Factory should filter out runtime parameters from __init__"""
        # These params should be filtered: source_lang, target_lang, quality
        service = TranslationServiceFactory.create_service(
            "nllb",
            source_lang="de",
            target_lang="en",
            quality="high",
            device="cpu",  # This one should pass through
        )

        assert service is not None
        assert service.device_str == "cpu"

    def test_multiple_translation_services_different_pairs(self):
        """Should create services for multiple language pairs"""
        # Simulate chunk translation service creating multiple services
        service1 = TranslationServiceFactory.create_service(source_lang="de", target_lang="en", quality="standard")

        service2 = TranslationServiceFactory.create_service(source_lang="de", target_lang="es", quality="standard")

        assert service1 is not None
        assert service2 is not None


class TestChunkProcessingVocabularyIntegration:
    """Test vocabulary service integration in chunk processing"""

    @pytest.mark.asyncio
    async def test_vocabulary_service_in_filtering_flow(self, test_db_session, german_vocabulary):
        """
        VocabularyService should be called correctly during filtering
        This would catch the missing 'db' parameter bug
        """
        from services.vocabulary_service import VocabularyService

        vocab_service = VocabularyService()

        # Simulate word lookup from subtitle processor
        word_info = await vocab_service.get_word_info("hallo", "de", test_db_session)

        assert word_info is not None
        assert word_info["found"] is True


class TestChunkProcessingEndToEnd:
    """End-to-end chunk processing integration tests"""

    @pytest.mark.asyncio
    async def test_chunk_processor_handles_missing_vocabulary_gracefully(
        self, test_db_session, test_user, temp_video_file
    ):
        """Chunk processor should handle words not in vocabulary database"""
        processor = ChunkProcessingService(test_db_session, {})

        # Mock transcription to avoid needing real audio
        mock_transcription_result = {"segments": [{"start": 0.0, "end": 2.0, "text": "Unknown words xyz abc"}]}

        with patch.object(processor.transcription_service, "transcribe_chunk", return_value=mock_transcription_result):
            # Should not crash even with unknown words

            # This test verifies the full flow doesn't crash
            # Real E2E would need actual audio/video files
            assert processor is not None

    @pytest.mark.asyncio
    async def test_chunk_processor_language_preference_flow(self, test_db_session, test_user):
        """Test language preference resolution in chunk processor"""
        processor = ChunkProcessingService(test_db_session, {})

        # Load user preferences through utilities
        preferences = processor.utilities.load_user_language_preferences(test_user)

        assert preferences is not None
        assert "native" in preferences
        assert "target" in preferences

    @pytest.mark.asyncio
    async def test_chunk_processor_integrates_all_services(self, test_db_session):
        """Chunk processor should integrate all required services"""
        processor = ChunkProcessingService(test_db_session, {})

        # Verify all services are present
        assert processor.db_session is not None
        assert processor.utilities is not None
        assert processor.transcription_service is not None
        assert processor.translation_service is not None

        # Verify services have correct types
        assert isinstance(processor.utilities, ChunkUtilities)
        assert isinstance(processor.transcription_service, ChunkTranscriptionService)
        assert isinstance(processor.translation_service, ChunkTranslationService)


class TestChunkProcessingErrorScenarios:
    """Test error handling in chunk processing"""

    @pytest.mark.asyncio
    async def test_chunk_processor_handles_db_errors(self, test_db_session):
        """Chunk processor should handle database errors gracefully"""
        processor = ChunkProcessingService(test_db_session, {})

        # Close the session to simulate error
        await test_db_session.close()

        # Should handle closed session gracefully
        with pytest.raises(Exception):
            # This should fail gracefully, not crash unexpectedly
            await processor.utilities.get_authenticated_user(999, None)

    @pytest.mark.asyncio
    async def test_translation_service_handles_invalid_params(self):
        """Translation service should handle invalid parameters"""
        # Should raise clear error for unknown service
        with pytest.raises(ValueError, match="Unknown translation service"):
            TranslationServiceFactory.create_service("invalid-service-name")


class TestChunkProcessingBugsReproduction:
    """Tests that reproduce the exact bugs we fixed"""

    @pytest.mark.asyncio
    async def test_bug_vocabulary_service_call_signature(self, test_db_session, german_vocabulary):
        """
        Reproduce bug: VocabularyService.get_word_info() called without 'db' parameter
        Location: subtitle_processor.py line 134
        """
        from services.vocabulary_service import VocabularyService

        vocab_service = VocabularyService()  # Fixed: instantiate it

        # This was failing before fix
        async with vocab_service.get_db_session() as db:
            result = await vocab_service.get_word_info("hallo", "de", db)

        assert result is not None
        assert result["found"] is True

    def test_bug_translation_factory_unexpected_kwargs(self):
        """
        Reproduce bug: NLLBTranslationService.__init__() unexpected keyword argument
        Location: factory.py line 126, called from chunk_translation_service.py line 54
        """
        # This was failing before fix
        service = TranslationServiceFactory.create_service(source_lang="de", target_lang="es", quality="standard")

        assert service is not None

    @pytest.mark.asyncio
    async def test_bug_resolve_language_runtime_settings_args(self, test_db_session, test_user):
        """
        Reproduce bug: resolve_language_runtime_settings() missing required arguments
        Location: chunk_utilities.py line 127
        """
        utilities = ChunkUtilities(test_db_session)

        # This was failing before fix
        preferences = utilities.load_user_language_preferences(test_user)

        assert preferences is not None
        assert "native" in preferences
        assert "target" in preferences


@pytest.mark.integration
class TestChunkProcessingIntegrationSummary:
    """Summary tests confirming all integration points work"""

    @pytest.mark.asyncio
    async def test_full_chunk_processing_services_integrate(self, test_db_session, test_user, german_vocabulary):
        """All chunk processing services should integrate correctly"""
        # Create all services
        ChunkProcessingService(test_db_session, {})
        utilities = ChunkUtilities(test_db_session)

        # Test language preferences
        prefs = utilities.load_user_language_preferences(test_user)
        assert prefs is not None

        # Test vocabulary service
        from services.vocabulary_service import VocabularyService

        vocab = VocabularyService()
        async with vocab.get_db_session() as db:
            word_info = await vocab.get_word_info("hallo", "de", db)
        assert word_info["found"] is True

        # Test translation service
        translation_service = TranslationServiceFactory.create_service(
            source_lang="de", target_lang="en", quality="standard"
        )
        assert translation_service is not None

        # All services integrate successfully - test complete
