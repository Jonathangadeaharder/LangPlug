"""
Integration tests for VocabularyService with real database operations
Tests actual service boundaries without excessive mocking
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, VocabularyWord
from services.vocabulary.vocabulary_service import VocabularyService


@pytest.fixture
async def test_engine():
    """Create in-memory test database engine"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest.fixture
async def test_db_session(test_engine):
    """Create test database session with automatic rollback"""
    async_session = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session
        # Rollback happens automatically when exiting context


@pytest.fixture
async def sample_vocabulary(test_db_session: AsyncSession):
    """Insert sample vocabulary data"""
    words = [
        VocabularyWord(
            word="Haus",
            lemma="haus",
            language="de",
            difficulty_level="A1",
            part_of_speech="noun",
            gender="das",
            translation_en="house",
            translation_native="casa",
            frequency_rank=100,
        ),
        VocabularyWord(
            word="gehen",
            lemma="gehen",
            language="de",
            difficulty_level="A1",
            part_of_speech="verb",
            translation_en="to go",
            translation_native="ir",
            frequency_rank=50,
        ),
        VocabularyWord(
            word="schwierig",
            lemma="schwierig",
            language="de",
            difficulty_level="B2",
            part_of_speech="adjective",
            translation_en="difficult",
            translation_native="difícil",
            frequency_rank=500,
        ),
    ]

    for word in words:
        test_db_session.add(word)

    await test_db_session.commit()

    return words


class TestVocabularyServiceRealIntegration:
    """Test VocabularyService with actual database operations"""

    @pytest.mark.asyncio
    async def test_get_word_info_with_real_db(self, test_db_session, sample_vocabulary):
        """VocabularyService.get_word_info should query real database"""
        service = VocabularyService()

        # Test with existing word
        result = await service.get_word_info("Haus", "de", test_db_session)

        assert result is not None
        assert result["found"] is True
        assert result["word"].lower() == "haus"  # Check normalized
        assert result["difficulty_level"] == "A1"
        assert result["translation_en"] == "house"

    @pytest.mark.asyncio
    async def test_get_word_info_not_found(self, test_db_session, sample_vocabulary):
        """VocabularyService.get_word_info should return not found for missing words"""
        service = VocabularyService()

        result = await service.get_word_info("nonexistent", "de", test_db_session)

        assert result is not None
        assert result["found"] is False

    @pytest.mark.asyncio
    async def test_get_word_info_call_signature(self, test_db_session, sample_vocabulary):
        """
        Test exact call signature from subtitle_processor.py
        This reproduces the bug we just fixed
        """
        service = VocabularyService()

        # This was failing before: missing 'db' parameter
        # Correct call signature: word, language, db
        result = await service.get_word_info("gehen", "de", test_db_session)

        assert result is not None
        assert result["found"] is True
        assert result["word"].lower() == "gehen"

    @pytest.mark.asyncio
    async def test_get_vocabulary_library_with_real_db(self, test_db_session, sample_vocabulary):
        """VocabularyService.get_vocabulary_library should query real database"""
        service = VocabularyService()

        result = await service.get_vocabulary_library(db=test_db_session, language="de", level="A1", limit=10)

        assert result is not None
        assert "words" in result
        assert len(result["words"]) == 2  # Only A1 words
        assert result["total_count"] == 2

    @pytest.mark.asyncio
    async def test_service_instantiation_creates_instance(self):
        """VocabularyService should be instantiated as object, not used as class"""
        # This was the bug: passing VocabularyService instead of VocabularyService()
        service = VocabularyService()

        # Should be an instance, not a class
        assert not isinstance(service, type)
        assert hasattr(service, "get_word_info")
        assert callable(service.get_word_info)


class TestVocabularyServiceSubtitleProcessorScenario:
    """Test vocabulary service usage as it appears in subtitle_processor.py"""

    @pytest.mark.asyncio
    async def test_subtitle_processor_usage_pattern(self, test_db_session, sample_vocabulary):
        """
        Reproduce exact usage pattern from subtitle_processor.py lines 134-137
        This is the pattern that was failing before the fix
        """
        # Create service (was incorrectly stored as class)
        vocab_service = VocabularyService()  # Fixed: instantiate it

        # Simulate processing a word from subtitle
        word_text = "haus"
        language = "de"

        # Correct pattern: service takes db session as parameter
        word_info = await vocab_service.get_word_info(word_text, language, test_db_session)

        assert word_info is not None
        assert word_info["found"] is True

    @pytest.mark.asyncio
    async def test_multiple_word_lookups_same_session(self, test_db_session, sample_vocabulary):
        """Service should handle multiple lookups in same session efficiently"""
        vocab_service = VocabularyService()
        words_to_lookup = ["haus", "gehen", "schwierig"]

        results = []
        for word in words_to_lookup:
            result = await vocab_service.get_word_info(word, "de", test_db_session)
            results.append(result)

        # All should succeed
        assert len(results) == 3
        assert all(r["found"] for r in results)


class TestVocabularyServiceIntegrationBoundaries:
    """Test service boundaries and integration points"""

    @pytest.mark.asyncio
    async def test_service_query_delegation(self, test_db_session, sample_vocabulary):
        """VocabularyService should properly delegate to query_service"""
        service = VocabularyService()

        # Service should have query_service
        assert hasattr(service, "query_service")
        assert service.query_service is not None

        # Query should work through delegation
        result = await service.get_word_info("Haus", "de", test_db_session)
        assert result["found"] is True

    @pytest.mark.asyncio
    async def test_service_handles_different_languages(self, test_db_session):
        """Service should handle queries for different languages"""
        service = VocabularyService()

        # Add words in different languages
        words = [
            VocabularyWord(word="hello", lemma="hello", language="en", difficulty_level="A1"),
            VocabularyWord(word="hola", lemma="hola", language="es", difficulty_level="A1"),
            VocabularyWord(word="bonjour", lemma="bonjour", language="fr", difficulty_level="A1"),
        ]

        for word in words:
            test_db_session.add(word)
        await test_db_session.commit()

        # Query each language
        for lang, word in [("en", "hello"), ("es", "hola"), ("fr", "bonjour")]:
            result = await service.get_word_info(word, lang, test_db_session)
            assert result["found"] is True
            assert result["word"].lower() == word.lower()
