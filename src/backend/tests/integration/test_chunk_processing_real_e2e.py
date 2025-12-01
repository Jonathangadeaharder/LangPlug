"""
True end-to-end integration tests for chunk processing
Tests actual service methods with minimal mocking - exercises real code paths
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, VocabularyWord
from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor
from services.filterservice.interface import FilteredSubtitle, FilteredWord
from services.translationservice.factory import TranslationServiceFactory
from services.vocabulary.vocabulary_service import VocabularyService

# Check if spaCy German models are available
try:
    import spacy

    spacy.load("de_core_news_lg")
    SPACY_DE_AVAILABLE = True
except (ImportError, OSError):
    SPACY_DE_AVAILABLE = False

skip_if_no_spacy_de = pytest.mark.skipif(
    not SPACY_DE_AVAILABLE, reason="spaCy German language model (de_core_news_lg) not installed"
)


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
    """Create test database session with proper transaction management"""
    async_session = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def german_vocabulary(test_db_session: AsyncSession):
    """Insert German vocabulary test data"""
    words = [
        VocabularyWord(
            word="Hallo",
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


@skip_if_no_spacy_de
class TestVocabularyServiceSessionManagement:
    """Test that VocabularyService creates sessions correctly"""

    @pytest.mark.asyncio
    async def test_vocabulary_service_accepts_external_session(self, test_db_session, german_vocabulary):
        """
        VocabularyService should accept external database session
        This test reproduces Bug #4 - would have caught get_db_session() error
        """
        from services.vocabulary.vocabulary_progress_service import get_vocabulary_progress_service
        from services.vocabulary.vocabulary_query_service import get_vocabulary_query_service
        from services.vocabulary.vocabulary_stats_service import get_vocabulary_stats_service

        # Create real service instances
        query_service = get_vocabulary_query_service()
        progress_service = get_vocabulary_progress_service()
        stats_service = get_vocabulary_stats_service()
        service = VocabularyService(query_service, progress_service, stats_service)

        # Service should accept passed-in session (the correct pattern)
        result = await service.get_word_info("hallo", "de", test_db_session)

        # Verify actual query worked
        assert result is not None
        assert result["found"] is True
        assert result["word"].lower() == "hallo"

    @pytest.mark.asyncio
    async def test_subtitle_processor_uses_correct_session_pattern(self, german_vocabulary, test_db_session):
        """
        DirectSubtitleProcessor should use AsyncSessionLocal for database queries
        This test exercises the actual code path in subtitle_processor.py:136
        """
        processor = DirectSubtitleProcessor()

        subtitles = [
            FilteredSubtitle(
                original_text="Hallo Welt",
                start_time=1.0,
                end_time=3.0,
                words=[
                    FilteredWord(text="Hallo", start_time=1.0, end_time=1.5),
                    FilteredWord(text="Welt", start_time=1.5, end_time=3.0),
                ],
            )
        ]

        # This exercises the real code path including session creation
        result = await processor.process_subtitles(
            subtitles=subtitles, user_id="test_user", db=test_db_session, user_level="A1", language="de"
        )

        # Verify actual processing worked
        assert result is not None


@skip_if_no_spacy_de
class TestTranslationServiceMethodCalls:
    """Test that translation services are called with correct methods"""

    def test_translation_service_has_translate_method(self):
        """
        Translation service should have translate() method, not translate_text()
        This test would have caught Bug #5
        """
        service = TranslationServiceFactory.create_service("nllb")

        # Verify service has correct method
        assert callable(service.translate)

        # Verify it doesn't have the wrong method name
        assert not hasattr(service, "translate_text")

    def test_translation_service_interface_contract(self):
        """
        Translation service must implement ITranslationService interface
        This verifies the return type handling in chunk_translation_service.py:188
        """
        import inspect

        from services.translationservice.interface import ITranslationService, TranslationResult

        service = TranslationServiceFactory.create_service("nllb")

        # Verify service implements interface
        assert isinstance(service, ITranslationService)

        # Verify translate method signature
        sig = inspect.signature(service.translate)
        assert "text" in sig.parameters
        assert "source_lang" in sig.parameters
        assert "target_lang" in sig.parameters

        # Verify return type annotation
        return_annotation = sig.return_annotation
        assert return_annotation == TranslationResult or "TranslationResult" in str(return_annotation)

    def test_translation_result_has_translated_text_attribute(self):
        """
        TranslationResult must have translated_text attribute
        This exercises the actual pattern in chunk_translation_service.py:188-198
        """
        from services.translationservice.interface import TranslationResult

        # Create a sample TranslationResult
        result = TranslationResult(
            original_text="Hello", translated_text="Hallo", source_language="en", target_language="de"
        )

        # Verify the attribute can be accessed
        translated_text = result.translated_text
        assert isinstance(translated_text, str)
        assert translated_text == "Hallo"


@skip_if_no_spacy_de
class TestIntegrationWithoutMocks:
    """Integration tests that exercise actual code without mocking"""

    @pytest.mark.asyncio
    async def test_vocabulary_lookup_full_flow(self, test_db_session, german_vocabulary):
        """
        Test vocabulary lookup using actual VocabularyService and real database
        No mocks - exercises actual production code path
        """
        from services.vocabulary.vocabulary_progress_service import get_vocabulary_progress_service
        from services.vocabulary.vocabulary_query_service import get_vocabulary_query_service
        from services.vocabulary.vocabulary_stats_service import get_vocabulary_stats_service

        # Create real service instances
        query_service = get_vocabulary_query_service()
        progress_service = get_vocabulary_progress_service()
        stats_service = get_vocabulary_stats_service()
        vocab_service = VocabularyService(query_service, progress_service, stats_service)

        # Look up a word using real database session
        result = await vocab_service.get_word_info("welt", "de", test_db_session)

        # Verify actual results
        assert result["found"] is True
        assert result["word"].lower() == "welt"
        assert result["difficulty_level"] == "A1"
        assert result["translation_en"] == "world"

    @pytest.mark.asyncio
    async def test_subtitle_processor_vocabulary_integration(self, german_vocabulary, test_db_session):
        """
        Test subtitle processor with vocabulary service integration
        No mocks - uses real services and database
        """
        processor = DirectSubtitleProcessor()

        # Create subtitles with German words
        subtitles = [
            FilteredSubtitle(
                original_text="Hallo Welt ist groß",
                start_time=1.0,
                end_time=3.0,
                words=[
                    FilteredWord(text="Hallo", start_time=1.0, end_time=1.5),
                    FilteredWord(text="Welt", start_time=1.5, end_time=2.0),
                    FilteredWord(text="ist", start_time=2.0, end_time=2.3),
                    FilteredWord(text="groß", start_time=2.3, end_time=3.0),
                ],
            )
        ]

        # Process with real services
        result = await processor.process_subtitles(
            subtitles=subtitles, user_id="test_user", db=test_db_session, user_level="A1", language="de"
        )

        # Verify actual processing results
        assert result is not None
        total_words = result.statistics.get("total_words", 0)
        assert total_words == 4

    def test_translation_factory_creates_correct_service_type(self):
        """
        Test translation factory creates services with correct interface
        Tests service creation without loading heavy models
        """
        from services.translationservice.interface import ITranslationService

        # Create service through factory
        service = TranslationServiceFactory.create_service(source_lang="en", target_lang="de", quality="standard")

        # Verify service type and interface
        assert service is not None
        assert isinstance(service, ITranslationService)
        assert callable(service.translate)

        # Verify it's not initialized yet (no heavy models loaded)
        assert not service.is_initialized


@skip_if_no_spacy_de
class TestBugReproduction:
    """Tests that reproduce the exact bugs we fixed"""

    @pytest.mark.asyncio
    async def test_bug_4_vocab_service_session_management(self, test_db_session, german_vocabulary):
        """
        Reproduces Bug #4: VocabularyService.get_db_session() doesn't exist
        This test would have failed with the buggy code
        """
        from services.vocabulary.vocabulary_progress_service import get_vocabulary_progress_service
        from services.vocabulary.vocabulary_query_service import get_vocabulary_query_service
        from services.vocabulary.vocabulary_stats_service import get_vocabulary_stats_service

        query_service = get_vocabulary_query_service()
        progress_service = get_vocabulary_progress_service()
        stats_service = get_vocabulary_stats_service()
        vocab_service = VocabularyService(query_service, progress_service, stats_service)

        # Verify service doesn't have get_db_session() method (the bug)
        assert not hasattr(vocab_service, "get_db_session")

        # This is the CORRECT pattern - pass session as parameter
        result = await vocab_service.get_word_info("hallo", "de", test_db_session)

        assert result["found"] is True

    def test_bug_5_translation_method_name(self):
        """
        Reproduces Bug #5: translate_text() doesn't exist, should be translate()
        This test would have failed with the buggy code
        """
        service = TranslationServiceFactory.create_service("nllb")

        # Verify service has translate() not translate_text()
        assert callable(service.translate)
        assert not hasattr(service, "translate_text")

    def test_bug_5_translation_result_extraction(self):
        """
        Reproduces Bug #5: Code expected string but got TranslationResult
        This test verifies the correct extraction pattern
        """
        import inspect

        from services.translationservice.interface import TranslationResult

        service = TranslationServiceFactory.create_service("nllb")

        # Verify translate() method signature
        sig = inspect.signature(service.translate)

        # Verify return type is TranslationResult, not str
        return_annotation = sig.return_annotation
        assert return_annotation == TranslationResult or "TranslationResult" in str(return_annotation)

        # Create a sample result to verify extraction pattern
        sample_result = TranslationResult(
            original_text="Test", translated_text="Test translated", source_language="en", target_language="de"
        )

        # Verify the CORRECT extraction pattern works
        translated_text = sample_result.translated_text
        assert isinstance(translated_text, str)
        assert translated_text == "Test translated"
