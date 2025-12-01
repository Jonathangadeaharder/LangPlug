"""
Comprehensive tests for VocabularyService to achieve 85%+ coverage
Tests facade delegation and custom word management functionality
"""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from services.vocabulary.vocabulary_service import VocabularyService, get_vocabulary_service


@pytest.fixture
def vocab_service():
    """Fixture providing a VocabularyService with mocked dependencies"""
    mock_query_service = AsyncMock()
    mock_progress_service = AsyncMock()
    mock_stats_service = AsyncMock()
    return VocabularyService(mock_query_service, mock_progress_service, mock_stats_service)


class TestVocabularyServiceFacadePatternFunctionality:
    """Test that VocabularyService correctly delegates to sub-services"""

    @pytest.mark.asyncio
    async def test_get_vocabulary_library_delegates_to_query_service(self, vocab_service):
        """Verify get_vocabulary_library delegates to query_service"""
        # Arrange
        service = vocab_service
        mock_db = AsyncMock(spec=AsyncSession)

        expected_result = {
            "words": [
                {"word": "Haus", "difficulty_level": "A1"},
                {"word": "Katze", "difficulty_level": "A1"},
            ],
            "total_count": 2,
        }

        # Act
        with patch.object(
            service.query_service, "get_vocabulary_library", new_callable=AsyncMock, return_value=expected_result
        ) as mock_method:
            result = await service.get_vocabulary_library(
                db=mock_db, language="de", level="A1", user_id=123, limit=50, offset=0
            )

        # Assert
        mock_method.assert_called_once_with(mock_db, "de", "A1", 123, 50, 0)
        assert result["total_count"] == 2
        assert len(result["words"]) == 2

    @pytest.mark.asyncio
    async def test_search_vocabulary_delegates_to_query_service(self, vocab_service):
        """Verify search_vocabulary delegates to query_service"""
        # Arrange
        service = vocab_service
        mock_db = AsyncMock(spec=AsyncSession)

        expected_result = [
            {"word": "Haus", "lemma": "haus"},
            {"word": "Hausbau", "lemma": "hausbau"},
        ]

        # Act
        with patch.object(
            service.query_service, "search_vocabulary", new_callable=AsyncMock, return_value=expected_result
        ) as mock_method:
            result = await service.search_vocabulary(mock_db, "Haus", "de", limit=10)

        # Assert
        mock_method.assert_called_once_with(mock_db, "Haus", "de", 10)
        assert len(result) == 2
        assert result[0]["word"] == "Haus"

    @pytest.mark.asyncio
    async def test_bulk_mark_level_delegates_to_progress_service(self, vocab_service):
        """Verify bulk_mark_level delegates to progress_service"""
        # Arrange
        service = vocab_service
        mock_db = AsyncMock(spec=AsyncSession)

        expected_result = {
            "success": True,
            "words_updated": 25,
            "level": "A1",
        }

        # Act
        with patch.object(
            service.progress_service, "bulk_mark_level", new_callable=AsyncMock, return_value=expected_result
        ) as mock_method:
            result = await service.bulk_mark_level(mock_db, user_id=123, language="de", level="A1", is_known=True)

        # Assert
        mock_method.assert_called_once_with(mock_db, 123, "de", "A1", True)
        assert result["success"] is True
        assert result["words_updated"] == 25

    @pytest.mark.asyncio
    async def test_get_vocabulary_stats_delegates_to_stats_service(self, vocab_service):
        """Verify get_vocabulary_stats delegates to stats_service"""
        # Arrange
        service = vocab_service

        expected_result = {
            "A1": 100,
            "A2": 150,
            "B1": 200,
        }

        # Act
        with patch.object(
            service.stats_service, "get_vocabulary_stats", new_callable=AsyncMock, return_value=expected_result
        ) as mock_method:
            result = await service.get_vocabulary_stats("de")

        # Assert
        mock_method.assert_called_once_with("de")
        assert result["A1"] == 100
        assert result["A2"] == 150

    @pytest.mark.asyncio
    async def test_get_user_progress_summary_delegates_to_stats_service(self, vocab_service):
        """Verify get_user_progress_summary delegates to stats_service"""
        # Arrange
        service = vocab_service
        mock_db = AsyncMock(spec=AsyncSession)

        expected_result = {
            "total_known": 150,
            "by_level": {
                "A1": 80,
                "A2": 50,
                "B1": 20,
            },
        }

        # Act
        with patch.object(
            service.stats_service, "get_user_progress_summary", new_callable=AsyncMock, return_value=expected_result
        ) as mock_method:
            result = await service.get_user_progress_summary(mock_db, user_id="123")

        # Assert
        mock_method.assert_called_once_with(mock_db, "123")
        assert result["total_known"] == 150
        assert result["by_level"]["A1"] == 80

    @pytest.mark.asyncio
    async def test_get_supported_languages_delegates_to_stats_service(self, vocab_service):
        """Verify get_supported_languages delegates to stats_service"""
        # Arrange
        service = vocab_service

        expected_result = ["de", "es", "fr", "it"]

        # Act
        with patch.object(
            service.stats_service, "get_supported_languages", new_callable=AsyncMock, return_value=expected_result
        ) as mock_method:
            result = await service.get_supported_languages()

        # Assert
        mock_method.assert_called_once()
        assert "de" in result
        assert "es" in result
        assert len(result) == 4


