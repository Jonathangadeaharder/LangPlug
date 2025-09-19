"""Unit tests for `SRTParser` that avoid external fixture files."""
from __future__ import annotations

from pathlib import Path
import pytest

from services.utils.srt_parser import SRTParser, SRTSegment


SAMPLE_SRT = """1
00:00:00,000 --> 00:00:02,000
Hallo Welt

2
00:00:02,000 --> 00:00:04,000
Bonjour | Hello
"""


@pytest.mark.timeout(30)
def test_WhenParsecontentCalled_ThenReturnssegments():
    segments = SRTParser.parse_content(SAMPLE_SRT)
    assert len(segments) == 2
    assert segments[0].text == "Hallo Welt"
    assert segments[1].translation == "Hello"


@pytest.mark.timeout(30)
def test_WhenSegmentsToSrtCalled_ThenRoundtripWorks(tmp_path: Path):
    segments = SRTParser.parse_content(SAMPLE_SRT)
    rendered = SRTParser.segments_to_srt(segments)
    path = tmp_path / "out.srt"
    SRTParser.save_segments(segments, str(path))

    assert "Bonjour" in rendered
    assert path.read_text(encoding="utf-8").count("--> ") == 2


@pytest.mark.timeout(30)
def test_WhenFormattimestampCalled_ThenMatchesparse():
    original = "00:01:02,345"
    seconds = SRTParser.parse_timestamp(original)
    regenerated = SRTParser.format_timestamp(seconds)
    assert regenerated[:11] == original[:11]
