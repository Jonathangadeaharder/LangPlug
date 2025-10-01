"""
Test suite for ChunkTranslationService
Tests translation service management and subtitle translation building
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from services.processing.chunk_translation_service import ChunkTranslationService
from utils.srt_parser import SRTSegment


class TestChunkTranslationServiceInitialization:
    """Test service initialization"""

    def test_initialization(self):
        """Test service initializes with empty cache"""
        service = ChunkTranslationService()

        assert service._translation_services == {}


class TestGetTranslationService:
    """Test translation service creation and caching"""

    @pytest.fixture
    def service(self):
        return ChunkTranslationService()

    def test_get_translation_service_creates_new(self, service):
        """Test creating new translation service"""
        with patch("services.processing.chunk_translation_service.TranslationServiceFactory") as MockFactory:
            mock_service = Mock()
            MockFactory.create_service.return_value = mock_service

            result = service.get_translation_service("de", "en", "standard")

            assert result == mock_service
            MockFactory.create_service.assert_called_once_with(source_lang="de", target_lang="en", quality="standard")

    def test_get_translation_service_caches(self, service):
        """Test translation service is cached"""
        with patch("services.processing.chunk_translation_service.TranslationServiceFactory") as MockFactory:
            mock_service = Mock()
            MockFactory.create_service.return_value = mock_service

            # First call creates service
            result1 = service.get_translation_service("de", "en", "standard")
            # Second call uses cached service
            result2 = service.get_translation_service("de", "en", "standard")

            assert result1 == result2
            assert MockFactory.create_service.call_count == 1

    def test_get_translation_service_different_pairs(self, service):
        """Test different language pairs create separate services"""
        with patch("services.processing.chunk_translation_service.TranslationServiceFactory") as MockFactory:
            mock_service1 = Mock(name="service1")
            mock_service2 = Mock(name="service2")
            MockFactory.create_service.side_effect = [mock_service1, mock_service2]

            result1 = service.get_translation_service("de", "en")
            result2 = service.get_translation_service("es", "en")

            assert result1 != result2
            assert MockFactory.create_service.call_count == 2

    def test_get_translation_service_different_quality(self, service):
        """Test different quality levels create separate services"""
        with patch("services.processing.chunk_translation_service.TranslationServiceFactory") as MockFactory:
            mock_service1 = Mock(name="standard")
            mock_service2 = Mock(name="high")
            MockFactory.create_service.side_effect = [mock_service1, mock_service2]

            result1 = service.get_translation_service("de", "en", "standard")
            result2 = service.get_translation_service("de", "en", "high")

            assert result1 != result2
            assert MockFactory.create_service.call_count == 2


class TestBuildTranslationSegments:
    """Test building translation segments from SRT"""

    @pytest.fixture
    def service(self):
        return ChunkTranslationService()

    @pytest.fixture
    def task_progress(self):
        return {"test_task": Mock(progress=0, current_step="", message="")}

    @pytest.mark.anyio
    async def test_build_translation_segments_empty_vocabulary(self, service, task_progress):
        """Test handling empty vocabulary list"""
        result = await service.build_translation_segments(
            task_id="test_task",
            task_progress=task_progress,
            srt_file_path="/test.srt",
            vocabulary=[],
            language_preferences={"target": "de", "native": "en"},
        )

        assert result == []

    @pytest.mark.anyio
    async def test_build_translation_segments_no_segments_in_file(self, service, task_progress):
        """Test handling SRT file with no segments"""
        vocabulary = [{"word": "test", "active": True}]

        with patch("services.processing.chunk_translation_service.SRTParser") as MockParser:
            mock_parser = MockParser.return_value
            mock_parser.parse_file.return_value = []

            result = await service.build_translation_segments(
                task_id="test_task",
                task_progress=task_progress,
                srt_file_path="/test.srt",
                vocabulary=vocabulary,
                language_preferences={"target": "de", "native": "en"},
            )

            assert result == []

    @pytest.mark.anyio
    async def test_build_translation_segments_success(self, service, task_progress):
        """Test successful translation segment building"""
        vocabulary = [{"word": "Hallo", "active": True}]
        segments = [SRTSegment(1, "00:00:00,000", "00:00:02,000", "Hallo Welt")]

        with patch("services.processing.chunk_translation_service.SRTParser") as MockParser:
            mock_parser = MockParser.return_value
            mock_parser.parse_file.return_value = segments

            service._map_active_words_to_segments = Mock(return_value=[(vocabulary[0], segments[0])])
            service._build_translation_texts = AsyncMock(
                return_value=[SRTSegment(1, "00:00:00,000", "00:00:02,000", "Hello World")]
            )

            result = await service.build_translation_segments(
                task_id="test_task",
                task_progress=task_progress,
                srt_file_path="/test.srt",
                vocabulary=vocabulary,
                language_preferences={"target": "de", "native": "en"},
            )

            assert len(result) == 1
            assert result[0].text == "Hello World"

    @pytest.mark.anyio
    async def test_build_translation_segments_no_active_words_in_segments(self, service, task_progress):
        """Test when no active words found in segments"""
        vocabulary = [{"word": "test", "active": True}]
        segments = [SRTSegment(1, "00:00:00,000", "00:00:02,000", "Other text")]

        with patch("services.processing.chunk_translation_service.SRTParser") as MockParser:
            mock_parser = MockParser.return_value
            mock_parser.parse_file.return_value = segments

            service._map_active_words_to_segments = Mock(return_value=[])

            result = await service.build_translation_segments(
                task_id="test_task",
                task_progress=task_progress,
                srt_file_path="/test.srt",
                vocabulary=vocabulary,
                language_preferences={"target": "de", "native": "en"},
            )

            assert result == []


class TestMapActiveWordsToSegments:
    """Test mapping vocabulary words to subtitle segments"""

    @pytest.fixture
    def service(self):
        return ChunkTranslationService()

    def test_map_active_words_finds_words(self, service):
        """Test mapping finds words in segments"""
        vocabulary = [{"word": "Hallo", "active": True}, {"word": "Welt", "active": True}]
        segments = [
            SRTSegment(1, "00:00:00,000", "00:00:02,000", "Hallo Welt"),
            SRTSegment(2, "00:00:02,000", "00:00:04,000", "Guten Tag"),
        ]

        result = service._map_active_words_to_segments(vocabulary, segments)

        assert len(result) == 2
        assert result[0][0]["word"] == "Hallo"
        assert result[1][0]["word"] == "Welt"

    def test_map_active_words_case_insensitive(self, service):
        """Test word matching is case insensitive"""
        vocabulary = [{"word": "hallo", "active": True}]
        segments = [SRTSegment(1, "00:00:00,000", "00:00:02,000", "HALLO WELT")]

        result = service._map_active_words_to_segments(vocabulary, segments)

        assert len(result) == 1
        assert "HALLO" in result[0][1].text

    def test_map_active_words_skips_inactive(self, service):
        """Test inactive words are skipped"""
        vocabulary = [{"word": "Hallo", "active": True}, {"word": "Welt", "active": False}]
        segments = [SRTSegment(1, "00:00:00,000", "00:00:02,000", "Hallo Welt")]

        result = service._map_active_words_to_segments(vocabulary, segments)

        assert len(result) == 1
        assert result[0][0]["word"] == "Hallo"

    def test_map_active_words_skips_invalid_entries(self, service):
        """Test invalid vocabulary entries are skipped"""
        vocabulary = [
            "invalid_string",  # Not a dict
            {"active": True},  # No word field
            {"word": "", "active": True},  # Empty word
            {"word": "Hallo", "active": True},  # Valid
        ]
        segments = [SRTSegment(1, "00:00:00,000", "00:00:02,000", "Hallo")]

        result = service._map_active_words_to_segments(vocabulary, segments)

        assert len(result) == 1
        assert result[0][0]["word"] == "Hallo"

    def test_map_active_words_one_segment_per_word(self, service):
        """Test each word maps to only one segment (first match)"""
        vocabulary = [{"word": "Hallo", "active": True}]
        segments = [
            SRTSegment(1, "00:00:00,000", "00:00:02,000", "Hallo Welt"),
            SRTSegment(2, "00:00:02,000", "00:00:04,000", "Hallo nochmal"),
        ]

        result = service._map_active_words_to_segments(vocabulary, segments)

        # Should only map to first segment
        assert len(result) == 1
        assert result[0][1].index == 1


class TestBuildTranslationTexts:
    """Test building translated text segments"""

    @pytest.fixture
    def service(self):
        return ChunkTranslationService()

    @pytest.fixture
    def task_progress(self):
        return {"test_task": Mock(progress=0)}

    @pytest.mark.anyio
    async def test_build_translation_texts_success(self, service, task_progress):
        """Test successful translation building"""
        word_segments = [({"word": "Hallo", "active": True}, SRTSegment(1, "00:00:00,000", "00:00:02,000", "Hallo"))]
        language_prefs = {"target": "de", "native": "en"}

        mock_translation_service = Mock()
        mock_result = Mock(translated_text="Hello")
        mock_translation_service.translate.return_value = mock_result

        service.get_translation_service = Mock(return_value=mock_translation_service)

        result = await service._build_translation_texts(
            task_id="test_task",
            task_progress=task_progress,
            active_word_segments=word_segments,
            language_preferences=language_prefs,
        )

        assert len(result) == 1
        assert result[0].text == "Hello"
        assert result[0].index == 1

    @pytest.mark.anyio
    async def test_build_translation_texts_handles_errors(self, service, task_progress):
        """Test translation continues on individual segment errors"""
        word_segments = [
            ({"word": "Hallo", "active": True}, SRTSegment(1, "00:00:00,000", "00:00:02,000", "Hallo")),
            ({"word": "Welt", "active": True}, SRTSegment(2, "00:00:02,000", "00:00:04,000", "Welt")),
        ]
        language_prefs = {"target": "de", "native": "en"}

        mock_translation_service = Mock()
        # First translation fails, second succeeds
        mock_result = Mock(translated_text="World")
        mock_translation_service.translate.side_effect = [Exception("Translation error"), mock_result]

        service.get_translation_service = Mock(return_value=mock_translation_service)

        result = await service._build_translation_texts(
            task_id="test_task",
            task_progress=task_progress,
            active_word_segments=word_segments,
            language_preferences=language_prefs,
        )

        # Should have one successful translation
        assert len(result) == 1
        assert result[0].text == "World"

    @pytest.mark.anyio
    async def test_build_translation_texts_updates_progress(self, service, task_progress):
        """Test progress is updated during translation"""
        word_segments = [({"word": "Hallo", "active": True}, SRTSegment(1, "00:00:00,000", "00:00:02,000", "Hallo"))]
        language_prefs = {"target": "de", "native": "en"}

        mock_translation_service = Mock()
        mock_result = Mock(translated_text="Hello")
        mock_translation_service.translate.return_value = mock_result

        service.get_translation_service = Mock(return_value=mock_translation_service)

        initial_progress = task_progress["test_task"].progress

        await service._build_translation_texts(
            task_id="test_task",
            task_progress=task_progress,
            active_word_segments=word_segments,
            language_preferences=language_prefs,
        )

        # Progress should have been updated
        final_progress = task_progress["test_task"].progress
        assert final_progress > initial_progress


class TestSegmentsOverlap:
    """Test time segment overlap detection"""

    @pytest.fixture
    def service(self):
        return ChunkTranslationService()

    def test_segments_overlap_full_overlap(self, service):
        """Test detecting full overlap"""
        result = service.segments_overlap(0.0, 10.0, 0.0, 10.0)
        assert result is True

    def test_segments_overlap_significant_overlap(self, service):
        """Test detecting significant overlap (>= 50%)"""
        result = service.segments_overlap(0.0, 10.0, 5.0, 15.0, threshold=0.5)
        assert result is True

    def test_segments_overlap_no_overlap(self, service):
        """Test detecting no overlap"""
        result = service.segments_overlap(0.0, 5.0, 10.0, 15.0)
        assert result is False

    def test_segments_overlap_minimal_overlap(self, service):
        """Test minimal overlap below threshold"""
        result = service.segments_overlap(0.0, 10.0, 9.0, 15.0, threshold=0.5)
        # Only 1 second overlap out of 10 second segment = 10% < 50%
        assert result is False

    def test_segments_overlap_partial_contained(self, service):
        """Test one segment partially contained in another"""
        result = service.segments_overlap(0.0, 10.0, 2.0, 8.0, threshold=0.5)
        # Smaller segment (6s) fully inside larger (10s) = 100% overlap
        assert result is True

    def test_segments_overlap_zero_duration(self, service):
        """Test handling zero duration segments"""
        result = service.segments_overlap(5.0, 5.0, 3.0, 7.0)
        assert result is False

    def test_segments_overlap_touching_edges(self, service):
        """Test segments that just touch at boundaries"""
        result = service.segments_overlap(0.0, 5.0, 5.0, 10.0)
        # No actual overlap, just touching
        assert result is False

    def test_segments_overlap_custom_threshold(self, service):
        """Test custom overlap threshold"""
        # 25% overlap with 75% threshold
        result = service.segments_overlap(0.0, 10.0, 7.5, 15.0, threshold=0.75)
        assert result is False

        # 75% overlap with 50% threshold
        result = service.segments_overlap(0.0, 10.0, 2.5, 12.5, threshold=0.5)
        assert result is True


class TestIntegration:
    """Test integration scenarios"""

    @pytest.fixture
    def service(self):
        return ChunkTranslationService()

    @pytest.fixture
    def task_progress(self):
        return {"test_task": Mock(progress=0, current_step="", message="")}

    @pytest.mark.anyio
    async def test_end_to_end_translation_workflow(self, service, task_progress):
        """Test complete translation workflow"""
        vocabulary = [{"word": "Hallo", "active": True}, {"word": "Welt", "active": True}]
        segments = [SRTSegment(1, "00:00:00,000", "00:00:02,000", "Hallo Welt")]
        language_prefs = {"target": "de", "native": "en"}

        with patch("services.processing.chunk_translation_service.SRTParser") as MockParser:
            mock_parser = MockParser.return_value
            mock_parser.parse_file.return_value = segments

            with patch("services.processing.chunk_translation_service.TranslationServiceFactory") as MockFactory:
                mock_trans_service = Mock()
                mock_result = Mock(translated_text="Hello World")
                mock_trans_service.translate.return_value = mock_result
                MockFactory.create_service.return_value = mock_trans_service

                result = await service.build_translation_segments(
                    task_id="test_task",
                    task_progress=task_progress,
                    srt_file_path="/test.srt",
                    vocabulary=vocabulary,
                    language_preferences=language_prefs,
                )

                # Should have translations for active words
                assert len(result) >= 1
                assert any("Hello" in seg.text or "World" in seg.text for seg in result)
