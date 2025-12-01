"""
SRT file handler using pysrt library

Handles reading, writing, and manipulating SRT (SubRip) subtitle files.
"""

import pysrt

from core.config.logging_config import get_logger

logger = get_logger(__name__)


class SRTFileHandler:
    """
    Handle SRT subtitle files using pysrt library.

    Provides methods for:
    - Reading SRT files
    - Writing SRT files
    - Modifying subtitles
    - Subtitle synchronization
    """

    @staticmethod
    def read_srt(filepath: str) -> pysrt.SubRipFile | None:
        """
        Read SRT file.

        Args:
            filepath: Path to SRT file

        Returns:
            SubRipFile object or None if error
        """
        try:
            subs = pysrt.open(filepath)
            logger.debug("Loaded subtitles", count=len(subs))
            return subs
        except Exception as e:
            logger.error("Error reading SRT file", error=str(e))
            return None

    @staticmethod
    def write_srt(filepath: str, subtitles: pysrt.SubRipFile) -> bool:
        """
        Write subtitles to SRT file.

        Args:
            filepath: Path to write SRT file
            subtitles: SubRipFile object to write

        Returns:
            True if successful, False otherwise
        """
        try:
            subtitles.save(filepath)
            logger.debug("Saved subtitles", count=len(subtitles))
            return True
        except Exception as e:
            logger.error("Error writing SRT file", error=str(e))
            return False

    @staticmethod
    def create_subtitle(index: int, start_ms: int, end_ms: int, text: str) -> pysrt.SubRipItem:
        """
        Create a subtitle item.

        Args:
            index: Subtitle index (1-based)
            start_ms: Start time in milliseconds
            end_ms: End time in milliseconds
            text: Subtitle text

        Returns:
            SubRipItem object
        """
        return pysrt.SubRipItem(
            index=index,
            start=pysrt.SubRipTime(milliseconds=start_ms),
            end=pysrt.SubRipTime(milliseconds=end_ms),
            text=text,
        )

    @staticmethod
    def shift_time(subtitles: pysrt.SubRipFile, milliseconds: int) -> pysrt.SubRipFile:
        """
        Shift subtitle timings.

        Args:
            subtitles: SubRipFile to shift
            milliseconds: Amount to shift (positive or negative)

        Returns:
            Modified SubRipFile
        """
        try:
            subtitles.shift(milliseconds=milliseconds)
            return subtitles
        except Exception as e:
            logger.error("Error shifting subtitles", error=str(e))
            return subtitles

    @staticmethod
    def filter_subtitles(subtitles: pysrt.SubRipFile, start_ms: int, end_ms: int) -> pysrt.SubRipFile:
        """
        Filter subtitles to time range.

        Args:
            subtitles: SubRipFile to filter
            start_ms: Start time in milliseconds
            end_ms: End time in milliseconds

        Returns:
            Filtered SubRipFile
        """
        filtered = pysrt.SubRipFile()

        for sub in subtitles:
            sub_start = sub.start.milliseconds
            sub_end = sub.end.milliseconds

            # Check if subtitle overlaps with range
            if sub_end > start_ms and sub_start < end_ms:
                filtered.append(sub)

        # Reindex
        for i, sub in enumerate(filtered, 1):
            sub.index = i

        return filtered

    @staticmethod
    def extract_text(subtitles: pysrt.SubRipFile) -> str:
        """
        Extract all text from subtitles.

        Args:
            subtitles: SubRipFile

        Returns:
            Combined text from all subtitles
        """
        texts = [str(sub.text).strip() for sub in subtitles]
        return " ".join(texts)

    @staticmethod
    def merge_subtitles(subs1: pysrt.SubRipFile, subs2: pysrt.SubRipFile) -> pysrt.SubRipFile:
        """
        Merge two subtitle files.

        Args:
            subs1: First SubRipFile
            subs2: Second SubRipFile

        Returns:
            Merged SubRipFile
        """
        merged = pysrt.SubRipFile()

        for sub in subs1:
            merged.append(sub)

        # Reindex second file
        max_index = len(merged)
        for sub in subs2:
            sub.index = max_index + 1
            merged.append(sub)
            max_index += 1

        return merged

    @staticmethod
    def get_duration(subtitles: pysrt.SubRipFile) -> int:
        """
        Get total duration of subtitles.

        Args:
            subtitles: SubRipFile

        Returns:
            Duration in milliseconds
        """
        if not subtitles:
            return 0
        end_time = subtitles[-1].end
        # Convert time to total milliseconds: hours*3600000 + minutes*60000 + seconds*1000 + milliseconds
        total_ms = end_time.hours * 3600000 + end_time.minutes * 60000 + end_time.seconds * 1000 + end_time.milliseconds
        return total_ms


# Example usage and testing
if __name__ == "__main__":
    handler = SRTFileHandler()

    # Create sample subtitles
    subs = pysrt.SubRipFile()

    subs.append(handler.create_subtitle(1, 0, 5000, "First subtitle"))

    subs.append(handler.create_subtitle(2, 5000, 10000, "Second subtitle"))

    # Save to file
    handler.write_srt("test_subtitles.srt", subs)

    # Read back
    loaded = handler.read_srt("test_subtitles.srt")

    # Extract text
    text = handler.extract_text(loaded)
