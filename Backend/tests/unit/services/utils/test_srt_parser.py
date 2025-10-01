"""
Test suite for SRTParser
Tests SRT subtitle file parsing and formatting
"""

from unittest.mock import patch

import pytest

from services.utils.srt_parser import SRTParser, SRTSegment


class TestSRTSegmentDataclass:
    """Test SRTSegment dataclass"""

    def test_segment_creation_minimal(self):
        """Test creating segment with minimal fields"""
        segment = SRTSegment(index=1, start_time=0.0, end_time=5.0, text="Hello world")
        assert segment.index == 1
        assert segment.start_time == 0.0
        assert segment.end_time == 5.0
        assert segment.text == "Hello world"
        assert segment.original_text == ""
        assert segment.translation == ""

    def test_segment_creation_dual_language(self):
        """Test creating segment with dual language"""
        segment = SRTSegment(
            index=1,
            start_time=0.0,
            end_time=5.0,
            text="Hello world",
            original_text="Hello world",
            translation="Hallo Welt",
        )
        assert segment.original_text == "Hello world"
        assert segment.translation == "Hallo Welt"


class TestParseTimestamp:
    """Test timestamp parsing"""

    def test_parse_timestamp_zero(self):
        """Test parsing zero timestamp"""
        result = SRTParser.parse_timestamp("00:00:00,000")
        assert result == 0.0

    def test_parse_timestamp_seconds(self):
        """Test parsing seconds only"""
        result = SRTParser.parse_timestamp("00:00:45,500")
        assert result == 45.5

    def test_parse_timestamp_minutes(self):
        """Test parsing minutes and seconds"""
        result = SRTParser.parse_timestamp("00:02:05,250")
        assert result == 125.25

    def test_parse_timestamp_hours(self):
        """Test parsing hours, minutes, seconds"""
        result = SRTParser.parse_timestamp("01:02:05,123")
        assert result == 3725.123

    def test_parse_timestamp_invalid_format(self):
        """Test parsing invalid timestamp raises error"""
        with pytest.raises(ValueError, match="Invalid timestamp format"):
            SRTParser.parse_timestamp("invalid")

    def test_parse_timestamp_missing_parts(self):
        """Test parsing timestamp with missing parts"""
        with pytest.raises(ValueError, match="Invalid timestamp format"):
            SRTParser.parse_timestamp("00:00")


class TestFormatTimestamp:
    """Test timestamp formatting"""

    def test_format_timestamp_zero(self):
        """Test formatting zero seconds"""
        result = SRTParser.format_timestamp(0.0)
        assert result == "00:00:00,000"

    def test_format_timestamp_seconds(self):
        """Test formatting seconds"""
        result = SRTParser.format_timestamp(45.5)
        assert result == "00:00:45,500"

    def test_format_timestamp_minutes(self):
        """Test formatting minutes"""
        result = SRTParser.format_timestamp(125.25)
        assert result == "00:02:05,250"

    def test_format_timestamp_hours(self):
        """Test formatting hours"""
        result = SRTParser.format_timestamp(3725.123)
        assert result == "01:02:05,123"

    def test_format_timestamp_milliseconds_rounding(self):
        """Test milliseconds are rounded correctly"""
        result = SRTParser.format_timestamp(10.999)
        assert result == "00:00:10,999"