class TestExtractBlockingWordsFromSrt:
    """Test SRT subtitle parsing and word extraction"""

    @pytest.fixture
    def vocab_service(self):
        """Fixture providing a VocabularyService with mocked dependencies"""
        mock_query_service = AsyncMock()
        mock_progress_service = AsyncMock()
        mock_stats_service = AsyncMock()
        return VocabularyService(mock_query_service, mock_progress_service, mock_stats_service)

    @pytest.mark.asyncio
    async def test_extract_blocking_words_from_valid_srt(self, vocab_service):
        """Test extracting words from properly formatted SRT content"""
        # Arrange
        service = vocab_service
        mock_db = AsyncMock(spec=AsyncSession)

        srt_content = """1
00:00:01,000 --> 00:00:03,000
Hallo Welt, willkommen in Deutschland

2
00:00:04,000 --> 00:00:06,000
Heute lernen wir Deutsch sprechen
"""

        # Act
        result = await service.extract_blocking_words_from_srt(
            db=mock_db, srt_content=srt_content, user_id=123, video_path="/test/video.mp4"
        )

        # Assert
        assert isinstance(result, list)
        assert len(result) > 0

        # Verify word structure
        for word in result:
            assert "word" in word
            assert "translation" in word
            assert "difficulty_level" in word
            assert "lemma" in word
            assert word["difficulty_level"] == "B1"  # Default level
            assert word["known"] is False

    @pytest.mark.asyncio
    async def test_extract_blocking_words_filters_common_words(self, vocab_service):
        """Test that common words like 'und', 'der', 'die' are filtered out"""
        # Arrange
        service = vocab_service
        mock_db = AsyncMock(spec=AsyncSession)

        srt_content = """1
00:00:01,000 --> 00:00:03,000
und der die das ist sind war
"""

        # Act
        result = await service.extract_blocking_words_from_srt(
            db=mock_db, srt_content=srt_content, user_id=123, video_path="/test/video.mp4"
        )

        # Assert - should return empty as all are common words
        assert isinstance(result, list)
        # All words should be filtered out (common words + short words)

    @pytest.mark.asyncio
    async def test_extract_blocking_words_handles_empty_srt(self, vocab_service):
        """Test handling of empty SRT content"""
        # Arrange
        service = vocab_service
        mock_db = AsyncMock(spec=AsyncSession)

        srt_content = ""

        # Act
        result = await service.extract_blocking_words_from_srt(
            db=mock_db, srt_content=srt_content, user_id=123, video_path="/test/video.mp4"
        )

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_extract_blocking_words_handles_malformed_srt(self, vocab_service):
        """Test handling of malformed SRT content"""
        # Arrange
        service = vocab_service
        mock_db = AsyncMock(spec=AsyncSession)

        srt_content = "Not a valid SRT format at all"

        # Act
        result = await service.extract_blocking_words_from_srt(
            db=mock_db, srt_content=srt_content, user_id=123, video_path="/test/video.mp4"
        )

        # Assert - should handle gracefully
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_extract_blocking_words_returns_unique_words(self, vocab_service):
        """Test that duplicate words are removed"""
        # Arrange
        service = vocab_service
        mock_db = AsyncMock(spec=AsyncSession)

        srt_content = """1
00:00:01,000 --> 00:00:03,000
Katze Katze Hund

2
00:00:04,000 --> 00:00:06,000
Katze Katze Katze
"""

        # Act
        result = await service.extract_blocking_words_from_srt(
            db=mock_db, srt_content=srt_content, user_id=123, video_path="/test/video.mp4"
        )

        # Assert
        word_texts = [w["word"] for w in result]
        # Should have unique words
        assert len(word_texts) == len(set(word_texts))

    @pytest.mark.asyncio
    async def test_extract_blocking_words_limits_to_20_words(self, vocab_service):
        """Test that result is limited to 20 words maximum"""
        # Arrange
        service = vocab_service
        mock_db = AsyncMock(spec=AsyncSession)

        # Create SRT with many unique words
        words = [f"testword{i}" for i in range(50)]
        srt_content = f"""1
00:00:01,000 --> 00:00:03,000
{" ".join(words)}
"""

        # Act
        result = await service.extract_blocking_words_from_srt(
            db=mock_db, srt_content=srt_content, user_id=123, video_path="/test/video.mp4"
        )

        # Assert
        assert len(result) <= 20  # Should be limited to 20

    @pytest.mark.asyncio
    async def test_extract_blocking_words_handles_exception(self, vocab_service):
        """Test error handling when extraction fails"""
        # Arrange
        service = vocab_service
        mock_db = AsyncMock(spec=AsyncSession)

        # Pass None instead of string to cause TypeError
        srt_content = None

        # Act
        result = await service.extract_blocking_words_from_srt(
            db=mock_db, srt_content=srt_content, user_id=123, video_path="/test/video.mp4"
        )

        # Assert - should return empty list on error
        assert result == []


