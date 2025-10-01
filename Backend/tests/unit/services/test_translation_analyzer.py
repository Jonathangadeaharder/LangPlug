"""
Test suite for TranslationAnalyzer
Tests translation analysis and re-filtering functionality
"""

from unittest.mock import AsyncMock, Mock

import pytest

from services.filtering.translation_analyzer import TranslationAnalyzer


class TestTranslationAnalyzer:
    """Test TranslationAnalyzer functionality"""

    def test_initialization_with_processor(self):
        """Test service initialization with custom subtitle processor"""
        mock_processor = Mock()
        service = TranslationAnalyzer(mock_processor)
        assert service.subtitle_processor == mock_processor

    @pytest.fixture
    def service(self):
        return TranslationAnalyzer()


class TestRefilterForTranslations:
    """Test re-filtering for translations functionality"""

    @pytest.fixture
    def service(self):
        return TranslationAnalyzer()

    async def test_refilter_for_translations_success(self, service):
        """Test successful re-filtering for translations"""
        # Setup
        srt_path = "/path/to/test.srt"
        user_id = "user123"
        known_words = ["der", "die", "das"]
        user_level = "A1"
        target_language = "de"

        # Mock original filtering result
        mock_blocker1 = Mock()
        mock_blocker1.word = "der"  # Known word

        mock_blocker2 = Mock()
        mock_blocker2.word = "haus"  # Unknown word

        mock_blocker3 = Mock()
        mock_blocker3.word = "auto"  # Unknown word

        mock_filtering_result = Mock()
        mock_filtering_result.blocker_words = [mock_blocker1, mock_blocker2, mock_blocker3]
        mock_filtering_result.filtered_subtitles = []

        service.subtitle_processor.process_subtitles = AsyncMock(return_value=mock_filtering_result)

        # Execute
        result = await service.refilter_for_translations(srt_path, user_id, known_words, user_level, target_language)

        # Assert
        assert result["total_subtitles"] == 0
        assert result["original_blockers"] == 3
        assert result["known_blockers"] == 1  # "der" is known
        assert result["unknown_blockers"] == 2  # "haus" and "auto" are unknown
        assert result["filtering_stats"]["translation_reduction"] == 33.3  # 1/3 * 100

    async def test_refilter_for_translations_no_original_result(self, service):
        """Test re-filtering when no original filtering results"""
        # Setup
        srt_path = "/path/to/test.srt"
        user_id = "user123"
        known_words = ["der"]

        # Mock empty filtering result
        service.subtitle_processor.process_subtitles = AsyncMock(return_value=None)

        # Execute
        result = await service.refilter_for_translations(srt_path, user_id, known_words, "A1", "de")

        # Assert - should return empty result structure
        assert result["total_subtitles"] == 0
        assert result["original_blockers"] == 0
        assert result["known_blockers"] == 0
        assert result["unknown_blockers"] == 0

    async def test_refilter_for_translations_processing_error(self, service):
        """Test re-filtering with processing error"""
        # Setup
        srt_path = "/path/to/test.srt"
        user_id = "user123"
        known_words = ["der"]

        # Mock subtitle processor to raise exception
        service.subtitle_processor.process_subtitles = AsyncMock(side_effect=Exception("Processing error"))

        # Execute
        result = await service.refilter_for_translations(srt_path, user_id, known_words, "A1", "de")

        # Assert - should return empty result structure on error
        assert result["total_subtitles"] == 0
        assert result["translation_count"] == 0


class TestAnalyzeTranslationNeeds:
    """Test translation needs analysis functionality"""

    @pytest.fixture
    def service(self):
        return TranslationAnalyzer()

    def test_analyze_translation_needs_success(self, service):
        """Test successful translation needs analysis"""
        # Setup
        mock_filtered_word1 = Mock()
        mock_filtered_word1.word = "haus"

        mock_filtered_word2 = Mock()
        mock_filtered_word2.word = "auto"

        mock_subtitle1 = Mock()
        mock_subtitle1.filtered_words = [mock_filtered_word1, mock_filtered_word2]

        mock_subtitle2 = Mock()
        mock_subtitle2.filtered_words = [mock_filtered_word1]

        filtered_subtitles = [mock_subtitle1, mock_subtitle2]
        unknown_blockers = [Mock(word="haus"), Mock(word="auto")]
        known_blockers = []

        # Execute
        result = service._analyze_translation_needs(filtered_subtitles, unknown_blockers, known_blockers)

        # Assert
        assert result["subtitles_needing_translation"] == 2
        assert result["total_subtitles"] == 2
        assert result["translation_percentage"] == 100.0

    def test_analyze_translation_needs_empty(self, service):
        """Test translation needs analysis with empty data"""
        result = service._analyze_translation_needs([], [], [])

        assert result["subtitles_needing_translation"] == 0
        assert result["total_subtitles"] == 0
        assert result["translation_percentage"] == 0
        assert result["average_unknown_words_per_subtitle"] == 0


class TestBuildTranslationSegments:
    """Test translation segments building functionality"""

    @pytest.fixture
    def service(self):
        return TranslationAnalyzer()

    def test_build_translation_segments_success(self, service):
        """Test successful translation segments building"""
        # Setup
        mock_filtered_word = Mock()
        mock_filtered_word.word = "haus"
        mock_filtered_word.lemma = "haus"
        mock_filtered_word.pos = "noun"
        mock_filtered_word.difficulty = "A1"

        mock_subtitle = Mock()
        mock_subtitle.index = 1
        mock_subtitle.start_time = "00:00:01,000"
        mock_subtitle.end_time = "00:00:03,000"
        mock_subtitle.text = "Das ist ein Haus"
        mock_subtitle.filtered_words = [mock_filtered_word]

        filtered_subtitles = [mock_subtitle]
        unknown_blockers = [Mock(word="haus")]

        # Execute
        result = service._build_translation_segments(filtered_subtitles, unknown_blockers)

        # Assert
        assert len(result) == 1
        segment = result[0]
        assert segment["subtitle_index"] == 1
        assert segment["text"] == "Das ist ein Haus"
        assert len(segment["unknown_words"]) == 1
        assert segment["unknown_words"][0]["word"] == "haus"

    def test_build_translation_segments_no_unknown_words(self, service):
        """Test translation segments building with no unknown words"""
        # Setup - subtitle with no unknown words
        mock_subtitle = Mock()
        mock_subtitle.filtered_words = []

        filtered_subtitles = [mock_subtitle]
        unknown_blockers = []

        # Execute
        result = service._build_translation_segments(filtered_subtitles, unknown_blockers)

        # Assert
        assert result == []


class TestAnalyzeTranslationComplexity:
    """Test translation complexity analysis functionality"""

    @pytest.fixture
    def service(self):
        return TranslationAnalyzer()

    async def test_analyze_translation_complexity(self, service):
        """Test translation complexity analysis"""
        srt_path = "/path/to/test.srt"
        user_level = "A1"
        target_language = "de"

        result = await service.analyze_translation_complexity(srt_path, user_level, target_language)

        # Assert - should return basic analysis structure
        assert "overall_difficulty" in result
        assert "vocabulary_density" in result
        assert "recommended_level" in result
        assert "complexity_score" in result
        assert "content_type" in result
        assert result["recommended_level"] == user_level


class TestHealthCheck:
    """Test health check functionality"""

    @pytest.fixture
    def service(self):
        return TranslationAnalyzer()

    async def test_health_check(self, service):
        """Test service health check"""
        result = await service.health_check()

        assert result["service"] == "TranslationAnalyzer"
        assert result["status"] == "healthy"
        assert result["subtitle_processor"] == "available"
