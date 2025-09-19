"""SRT subtitle parser using pysrt library"""
from dataclasses import dataclass
from pathlib import Path

import pysrt
from pysrt import SubRipFile, SubRipItem


@dataclass
class SRTSegment:
    """Represents a subtitle segment"""
    start_time: float  # in seconds
    end_time: float    # in seconds
    text: str
    index: int

    def __post_init__(self):
        """Clean up text after initialization"""
        self.text = self.text.strip()


class SRTParser:
    """SRT subtitle parser using pysrt library"""

    def __init__(self):
        self.segments: list[SRTSegment] = []

    def parse_file(self, file_path: Path) -> list[SRTSegment]:
        """Parse SRT file and return list of segments"""
        try:
            # pysrt handles encoding detection automatically
            subs = pysrt.open(str(file_path))

            segments = []
            for sub in subs:
                segment = SRTSegment(
                    start_time=self._time_to_seconds(sub.start),
                    end_time=self._time_to_seconds(sub.end),
                    text=sub.text,
                    index=sub.index
                )
                segments.append(segment)

            self.segments = segments
            return segments

        except Exception as e:
            raise ValueError(f"Error parsing SRT file {file_path}: {e!s}")

    def parse_content(self, content: str) -> list[SRTSegment]:
        """Parse SRT content from string"""
        try:
            subs = pysrt.from_string(content)

            segments = []
            for sub in subs:
                segment = SRTSegment(
                    start_time=self._time_to_seconds(sub.start),
                    end_time=self._time_to_seconds(sub.end),
                    text=sub.text,
                    index=sub.index
                )
                segments.append(segment)

            self.segments = segments
            return segments

        except Exception as e:
            raise ValueError(f"Error parsing SRT content: {e!s}")

    def _time_to_seconds(self, time_obj) -> float:
        """Convert pysrt time object to seconds"""
        return (
            time_obj.hours * 3600 +
            time_obj.minutes * 60 +
            time_obj.seconds +
            time_obj.milliseconds / 1000.0
        )

    def get_text_at_time(self, time_seconds: float) -> str | None:
        """Get subtitle text at specific time"""
        for segment in self.segments:
            if segment.start_time <= time_seconds <= segment.end_time:
                return segment.text
        return None

    def get_segments_in_range(self, start_time: float, end_time: float) -> list[SRTSegment]:
        """Get all segments within time range"""
        return [
            segment for segment in self.segments
            if not (segment.end_time < start_time or segment.start_time > end_time)
        ]

    def save_to_file(self, file_path: Path, segments: list[SRTSegment] | None = None):
        """Save segments to SRT file"""
        if segments is None:
            segments = self.segments

        subs = SubRipFile()
        for segment in segments:
            item = SubRipItem(
                index=segment.index,
                start=self._seconds_to_time(segment.start_time),
                end=self._seconds_to_time(segment.end_time),
                text=segment.text
            )
            subs.append(item)

        subs.save(str(file_path), encoding='utf-8')

    def _seconds_to_time(self, seconds: float):
        """Convert seconds to pysrt time object"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)

        return pysrt.SubRipTime(hours, minutes, secs, milliseconds)

    def split_dual_language_text(self, text: str, separator: str = "\n") -> tuple[str, str]:
        """Split dual-language subtitle text"""
        parts = text.split(separator, 1)
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
        return text.strip(), ""

    def extract_language_segments(self, language_index: int = 0) -> list[SRTSegment]:
        """Extract segments for specific language from dual-language subtitles"""
        extracted_segments = []

        for segment in self.segments:
            lines = segment.text.split('\n')
            if language_index < len(lines):
                text = lines[language_index].strip()
                if text:  # Only include non-empty text
                    extracted_segments.append(SRTSegment(
                        start_time=segment.start_time,
                        end_time=segment.end_time,
                        text=text,
                        index=segment.index
                    ))

        return extracted_segments


def parse_srt_file(file_path: Path) -> list[SRTSegment]:
    """Convenience function to parse SRT file"""
    parser = SRTParser()
    return parser.parse_file(file_path)


def parse_srt_content(content: str) -> list[SRTSegment]:
    """Convenience function to parse SRT content"""
    parser = SRTParser()
    return parser.parse_content(content)