class TestParseFile:
    """Test SRT file parsing"""

    def test_parse_file_simple(self, tmp_path):
        """Test parsing simple SRT file"""
        srt_file = tmp_path / "test.srt"
        srt_file.write_text(
            "1\n00:00:00,000 --> 00:00:05,000\nHello world\n\n2\n00:00:05,000 --> 00:00:10,000\nSecond subtitle\n"
        )

        segments = SRTParser.parse_file(str(srt_file))

        assert len(segments) == 2
        assert segments[0].index == 1
        assert segments[0].text == "Hello world"
        assert segments[0].start_time == 0.0
        assert segments[0].end_time == 5.0
        assert segments[1].index == 2
        assert segments[1].text == "Second subtitle"

    def test_parse_file_not_found(self):
        """Test parsing non-existent file raises error"""
        with pytest.raises(FileNotFoundError, match="SRT file not found"):
            SRTParser.parse_file("/nonexistent/file.srt")

    def test_parse_file_unicode_decode_fallback(self, tmp_path):
        """Test file parsing falls back to latin-1 encoding"""
        srt_file = tmp_path / "test.srt"
        # Write with latin-1 encoding
        srt_file.write_bytes(
            b"1\n"
            b"00:00:00,000 --> 00:00:05,000\n"
            b"Caf\xe9\n"  # café in latin-1
            b"\n"
        )

        # Mock open to raise UnicodeDecodeError on first call
        original_open = open
        call_count = [0]

        def mock_open_func(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1 and kwargs.get("encoding") == "utf-8":
                raise UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")
            return original_open(*args, **kwargs)

        with patch("builtins.open", side_effect=mock_open_func):
            segments = SRTParser.parse_file(str(srt_file))

        assert len(segments) == 1


class TestParseContent:
    """Test SRT content parsing"""

    def test_parse_content_empty(self):
        """Test parsing empty content"""
        segments = SRTParser.parse_content("")
        assert segments == []

    def test_parse_content_single_segment(self):
        """Test parsing single segment"""
        content = "1\n00:00:00,000 --> 00:00:05,000\nHello world\n"
        segments = SRTParser.parse_content(content)

        assert len(segments) == 1
        assert segments[0].index == 1
        assert segments[0].text == "Hello world"
        assert segments[0].start_time == 0.0
        assert segments[0].end_time == 5.0

    def test_parse_content_multiline_text(self):
        """Test parsing segment with multiline text"""
        content = "1\n00:00:00,000 --> 00:00:05,000\nLine 1\nLine 2\nLine 3\n"
        segments = SRTParser.parse_content(content)

        assert len(segments) == 1
        assert segments[0].text == "Line 1\nLine 2\nLine 3"

    def test_parse_content_dual_language(self):
        """Test parsing dual-language format"""
        content = "1\n00:00:00,000 --> 00:00:05,000\nHello world | Hallo Welt\n"
        segments = SRTParser.parse_content(content)

        assert len(segments) == 1
        assert segments[0].text == "Hello world"
        assert segments[0].original_text == "Hello world"
        assert segments[0].translation == "Hallo Welt"

    def test_parse_content_windows_line_endings(self):
        """Test parsing content with Windows CRLF line endings"""
        content = (
            "1\r\n"
            "00:00:00,000 --> 00:00:05,000\r\n"
            "Hello world\r\n"
            "\r\n"
            "2\r\n"
            "00:00:05,000 --> 00:00:10,000\r\n"
            "Second subtitle\r\n"
        )
        segments = SRTParser.parse_content(content)

        assert len(segments) == 2
        assert segments[0].text == "Hello world"
        assert segments[1].text == "Second subtitle"

    def test_parse_content_malformed_block_too_few_lines(self):
        """Test parsing skips blocks with too few lines"""
        content = "1\n00:00:00,000 --> 00:00:05,000\n\n2\n00:00:05,000 --> 00:00:10,000\nValid subtitle\n"
        segments = SRTParser.parse_content(content)

        # Only the second (valid) segment should be parsed
        assert len(segments) == 1
        assert segments[0].index == 2

    def test_parse_content_malformed_timestamp(self):
        """Test parsing skips blocks with invalid timestamps"""
        content = "1\ninvalid timestamp\nHello world\n\n2\n00:00:00,000 --> 00:00:05,000\nValid subtitle\n"
        segments = SRTParser.parse_content(content)

        # Only the second (valid) segment should be parsed
        assert len(segments) == 1
        assert segments[0].index == 2

    def test_parse_content_malformed_index(self):
        """Test parsing skips blocks with invalid index"""
        content = (
            "not_a_number\n"
            "00:00:00,000 --> 00:00:05,000\n"
            "Hello world\n"
            "\n"
            "2\n"
            "00:00:05,000 --> 00:00:10,000\n"
            "Valid subtitle\n"
        )
        segments = SRTParser.parse_content(content)

        # Only the second (valid) segment should be parsed
        assert len(segments) == 1
        assert segments[0].index == 2

    def test_parse_content_empty_blocks(self):
        """Test parsing handles empty blocks"""
        content = "1\n00:00:00,000 --> 00:00:05,000\nFirst\n\n\n\n2\n00:00:05,000 --> 00:00:10,000\nSecond\n"
        segments = SRTParser.parse_content(content)

        assert len(segments) == 2


class TestSegmentsToSrt:
    """Test converting segments to SRT format"""

    def test_segments_to_srt_single(self):
        """Test converting single segment to SRT"""
        segment = SRTSegment(index=1, start_time=0.0, end_time=5.0, text="Hello world")
        result = SRTParser.segments_to_srt([segment])

        assert "1\n" in result
        assert "00:00:00,000 --> 00:00:05,000\n" in result
        assert "Hello world\n" in result

    def test_segments_to_srt_multiple(self):
        """Test converting multiple segments"""
        segments = [
            SRTSegment(index=1, start_time=0.0, end_time=5.0, text="First"),
            SRTSegment(index=2, start_time=5.0, end_time=10.0, text="Second"),
        ]
        result = SRTParser.segments_to_srt(segments)

        assert "1\n" in result
        assert "2\n" in result
        assert "First\n" in result
        assert "Second\n" in result

    def test_segments_to_srt_dual_language(self):
        """Test converting dual-language segment"""
        segment = SRTSegment(
            index=1,
            start_time=0.0,
            end_time=5.0,
            text="Hello world",
            original_text="Hello world",
            translation="Hallo Welt",
        )
        result = SRTParser.segments_to_srt([segment])

        assert "Hello world | Hallo Welt\n" in result

    def test_segments_to_srt_empty_text_fallback(self):
        """Test converting segment with empty text uses original_text"""
        segment = SRTSegment(index=1, start_time=0.0, end_time=5.0, text="", original_text="Fallback text")
        result = SRTParser.segments_to_srt([segment])

        assert "Fallback text\n" in result

    def test_segments_to_srt_completely_empty_text(self):
        """Test converting segment with no text at all"""
        segment = SRTSegment(index=1, start_time=0.0, end_time=5.0, text="", original_text="")
        result = SRTParser.segments_to_srt([segment])

        # Should still contain segment structure
        assert "1\n" in result
        assert "00:00:00,000 --> 00:00:05,000\n" in result


class TestSaveSegments:
    """Test saving segments to file"""

    def test_save_segments_success(self, tmp_path):
        """Test successfully saving segments"""
        output_file = tmp_path / "output.srt"
        segments = [SRTSegment(index=1, start_time=0.0, end_time=5.0, text="Test")]

        SRTParser.save_segments(segments, str(output_file))

        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "Test" in content

    def test_save_segments_creates_parent_directory(self, tmp_path):
        """Test saving creates parent directories"""
        output_file = tmp_path / "subdir" / "nested" / "output.srt"
        segments = [SRTSegment(index=1, start_time=0.0, end_time=5.0, text="Test")]

        SRTParser.save_segments(segments, str(output_file))

        assert output_file.exists()

    def test_save_segments_empty_file_retry(self, tmp_path):
        """Test empty file triggers retry with UTF-8 BOM"""
        output_file = tmp_path / "output.srt"
        segments = [SRTSegment(index=1, start_time=0.0, end_time=5.0, text="Test")]

        # Mock file writing to simulate empty file on first write
        original_open = open
        call_count = [0]

        def mock_open_func(path, mode="r", *args, **kwargs):
            call_count[0] += 1
            if mode == "w" and call_count[0] == 1:
                # First write creates empty file
                handle = original_open(path, mode, *args, **kwargs)
                handle.write = lambda x: 0  # Simulate write failure
                return handle
            return original_open(path, mode, *args, **kwargs)

        with patch("builtins.open", side_effect=mock_open_func):
            SRTParser.save_segments(segments, str(output_file))

        # File should exist after retry
        assert output_file.exists()


class TestRoundTripConversion:
    """Test parsing and converting back to SRT"""

    def test_roundtrip_simple(self, tmp_path):
        """Test parsing and saving produces same result"""
        original_content = (
            "1\n00:00:00,000 --> 00:00:05,000\nHello world\n\n2\n00:00:05,000 --> 00:00:10,000\nSecond subtitle\n"
        )

        srt_file = tmp_path / "input.srt"
        srt_file.write_text(original_content)

        # Parse
        segments = SRTParser.parse_file(str(srt_file))

        # Convert back
        result = SRTParser.segments_to_srt(segments)

        # Should contain same content
        assert "Hello world" in result
        assert "Second subtitle" in result
        assert "00:00:00,000 --> 00:00:05,000" in result
        assert "00:00:05,000 --> 00:00:10,000" in result

    def test_roundtrip_dual_language(self, tmp_path):
        """Test roundtrip with dual-language subtitles"""
        original_content = "1\n00:00:00,000 --> 00:00:05,000\nHello world | Hallo Welt\n"

        srt_file = tmp_path / "input.srt"
        srt_file.write_text(original_content)

        segments = SRTParser.parse_file(str(srt_file))
        result = SRTParser.segments_to_srt(segments)

        assert "Hello world | Hallo Welt" in result
