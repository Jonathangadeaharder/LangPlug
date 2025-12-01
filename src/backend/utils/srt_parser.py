"""SRT Subtitle Parser Utility

Parser for SRT subtitle files that handles both single-language and dual-language formats. Supports Windows and Unix line endings.
"""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SRTSegment:
    """Represents a single subtitle segment from an SRT file"""

    index: int
    start_time: float  # in seconds
    end_time: float  # in seconds
    text: str
    original_text: str = ""  # For dual-language subtitles
    translation: str = ""  # For dual-language subtitles


class SRTParser:
    """Parser for SRT subtitle files"""

    # SRT timestamp pattern: HH:MM:SS,mmm --> HH:MM:SS,mmm
    TIMESTAMP_PATTERN = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})")

    @staticmethod
    def parse_timestamp(timestamp_str: str) -> float:
        """Convert SRT timestamp to seconds

        Args:
            timestamp_str: Timestamp in format HH:MM:SS,mmm

        Returns:
            Time in seconds as float
        """
        match = re.match(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})", timestamp_str)
        if not match:
            raise ValueError(f"Invalid timestamp format: {timestamp_str}")

        hours, minutes, seconds, milliseconds = map(int, match.groups())
        return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000

    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """Convert seconds to SRT timestamp format

        Args:
            seconds: Time in seconds

        Returns:
            Timestamp in SRT format HH:MM:SS,mmm
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

    @classmethod
    def parse_file(cls, file_path: str) -> list[SRTSegment]:
        """Parse an SRT file into a list of segments

        Args:
            file_path: Path to the SRT file

        Returns:
            List of SRTSegment objects

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is invalid
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"SRT file not found: {file_path}")

        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(path, encoding="latin-1") as f:
                content = f.read()

        return cls.parse_content(content)

    @classmethod
    def parse_content(cls, content: str) -> list[SRTSegment]:
        """Parse SRT content string into segments

        Args:
            content: SRT file content as string

        Returns:
            List of SRTSegment objects
        """
        segments = []
        # Support both LF and CRLF newlines when splitting blocks
        # This ensures Windows-formatted SRT files are parsed correctly
        blocks = re.split(r"\r?\n\r?\n", content.strip())

        for block in blocks:
            if not block.strip():
                continue

            lines = block.strip().split("\n")
            if len(lines) < 3:
                continue

            try:
                # Parse index
                index = int(lines[0].strip())

                # Parse timestamps
                timestamp_match = cls.TIMESTAMP_PATTERN.match(lines[1])
                if not timestamp_match:
                    continue

                start_h, start_m, start_s, start_ms, end_h, end_m, end_s, end_ms = map(int, timestamp_match.groups())

                start_time = start_h * 3600 + start_m * 60 + start_s + start_ms / 1000
                end_time = end_h * 3600 + end_m * 60 + end_s + end_ms / 1000

                # Parse text (join remaining lines)
                text_lines = lines[2:]
                full_text = "\n".join(text_lines)

                # Check for dual-language format (original | translation)
                original_text = ""
                translation = ""

                if "|" in full_text:
                    parts = full_text.split("|", 1)
                    original_text = parts[0].strip()
                    translation = parts[1].strip() if len(parts) > 1 else ""
                    text = original_text  # Use original as main text
                else:
                    text = full_text.strip()
                    original_text = text

                segment = SRTSegment(
                    index=index,
                    start_time=start_time,
                    end_time=end_time,
                    text=text,
                    original_text=original_text,
                    translation=translation,
                )

                segments.append(segment)

            except (ValueError, IndexError):
                # Skip malformed blocks
                continue

        return segments

    @staticmethod
    def segments_to_srt(segments: list[SRTSegment]) -> str:
        """Convert segments back to SRT format

        Args:
            segments: List of SRTSegment objects

        Returns:
            SRT formatted string
        """
        srt_content = []

        for segment in segments:
            srt_content.append(str(segment.index))

            start_ts = SRTParser.format_timestamp(segment.start_time)
            end_ts = SRTParser.format_timestamp(segment.end_time)
            srt_content.append(f"{start_ts} --> {end_ts}")

            # Handle dual-language format
            if segment.translation:
                srt_content.append(f"{segment.original_text} | {segment.translation}")
            elif segment.text:
                srt_content.append(segment.text)
            else:
                # Ensure we have some text
                srt_content.append(segment.original_text or "")

            srt_content.append("")  # Empty line between segments

        return "\n".join(srt_content)

    @staticmethod
    def save_segments(segments: list[SRTSegment], file_path: str) -> None:
        """Save segments to an SRT file

        Args:
            segments: List of SRTSegment objects
            file_path: Output file path
        """
        import logging

        logger = logging.getLogger(__name__)

        srt_content = SRTParser.segments_to_srt(segments)
        logger.debug("Writing SRT file with %d chars", len(srt_content))

        # Ensure parent directory exists
        from pathlib import Path

        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
            f.flush()  # Force write to disk

        # Verify file was written
        if Path(file_path).exists():
            actual_size = Path(file_path).stat().st_size
            logger.debug("SRT file written with %d bytes", actual_size)
            if actual_size == 0 and len(srt_content) > 0:
                logger.error("SRT file is empty but content was not empty (%d chars)", len(srt_content))
                # Try writing again with explicit UTF-8 BOM
                with open(file_path, "w", encoding="utf-8-sig") as f:
                    f.write(srt_content)
                    f.flush()
                logger.debug("Retried SRT save with UTF-8 BOM")
        else:
            logger.error("SRT file was not created: %s", file_path)
