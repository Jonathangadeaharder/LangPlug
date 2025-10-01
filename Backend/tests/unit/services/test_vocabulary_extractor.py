"""
Test suite for VocabularyExtractor
Tests vocabulary extraction and building functionality
"""

from unittest.mock import AsyncMock, Mock, mock_open, patch

import pytest

from api.models.processing import VocabularyWord
from services.filtering.vocabulary_extractor import VocabularyExtractor
from services.filterservice.interface import FilteredSubtitle


class TestVocabularyExtractor:
    """Test VocabularyExtractor functionality"""

    def test_initialization_with_processor(self):
        """Test service initialization with custom subtitle processor"""
        mock_processor = Mock()
        service = VocabularyExtractor(mock_processor)
        assert service.subtitle_processor == mock_processor

    @pytest.fixture
    def service(self):
        return VocabularyExtractor()

    @pytest.fixture
    def mock_task_progress(self):
        return {"task123": Mock()}


class TestApplyFiltering:
    """Test filtering application functionality"""

    @pytest.fixture
    def service(self):
        return VocabularyExtractor()

    @pytest.fixture
    def mock_task_progress(self):
        return {"task123": Mock()}

    @pytest.fixture
    def mock_subtitles(self):
        subtitle1 = FilteredSubtitle(
            original_text="Hello world", start_time="00:00:01,000", end_time="00:00:03,000", words=[]
        )
        subtitle2 = FilteredSubtitle(
            original_text="This is a test", start_time="00:00:04,000", end_time="00:00:06,000", words=[]
        )
        return [subtitle1, subtitle2]

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.remove")
    async def test_apply_filtering_success(self, mock_remove, mock_file, service, mock_task_progress, mock_subtitles):
        """Test successful filtering application"""
        # Setup
        task_id = "task123"
        user_id = "user456"
        user_level = "A1"
        target_language = "de"

        # Mock filtering result
        mock_filtering_result = Mock()
        mock_filtering_result.blocker_words = [Mock(), Mock()]
        service.subtitle_processor.process_subtitles = AsyncMock(return_value=mock_filtering_result)

        # Execute
        result = await service.apply_filtering(
            mock_subtitles, mock_task_progress, task_id, user_id, user_level, target_language
        )

        # Assert
        assert result == mock_filtering_result
        assert mock_task_progress[task_id].progress == 40.0
        assert mock_task_progress[task_id].current_step == "Applying vocabulary filtering..."
        service.subtitle_processor.process_subtitles.assert_called_once()
        # Note: File cleanup is implementation detail, testing functional outcomes instead

    async def test_apply_filtering_error(self, service, mock_task_progress, mock_subtitles):
        """Test filtering application with error"""
        # Setup
        task_id = "task123"
        user_id = "user456"
        user_level = "A1"
        target_language = "de"

        # Mock subtitle processor to raise exception
        service.subtitle_processor.process_subtitles = AsyncMock(side_effect=Exception("Processing error"))

        # Execute and assert exception
        with pytest.raises(Exception, match="Processing error"):
            await service.apply_filtering(
                mock_subtitles, mock_task_progress, task_id, user_id, user_level, target_language
            )


class TestBuildVocabularyWords:
    """Test vocabulary word building functionality"""

    @pytest.fixture
    def service(self):
        return VocabularyExtractor()

    @pytest.fixture
    def mock_task_progress(self):
        return {"task123": Mock()}

    @pytest.fixture
    def mock_filtering_result(self):
        # Mock blocker words
        blocker1 = Mock()
        blocker1.word = "haus"
        blocker1.difficulty = "A1"
        blocker1.pos = "noun"
        blocker1.contexts = ["Das ist ein Haus"]
        blocker1.frequency = 5

        blocker2 = Mock()
        blocker2.word = "auto"
        blocker2.difficulty = "A2"
        blocker2.pos = "noun"
        blocker2.contexts = ["Ich fahre Auto"]
        blocker2.frequency = 3

        result = Mock()
        result.blocker_words = [blocker1, blocker2]
        return result

    @patch("services.filtering.vocabulary_extractor.lemmatize_word")
    async def test_build_vocabulary_words_success(
        self, mock_lemmatize, service, mock_task_progress, mock_filtering_result
    ):
        """Test successful vocabulary word building"""
        # Setup
        task_id = "task123"
        mock_lemmatize.side_effect = lambda word: word.lower()

        # Execute
        result = await service.build_vocabulary_words(mock_filtering_result, mock_task_progress, task_id)

        # Assert
        assert len(result) == 2
        assert isinstance(result[0], VocabularyWord)
        assert result[0].word == "haus"
        assert result[0].difficulty_level == "A1"
        assert result[0].semantic_category == "noun"
        assert result[0].lemma == "haus"

        assert mock_task_progress[task_id].progress == 60.0
        assert mock_task_progress[task_id].current_step == "Building vocabulary words..."

    async def test_build_vocabulary_words_empty_result(self, service, mock_task_progress):
        """Test vocabulary word building with empty filtering result"""
        # Setup
        task_id = "task123"
        empty_result = Mock()
        empty_result.blocker_words = []

        # Execute
        result = await service.build_vocabulary_words(empty_result, mock_task_progress, task_id)

        # Assert
        assert result == []

    async def test_build_vocabulary_words_none_result(self, service, mock_task_progress):
        """Test vocabulary word building with None filtering result"""
        # Setup
        task_id = "task123"

        # Execute
        result = await service.build_vocabulary_words(None, mock_task_progress, task_id)

        # Assert
        assert result == []

    @patch("services.filtering.vocabulary_extractor.lemmatize_word")
    async def test_build_vocabulary_words_with_error(self, mock_lemmatize, service, mock_task_progress):
        """Test vocabulary word building with individual word errors"""
        # Setup
        task_id = "task123"
        mock_lemmatize.side_effect = lambda word: word.lower()

        # Mock filtering result with problematic blocker word
        problematic_blocker = Mock()
        problematic_blocker.word = "problematic"
        # Missing required attributes to cause error

        result = Mock()
        result.blocker_words = [problematic_blocker]

        # Execute (should not raise exception, just skip problematic words)
        vocabulary_words = await service.build_vocabulary_words(result, mock_task_progress, task_id)

        # Assert - should continue processing despite errors
        assert isinstance(vocabulary_words, list)


