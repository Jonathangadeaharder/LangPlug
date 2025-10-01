"""
Unit tests for DirectSubtitleProcessor facade
Tests public API behavior - delegates to focused sub-services

NOTE: Private methods moved to sub-services in services/filterservice/subtitle_processing/
These should be tested in their respective sub-service test files.
"""

from unittest.mock import AsyncMock, patch

import pytest

from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor
from services.filterservice.interface import FilteredSubtitle, FilteredWord, FilteringResult, WordStatus


@pytest.fixture
def processor():
    """Create a DirectSubtitleProcessor instance"""
    return DirectSubtitleProcessor()


@pytest.fixture
def sample_subtitles():
    """Create sample subtitle objects for testing"""
    subtitles = []

    # Subtitle with learning content
    sub1 = FilteredSubtitle(
        original_text="Der Hund spielt im Garten",
        start_time=0.0,
        end_time=2.0,
        words=[
            FilteredWord(text="der", start_time=0.0, end_time=0.5, status=WordStatus.ACTIVE),
            FilteredWord(text="hund", start_time=0.5, end_time=1.0, status=WordStatus.ACTIVE),
            FilteredWord(text="spielt", start_time=1.0, end_time=1.5, status=WordStatus.ACTIVE),
            FilteredWord(text="im", start_time=1.5, end_time=1.7, status=WordStatus.ACTIVE),
            FilteredWord(text="garten", start_time=1.7, end_time=2.0, status=WordStatus.ACTIVE),
        ],
    )
    subtitles.append(sub1)

    # Subtitle with known words
    sub2 = FilteredSubtitle(
        original_text="Ich bin hier",
        start_time=2.0,
        end_time=3.5,
        words=[
            FilteredWord(text="ich", start_time=2.0, end_time=2.5, status=WordStatus.ACTIVE),
            FilteredWord(text="bin", start_time=2.5, end_time=3.0, status=WordStatus.ACTIVE),
            FilteredWord(text="hier", start_time=3.0, end_time=3.5, status=WordStatus.ACTIVE),
        ],
    )
    subtitles.append(sub2)

    # Subtitle with interjections
    sub3 = FilteredSubtitle(
        original_text="Oh, hallo!",
        start_time=3.5,
        end_time=4.5,
        words=[
            FilteredWord(text="oh", start_time=3.5, end_time=4.0, status=WordStatus.ACTIVE),
            FilteredWord(text="hallo", start_time=4.0, end_time=4.5, status=WordStatus.ACTIVE),
        ],
    )
    subtitles.append(sub3)

    return subtitles


class TestDirectSubtitleProcessor:
    """Test suite for DirectSubtitleProcessor facade"""

    @pytest.mark.asyncio
    async def test_process_subtitles_empty_list(self, processor):
        """Test processing empty subtitle list - facade delegation test"""
        # Arrange - Mock the sub-service
        expected_result = FilteringResult(
            learning_subtitles=[], blocker_words=[], empty_subtitles=[], statistics={"total_subtitles": 0}
        )

        with patch.object(
            processor.processor, "process_subtitles", new_callable=AsyncMock, return_value=expected_result
        ):
            # Act
            result = await processor.process_subtitles([], 1, "A1", "de")

            # Assert
            assert isinstance(result, FilteringResult)
            assert len(result.learning_subtitles) == 0
            assert len(result.blocker_words) == 0
            assert len(result.empty_subtitles) == 0
            assert result.statistics["total_subtitles"] == 0

    @pytest.mark.asyncio
    async def test_process_subtitles_with_content(self, processor, sample_subtitles):
        """Test processing subtitles with actual content - facade delegation test"""
        # Arrange - Mock the sub-service
        expected_result = FilteringResult(
            learning_subtitles=sample_subtitles,
            blocker_words=[],
            empty_subtitles=[],
            statistics={"total_subtitles": 3, "language": "de", "user_level": "A2", "user_id": "1"},
        )

        with patch.object(
            processor.processor, "process_subtitles", new_callable=AsyncMock, return_value=expected_result
        ):
            # Act
            result = await processor.process_subtitles(sample_subtitles, user_id=1, user_level="A2", language="de")

            # Assert
            assert isinstance(result, FilteringResult)
            assert result.statistics["total_subtitles"] == 3
            assert result.statistics["language"] == "de"
            assert result.statistics["user_level"] == "A2"
            assert result.statistics["user_id"] == "1"

    @pytest.mark.asyncio
    async def test_process_srt_file(self, processor, sample_subtitles):
        """Test processing an SRT file - facade delegation test"""
        # Arrange - Mock the sub-services
        expected_filtering_result = FilteringResult(
            learning_subtitles=sample_subtitles, blocker_words=[], empty_subtitles=[], statistics={"total_subtitles": 3}
        )

        expected_final_result = {
            "blocking_words": [],
            "learning_subtitles": [],
            "statistics": {"segments_parsed": 3, "language": "de", "user_level": "A1"},
        }

        with (
            patch.object(
                processor.file_handler, "parse_srt_file", new_callable=AsyncMock, return_value=sample_subtitles
            ),
            patch.object(
                processor.processor, "process_subtitles", new_callable=AsyncMock, return_value=expected_filtering_result
            ),
            patch.object(processor.file_handler, "format_processing_result", return_value=expected_final_result),
        ):
            # Act
            result = await processor.process_srt_file("/path/to/file.srt", user_id=1, user_level="A1", language="de")

            # Assert
            assert "blocking_words" in result
            assert "learning_subtitles" in result
            assert "statistics" in result
            assert result["statistics"]["segments_parsed"] == 3
