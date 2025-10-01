"""
Test suite for SubtitleFilter
Tests subtitle loading, parsing, and word extraction functionality
"""

from unittest.mock import Mock, patch

import pytest

from services.filtering.subtitle_filter import SubtitleFilter
from services.filterservice.interface import FilteredSubtitle


class TestSubtitleFilter:
    """Test SubtitleFilter functionality"""

    @pytest.fixture
    def service(self):
        return SubtitleFilter()

    @pytest.fixture
    def mock_task_progress(self):
        return {"task123": Mock()}


class TestLoadAndPrepareSubtitles:
    """Test subtitle loading and preparation functionality"""

    @pytest.fixture
    def service(self):
        return SubtitleFilter()

    @pytest.fixture
    def mock_task_progress(self):
        return {"task123": Mock()}

    @pytest.fixture
    def mock_srt_entries(self):
        entry1 = Mock()
        entry1.index = 1
        entry1.start_time = "00:00:01,000"
        entry1.end_time = "00:00:03,000"
        entry1.text = "Hello world"

        entry2 = Mock()
        entry2.index = 2
        entry2.start_time = "00:00:04,000"
        entry2.end_time = "00:00:06,000"
        entry2.text = "This is a test"

        return [entry1, entry2]

    @patch("services.filtering.subtitle_filter.Path")
    @patch("services.filtering.subtitle_filter.SRTParser")
    async def test_load_and_prepare_subtitles_success(
        self, mock_srt_parser, mock_path, service, mock_task_progress, mock_srt_entries
    ):
        """Test successful subtitle loading and preparation"""
        # Setup
        srt_path = "/path/to/test.srt"
        task_id = "task123"

        # Mock file existence
        mock_file = Mock()
        mock_file.exists.return_value = True
        mock_path.return_value = mock_file

        # Mock SRT parser
        mock_parser_instance = Mock()
        mock_parser_instance.parse_file.return_value = mock_srt_entries
        mock_srt_parser.return_value = mock_parser_instance

        # Execute
        result = await service.load_and_prepare_subtitles(srt_path, mock_task_progress, task_id)

        # Assert
        assert len(result) == 2
        assert isinstance(result[0], FilteredSubtitle)
        assert result[0].original_text == "Hello world"
        assert result[0].words == []
        assert result[0].start_time == "00:00:01,000"
        assert result[0].end_time == "00:00:03,000"

        # Check task progress was updated
        assert mock_task_progress[task_id].progress == 10.0
        assert mock_task_progress[task_id].current_step == "Loading subtitles..."

    @patch("services.filtering.subtitle_filter.Path")
    async def test_load_and_prepare_subtitles_file_not_found(self, mock_path, service, mock_task_progress):
        """Test subtitle loading when file doesn't exist"""
        # Setup
        srt_path = "/path/to/nonexistent.srt"
        task_id = "task123"

        # Mock file doesn't exist
        mock_file = Mock()
        mock_file.exists.return_value = False
        mock_path.return_value = mock_file

        # Execute and assert exception
        with pytest.raises(FileNotFoundError, match="SRT file not found"):
            await service.load_and_prepare_subtitles(srt_path, mock_task_progress, task_id)

    @patch("services.filtering.subtitle_filter.Path")
    @patch("services.filtering.subtitle_filter.SRTParser")
    async def test_load_and_prepare_subtitles_empty_file(self, mock_srt_parser, mock_path, service, mock_task_progress):
        """Test subtitle loading with empty SRT file"""
        # Setup
        srt_path = "/path/to/empty.srt"
        task_id = "task123"

        # Mock file exists but empty
        mock_file = Mock()
        mock_file.exists.return_value = True
        mock_path.return_value = mock_file

        # Mock SRT parser returns empty list
        mock_parser_instance = Mock()
        mock_parser_instance.parse_file.return_value = []
        mock_srt_parser.return_value = mock_parser_instance

        # Execute
        result = await service.load_and_prepare_subtitles(srt_path, mock_task_progress, task_id)

        # Assert
        assert result == []

    @patch("services.filtering.subtitle_filter.Path")
    @patch("services.filtering.subtitle_filter.SRTParser")
    async def test_load_and_prepare_subtitles_parser_error(
        self, mock_srt_parser, mock_path, service, mock_task_progress
    ):
        """Test subtitle loading when parser raises exception"""
        # Setup
        srt_path = "/path/to/corrupt.srt"
        task_id = "task123"

        # Mock file exists
        mock_file = Mock()
        mock_file.exists.return_value = True
        mock_path.return_value = mock_file

        # Mock SRT parser raises exception
        mock_parser_instance = Mock()
        mock_parser_instance.parse_file.side_effect = Exception("Parser error")
        mock_srt_parser.return_value = mock_parser_instance

        # Execute and assert exception
        with pytest.raises(Exception, match="Parser error"):
            await service.load_and_prepare_subtitles(srt_path, mock_task_progress, task_id)