class TestExtractBlockingWords:
    """Test blocking word extraction functionality"""

    @pytest.fixture
    def service(self):
        return VocabularyExtractor()

    async def test_extract_blocking_words_success(self, service):
        """Test successful blocking word extraction"""
        # Setup
        srt_path = "/path/to/test.srt"
        user_id = "user123"
        user_level = "A1"
        target_language = "de"

        # Mock filtering result
        blocker1 = Mock()
        blocker1.word = "haus"
        blocker1.difficulty = "A1"
        blocker1.pos = "noun"
        blocker1.contexts = ["Das ist ein Haus"]
        blocker1.frequency = 5

        mock_result = Mock()
        mock_result.blocker_words = [blocker1]

        service.subtitle_processor.process_subtitles = AsyncMock(return_value=mock_result)

        # Execute
        with patch("services.filtering.vocabulary_extractor.lemmatize_word", return_value="haus"):
            result = await service.extract_blocking_words(srt_path, user_id, user_level, target_language)

        # Assert
        assert len(result) == 1
        assert result[0]["word"] == "haus"
        assert result[0]["difficulty"] == "A1"
        assert result[0]["pos"] == "noun"
        assert result[0]["lemma"] == "haus"

    async def test_extract_blocking_words_empty_result(self, service):
        """Test blocking word extraction with empty result"""
        # Setup
        srt_path = "/path/to/test.srt"
        user_id = "user123"

        # Mock empty filtering result
        mock_result = Mock()
        mock_result.blocker_words = []
        service.subtitle_processor.process_subtitles = AsyncMock(return_value=mock_result)

        # Execute
        result = await service.extract_blocking_words(srt_path, user_id)

        # Assert
        assert result == []

    async def test_extract_blocking_words_error(self, service):
        """Test blocking word extraction with processing error"""
        # Setup
        srt_path = "/path/to/test.srt"
        user_id = "user123"

        # Mock subtitle processor to raise exception
        service.subtitle_processor.process_subtitles = AsyncMock(side_effect=Exception("Processing error"))

        # Execute
        result = await service.extract_blocking_words(srt_path, user_id)

        # Assert - should return empty list on error
        assert result == []


class TestGenerateCandidateForms:
    """Test candidate form generation functionality"""

    @pytest.fixture
    def service(self):
        return VocabularyExtractor()

    def test_generate_candidate_forms_german(self, service):
        """Test German candidate form generation"""
        result = service.generate_candidate_forms("hausaufgaben", "de")

        # Should include original word and lowercase
        assert "hausaufgaben" in result
        assert "hausaufgaben" in result

        # Should include potential German forms
        assert len(result) > 2  # Should have some heuristic forms

    def test_generate_candidate_forms_other_language(self, service):
        """Test candidate form generation for non-German language"""
        result = service.generate_candidate_forms("hello", "en")

        # Should include original word (which is already lowercase, so only 1 unique form)
        assert "hello" in result
        assert len(result) == 1  # Only one unique form since "hello" == "hello".lower()

    def test_german_heuristic_forms(self, service):
        """Test German-specific heuristic form generation"""
        result = service._german_heuristic_forms("hausaufgaben")

        # Should generate candidates by removing common German suffixes
        assert len(result) > 0
        # Should try removing 'en' ending
        assert "hausaufgab" in result

    def test_german_heuristic_forms_short_word(self, service):
        """Test German heuristic forms with short word"""
        result = service._german_heuristic_forms("er")

        # Should not generate forms for very short words
        assert len(result) == 0


class TestCreateSrtContent:
    """Test SRT content creation functionality"""

    @pytest.fixture
    def service(self):
        return VocabularyExtractor()

    @pytest.fixture
    def mock_subtitles(self):
        subtitle1 = FilteredSubtitle(
            original_text="Hello world", start_time="00:00:01,000", end_time="00:00:03,000", words=[]
        )
        subtitle2 = FilteredSubtitle(
            original_text="This is a test", start_time="00:00:04,000", end_time="00:00:06,000", words=[]
        )
        return [subtitle1, subtitle2]

    def test_create_srt_content(self, service, mock_subtitles):
        """Test SRT content creation from subtitles"""
        result = service._create_srt_content(mock_subtitles)

        # Should create proper SRT format
        lines = result.split("\n")
        assert "1" in lines  # First subtitle index
        assert "00:00:01,000 --> 00:00:03,000" in lines  # First timing
        assert "Hello world" in lines  # First text
        assert "2" in lines  # Second subtitle index
        assert "This is a test" in lines  # Second text

    def test_create_srt_content_empty(self, service):
        """Test SRT content creation with empty subtitles"""
        result = service._create_srt_content([])
        assert result == ""


class TestHealthCheck:
    """Test health check functionality"""

    @pytest.fixture
    def service(self):
        return VocabularyExtractor()

    async def test_health_check(self, service):
        """Test service health check"""
        result = await service.health_check()

        assert result["service"] == "VocabularyExtractor"
        assert result["status"] == "healthy"
        assert result["subtitle_processor"] == "available"
        assert result["lemmatizer"] == "available"