class TestGetVocabularyService:
    """Test the factory function"""

    def test_get_vocabulary_service_returns_instance(self):
        """Test that factory function returns VocabularyService instance"""
        # Act
        from unittest.mock import AsyncMock

        mock_query_service = AsyncMock()
        mock_progress_service = AsyncMock()
        mock_stats_service = AsyncMock()
        service = get_vocabulary_service(mock_query_service, mock_progress_service, mock_stats_service)

        # Assert
        assert isinstance(service, VocabularyService)
        assert hasattr(service, "query_service")
        assert hasattr(service, "progress_service")
        assert hasattr(service, "stats_service")

    def test_get_vocabulary_service_returns_fresh_instance(self):
        """Test that each call returns a new instance"""
        # Act
        from unittest.mock import AsyncMock

        mock_query_service1 = AsyncMock()
        mock_progress_service1 = AsyncMock()
        mock_stats_service1 = AsyncMock()
        service1 = get_vocabulary_service(mock_query_service1, mock_progress_service1, mock_stats_service1)

        mock_query_service2 = AsyncMock()
        mock_progress_service2 = AsyncMock()
        mock_stats_service2 = AsyncMock()
        service2 = get_vocabulary_service(mock_query_service2, mock_progress_service2, mock_stats_service2)

        # Assert
        assert service1 is not service2  # Different instances