class TestExtractWordsFromText:
    """Test word extraction functionality"""

    @pytest.fixture
    def service(self):
        return SubtitleFilter()

    def test_extract_words_from_text_normal(self, service):
        """Test normal word extraction"""
        text = "Hello world, this is a test!"
        result = service.extract_words_from_text(text)

        assert "hello" in result
        assert "world" in result
        assert "this" in result
        assert "test" in result
        # Single letter words should be excluded
        assert "a" not in result

    def test_extract_words_from_text_with_html_tags(self, service):
        """Test word extraction with HTML tags"""
        text = "Hello <b>world</b>, this is <i>italic</i> text!"
        result = service.extract_words_from_text(text)

        assert "hello" in result
        assert "world" in result
        assert "italic" in result
        # HTML tags should be removed
        assert "b" not in result
        assert "i" not in result

    def test_extract_words_from_text_with_speaker_labels(self, service):
        """Test word extraction with speaker labels and annotations"""
        text = "[Speaker 1]: Hello world (background music)"
        result = service.extract_words_from_text(text)

        assert "hello" in result
        assert "world" in result
        # Annotations should be removed
        assert "speaker" not in result
        assert "background" not in result
        assert "music" not in result

    def test_extract_words_from_text_empty(self, service):
        """Test word extraction with empty text"""
        result = service.extract_words_from_text("")
        assert result == []

    def test_extract_words_from_text_none(self, service):
        """Test word extraction with None text"""
        result = service.extract_words_from_text(None)
        assert result == []

    def test_extract_words_from_text_special_characters(self, service):
        """Test word extraction with special characters"""
        text = "Café naïve résumé"
        result = service.extract_words_from_text(text)

        # Should handle accented characters
        assert "café" in result
        assert "naïve" in result
        assert "résumé" in result

    def test_extract_words_from_text_hyphens_apostrophes(self, service):
        """Test word extraction with hyphens and apostrophes"""
        text = "don't well-known mother-in-law"
        result = service.extract_words_from_text(text)

        # Words with apostrophes and hyphens are kept intact
        assert "don't" in result
        assert "well-known" in result
        assert "mother-in-law" in result


class TestEstimateDuration:
    """Test duration estimation functionality"""

    @pytest.fixture
    def service(self):
        return SubtitleFilter()

    @patch("services.filtering.subtitle_filter.Path")
    def test_estimate_duration_normal_file(self, mock_path, service):
        """Test duration estimation for normal file"""
        # Setup - 5KB file
        mock_stat = Mock()
        mock_stat.st_size = 5120
        mock_file = Mock()
        mock_file.stat.return_value = mock_stat
        mock_path.return_value = mock_file

        result = service.estimate_duration("/path/to/test.srt")

        # Should estimate ~5 seconds for 5KB file
        assert result == 5

    @patch("services.filtering.subtitle_filter.Path")
    def test_estimate_duration_large_file(self, mock_path, service):
        """Test duration estimation for large file"""
        # Setup - 500KB file
        mock_stat = Mock()
        mock_stat.st_size = 512000
        mock_file = Mock()
        mock_file.stat.return_value = mock_stat
        mock_path.return_value = mock_file

        result = service.estimate_duration("/path/to/large.srt")

        # Should cap at 300 seconds (5 minutes)
        assert result == 300

    @patch("services.filtering.subtitle_filter.Path")
    def test_estimate_duration_small_file(self, mock_path, service):
        """Test duration estimation for very small file"""
        # Setup - 100 byte file
        mock_stat = Mock()
        mock_stat.st_size = 100
        mock_file = Mock()
        mock_file.stat.return_value = mock_stat
        mock_path.return_value = mock_file

        result = service.estimate_duration("/path/to/tiny.srt")

        # Should have minimum of 5 seconds
        assert result == 5

    @patch("services.filtering.subtitle_filter.Path")
    def test_estimate_duration_file_error(self, mock_path, service):
        """Test duration estimation when file access fails"""
        # Setup - file stat raises exception
        mock_file = Mock()
        mock_file.stat.side_effect = Exception("File access error")
        mock_path.return_value = mock_file

        result = service.estimate_duration("/path/to/error.srt")

        # Should return default estimate
        assert result == 30


class TestHealthCheck:
    """Test health check functionality"""

    @pytest.fixture
    def service(self):
        return SubtitleFilter()

    async def test_health_check(self, service):
        """Test service health check"""
        result = await service.health_check()

        assert result["service"] == "SubtitleFilter"
        assert result["status"] == "healthy"
        assert result["srt_parser"] == "available"
