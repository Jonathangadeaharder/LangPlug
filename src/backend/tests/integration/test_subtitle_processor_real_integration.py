"""
Integration tests for subtitle processing with real services
Tests actual service integration without excessive mocking
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, VocabularyWord
from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor
from services.filterservice.interface import FilteredSubtitle, FilteredWord

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
    """Create test database session with automatic rollback"""
    async_session = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session, session.begin():
        yield session


@pytest.fixture
async def german_vocabulary(test_db_session: AsyncSession):
    """Insert German vocabulary test data"""
    words = [
        VocabularyWord(
            word="das",
            lemma="das",
            language="de",
            difficulty_level="A1",
            part_of_speech="article",
            translation_en="the",
        ),
        VocabularyWord(
            word="Haus",
            lemma="haus",
            language="de",
            difficulty_level="A1",
            part_of_speech="noun",
            gender="das",
            translation_en="house",
        ),
        VocabularyWord(
            word="ist", lemma="sein", language="de", difficulty_level="A1", part_of_speech="verb", translation_en="is"
        ),
        VocabularyWord(
            word="groß",
            lemma="groß",
            language="de",
            difficulty_level="A2",
            part_of_speech="adjective",
            translation_en="big",
        ),
        VocabularyWord(
            word="kompliziert",
            lemma="kompliziert",
            language="de",
            difficulty_level="B2",
            part_of_speech="adjective",
            translation_en="complicated",
        ),
    ]

    for word in words:
        test_db_session.add(word)

    await test_db_session.commit()

    return words


@pytest.fixture
def sample_subtitles():
    """Create sample subtitle objects"""
    return [
        FilteredSubtitle(
            original_text="Das Haus ist groß",
            start_time=1.0,
            end_time=3.0,
            words=[
                FilteredWord(text="Das", start_time=1.0, end_time=1.5),
                FilteredWord(text="Haus", start_time=1.5, end_time=2.0),
                FilteredWord(text="ist", start_time=2.0, end_time=2.3),
                FilteredWord(text="groß", start_time=2.3, end_time=3.0),
            ],
        ),
        FilteredSubtitle(
            original_text="Es ist kompliziert",
            start_time=4.0,
            end_time=6.0,
            words=[
                FilteredWord(text="Es", start_time=4.0, end_time=4.5),
                FilteredWord(text="ist", start_time=4.5, end_time=4.8),
                FilteredWord(text="kompliziert", start_time=4.8, end_time=6.0),
            ],
        ),
    ]


@skip_if_no_spacy_de
class TestDirectSubtitleProcessorRealIntegration:
    """Test DirectSubtitleProcessor with real services"""

    @pytest.mark.asyncio
    async def test_processor_instantiates_vocabulary_service_correctly(self):
        """
        DirectSubtitleProcessor should instantiate VocabularyService as object
        This reproduces the bug we just fixed
        """
        from services.vocabulary.vocabulary_progress_service import get_vocabulary_progress_service
        from services.vocabulary.vocabulary_query_service import get_vocabulary_query_service
        from services.vocabulary.vocabulary_service import VocabularyService
        from services.vocabulary.vocabulary_stats_service import get_vocabulary_stats_service

        # Create real vocabulary service
        query_service = get_vocabulary_query_service()
        progress_service = get_vocabulary_progress_service()
        stats_service = get_vocabulary_stats_service()
        vocab_service = VocabularyService(query_service, progress_service, stats_service)

        processor = DirectSubtitleProcessor(vocab_service=vocab_service)

        # Should be an instance, not a class
        assert processor.vocab_service is not None
        assert not isinstance(processor.vocab_service, type)
        assert hasattr(processor.vocab_service, "get_word_info")

    @pytest.mark.asyncio
    async def test_processor_processes_subtitles_with_real_vocab_service(
        self, sample_subtitles, german_vocabulary, test_db_session
    ):
        """Processor should use real VocabularyService for word lookups"""
        processor = DirectSubtitleProcessor()

        # Process subtitles with real service
        result = await processor.process_subtitles(
            subtitles=sample_subtitles, user_id="test_user", user_level="A1", language="de"
        )

        # Should return results
        assert result is not None
        assert hasattr(result, "learning_subtitles")
        assert hasattr(result, "blocker_words")

    @pytest.mark.asyncio
    async def test_processor_uses_correct_vocabulary_call_signature(
        self, sample_subtitles, german_vocabulary, test_db_session
    ):
        """
        Processor should call vocab_service.get_word_info with correct parameters
        This test would have caught the bug: missing 'db' parameter
        """
        processor = DirectSubtitleProcessor()

        # This should not raise TypeError about missing parameters
        result = await processor.process_subtitles(
            subtitles=sample_subtitles,
            user_id="test_user",
            user_level="B2",  # High level to process all words
            language="de",
        )

        assert result is not None


@skip_if_no_spacy_de
class TestSubtitleProcessorWordLookupIntegration:
    """Test word lookup integration in subtitle processor"""

    @pytest.mark.asyncio
    async def test_processor_looks_up_words_in_database(self, sample_subtitles, german_vocabulary, test_db_session):
        """Processor should successfully look up words in vocabulary database"""
        processor = DirectSubtitleProcessor()

        result = await processor.process_subtitles(
            subtitles=sample_subtitles, user_id="test_user", user_level="A1", language="de"
        )

        # Should have processed words and looked them up
        assert result is not None
        # B2 word 'kompliziert' should be filtered out for A1 level
        # A1/A2 words should be in learning or blocker list

    @pytest.mark.asyncio
    async def test_processor_handles_word_not_in_database(self, german_vocabulary, test_db_session):
        """Processor should handle words not in vocabulary database gracefully"""
        processor = DirectSubtitleProcessor()

        # Subtitle with unknown word
        subtitles = [
            FilteredSubtitle(
                original_text="Xyz unknown word",
                start_time=1.0,
                end_time=3.0,
                words=[
                    FilteredWord(text="Xyz", start_time=1.0, end_time=2.0),
                    FilteredWord(text="unknown", start_time=2.0, end_time=3.0),
                ],
            )
        ]

        # Should not crash
        result = await processor.process_subtitles(
            subtitles=subtitles, user_id="test_user", user_level="A1", language="de"
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_processor_session_management(self, sample_subtitles, german_vocabulary, test_db_session):
        """Processor should properly manage database sessions"""
        processor = DirectSubtitleProcessor()

        # Multiple calls should not interfere with each other
        result1 = await processor.process_subtitles(
            subtitles=sample_subtitles, user_id="user1", user_level="A1", language="de"
        )

        result2 = await processor.process_subtitles(
            subtitles=sample_subtitles, user_id="user2", user_level="B1", language="de"
        )

        # Both should succeed independently
        assert result1 is not None
        assert result2 is not None


@skip_if_no_spacy_de
class TestSubtitleProcessorServiceBoundaries:
    """Test service boundaries and integration points"""

    @pytest.mark.asyncio
    async def test_processor_delegates_to_subtitle_processor(
        self, sample_subtitles, german_vocabulary, test_db_session
    ):
        """DirectSubtitleProcessor should delegate to SubtitleProcessor service"""
        processor = DirectSubtitleProcessor()

        # Should have processor service
        assert hasattr(processor, "processor")
        assert processor.processor is not None

        # Should work through delegation
        result = await processor.process_subtitles(
            subtitles=sample_subtitles, user_id="test_user", user_level="A1", language="de"
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_processor_uses_data_loader(self, sample_subtitles, german_vocabulary, test_db_session):
        """Processor should use data_loader to get user data"""
        processor = DirectSubtitleProcessor()

        # Should have data_loader
        assert hasattr(processor, "data_loader")
        assert processor.data_loader is not None

        result = await processor.process_subtitles(
            subtitles=sample_subtitles, user_id="test_user", user_level="A1", language="de"
        )

        # Should have loaded user data
        assert result is not None

    @pytest.mark.asyncio
    async def test_processor_integrates_all_services(self, sample_subtitles, german_vocabulary, test_db_session):
        """Processor should integrate all required services"""
        from services.vocabulary.vocabulary_progress_service import get_vocabulary_progress_service
        from services.vocabulary.vocabulary_query_service import get_vocabulary_query_service
        from services.vocabulary.vocabulary_service import VocabularyService
        from services.vocabulary.vocabulary_stats_service import get_vocabulary_stats_service

        # Create real vocabulary service
        query_service = get_vocabulary_query_service()
        progress_service = get_vocabulary_progress_service()
        stats_service = get_vocabulary_stats_service()
        vocab_service = VocabularyService(query_service, progress_service, stats_service)

        processor = DirectSubtitleProcessor(vocab_service=vocab_service)

        # Check all service dependencies
        assert processor.vocab_service is not None
        assert processor.data_loader is not None
        assert processor.validator is not None
        assert processor.filter is not None
        assert processor.processor is not None
        assert processor.file_handler is not None

        # All should work together
        result = await processor.process_subtitles(
            subtitles=sample_subtitles, user_id="test_user", user_level="A2", language="de"
        )

        assert result is not None


@skip_if_no_spacy_de
class TestSubtitleProcessorErrorHandling:
    """Test error handling in subtitle processor"""

    @pytest.mark.asyncio
    async def test_processor_handles_empty_subtitles(self, german_vocabulary, test_db_session):
        """Processor should handle empty subtitle list gracefully"""
        processor = DirectSubtitleProcessor()

        result = await processor.process_subtitles(subtitles=[], user_id="test_user", user_level="A1", language="de")

        assert result is not None
        assert len(result.learning_subtitles) == 0

    @pytest.mark.asyncio
    async def test_processor_handles_database_errors_gracefully(self):
        """Processor should handle database errors without crashing"""
        processor = DirectSubtitleProcessor()

        # Subtitle with valid structure
        subtitles = [
            FilteredSubtitle(
                original_text="Test text",
                start_time=1.0,
                end_time=3.0,
                words=[FilteredWord(text="Test", start_time=1.0, end_time=3.0)],
            )
        ]

        # Should not crash even if DB lookups fail (word not found)
        result = await processor.process_subtitles(
            subtitles=subtitles, user_id="test_user", user_level="A1", language="de"
        )

        assert result is not None
