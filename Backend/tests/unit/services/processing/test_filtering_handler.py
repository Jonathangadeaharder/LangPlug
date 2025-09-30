"""
Unit tests for FilteringHandler facade
Tests public API behavior - delegates to focused sub-services

NOTE: Private methods moved to sub-services in services/processing/filtering/
These should be tested in their respective sub-service test files.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from pathlib import Path
import json

from services.processing.filtering_handler import FilteringHandler
from services.filterservice.interface import FilteredSubtitle, FilteredWord, FilteringResult, WordStatus
from api.models.processing import VocabularyWord


class TestFilteringHandlerInitialization:
    """Test service initialization"""

    def test_initialization_with_processor(self):
        """Test service initializes with provided processor"""
        mock_processor = Mock()

        handler = FilteringHandler(mock_processor)

        assert handler.subtitle_processor == mock_processor

    def test_initialization_without_processor(self):
        """Test service initializes with default processor"""
        handler = FilteringHandler()

        assert handler.subtitle_processor is not None


class TestHealthCheck:
    """Test health check functionality"""

    @pytest.fixture
    def handler(self):
        return FilteringHandler()

    @pytest.mark.anyio
    async def test_health_check(self, handler):
        """Test service health check"""
        result = await handler.health_check()

        assert result["service"] == "FilteringHandler"
        assert result["status"] == "healthy"
        assert result["subtitle_processor"] == "available"


class TestValidateParameters:
    """Test parameter validation"""

    @pytest.fixture
    def handler(self):
        return FilteringHandler()

    def test_validate_parameters_all_present(self, handler):
        """Test validation with all required parameters"""
        result = handler.validate_parameters(
            srt_path="/path/to/file.srt",
            user_id="user123"
        )

        assert result is True

    def test_validate_parameters_missing_srt_path(self, handler):
        """Test validation with missing srt_path"""
        result = handler.validate_parameters(user_id="user123")

        assert result is False

    def test_validate_parameters_missing_user_id(self, handler):
        """Test validation with missing user_id"""
        result = handler.validate_parameters(srt_path="/path/to/file.srt")

        assert result is False

    def test_validate_parameters_extra_params_ok(self, handler):
        """Test validation ignores extra parameters"""
        result = handler.validate_parameters(
            srt_path="/path/to/file.srt",
            user_id="user123",
            extra_param="ignored"
        )

        assert result is True


class TestHandle:
    """Test handle method delegates to filter_subtitles"""

    @pytest.fixture
    def handler(self):
        return FilteringHandler()

    @pytest.mark.anyio
    async def test_handle_delegates_to_filter_subtitles(self, handler):
        """Test handle method delegates to filter_subtitles"""
        # Arrange
        expected_result = {"status": "success"}

        with patch.object(handler, 'filter_subtitles', new_callable=AsyncMock, return_value=expected_result):
            # Act
            result = await handler.handle(
                task_id="test_task",
                task_progress={},
                srt_path="/path/to/file.srt",
                user_id="user123",
                user_level="A1",
                target_language="de"
            )

            # Assert - handle returns None but delegates correctly
            handler.filter_subtitles.assert_called_once()



class TestExtractBlockingWords:
    """Test extracting blocking words - facade delegation test"""

    @pytest.fixture
    def handler(self):
        return FilteringHandler()

    @pytest.mark.anyio
    async def test_extract_blocking_words(self, handler):
        """Test extracting blocking vocabulary words"""
        # Arrange
        expected_vocab = [
            VocabularyWord(
                concept_id="123e4567-e89b-12d3-a456-426614174000",
                word="schwierig",
                translation="difficult",
                difficulty_level="B2",
                known=False
            )
        ]

        with patch.object(handler.coordinator, 'extract_blocking_words', new_callable=AsyncMock, return_value=expected_vocab):
            # Act
            result = await handler.extract_blocking_words(
                srt_path="/path/to/file.srt",
                user_id="user123",
                user_level="A1"
            )

            # Assert
            assert len(result) == 1
            assert result[0].word == "schwierig"
            assert result[0].difficulty_level == "B2"
            handler.coordinator.extract_blocking_words.assert_called_once()


class TestRefilterForTranslations:
    """Test refiltering for translations - facade delegation test"""

    @pytest.fixture
    def handler(self):
        return FilteringHandler()

    @pytest.mark.anyio
    async def test_refilter_for_translations(self, handler):
        """Test refiltering after user marks words as known"""
        # Arrange
        expected_result = {
            "total_subtitles": 10,
            "translation_count": 5,
            "needs_translation": [0, 2, 4, 6, 8]
        }

        with patch.object(handler.coordinator, 'refilter_for_translations', new_callable=AsyncMock, return_value=expected_result):
            # Act
            result = await handler.refilter_for_translations(
                srt_path="/path/to/file.srt",
                user_id="user123",
                known_words=["hund", "katze"],
                user_level="A1",
                target_language="de"
            )

            # Assert
            assert result["total_subtitles"] == 10
            assert result["translation_count"] == 5
            assert len(result["needs_translation"]) == 5
            handler.coordinator.refilter_for_translations.assert_called_once()

    @pytest.mark.anyio
    async def test_refilter_for_translations_all_known(self, handler):
        """Test refiltering when all blocking words are known"""
        # Arrange
        expected_result = {
            "total_subtitles": 10,
            "translation_count": 0,
            "needs_translation": []
        }

        with patch.object(handler.coordinator, 'refilter_for_translations', new_callable=AsyncMock, return_value=expected_result):
            # Act
            result = await handler.refilter_for_translations(
                srt_path="/path/to/file.srt",
                user_id="user123",
                known_words=["all", "blocking", "words"],
                user_level="A1",
                target_language="de"
            )

            # Assert
            assert result["translation_count"] == 0
            assert len(result["needs_translation"]) == 0


class TestEstimateDuration:
    """Test duration estimation"""

    @pytest.fixture
    def handler(self):
        return FilteringHandler()

    def test_estimate_duration(self, handler):
        """Test estimating task duration - delegates to loader"""
        # Arrange
        with patch.object(handler.loader, 'estimate_duration', return_value=120):
            # Act
            result = handler.estimate_duration("/path/to/file.srt")

            # Assert
            assert result == 120
            handler.loader.estimate_duration.assert_called_once_with("/path/to/file.srt")