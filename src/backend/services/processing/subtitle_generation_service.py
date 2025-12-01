"""
Subtitle Generation Service
Handles generation and processing of filtered subtitle files
"""

import re
from pathlib import Path
from typing import Any

from core.config.logging_config import get_logger

logger = get_logger(__name__)


class SubtitleGenerationService:
    """Service for generating and processing filtered subtitle files"""

    def __init__(self):
        self._word_pattern = re.compile(r"\b[\w]+\b")

    async def generate_filtered_subtitles(
        self, video_file: Path, vocabulary: list[dict[str, Any]], source_srt: str, suffix: str = ""
    ) -> str:
        """
        Generate filtered subtitle files for the chunk

        Args:
            video_file: Path to video file
            vocabulary: List of vocabulary words
            source_srt: Path to source SRT file
            suffix: Optional suffix for filtered file (e.g., "_pregame" or "_postgame")

        Returns:
            Path to the generated filtered subtitle file
        """
        logger.debug("Generating filtered subtitles", word_count=len(vocabulary))

        # Verify source SRT exists
        if not Path(source_srt).exists():
            logger.warning("No source SRT file found", path=source_srt)
            return source_srt

        # Create filtered subtitle file path with optional suffix
        if suffix:
            filtered_srt = video_file.parent / f"{video_file.stem}_filtered{suffix}.srt"
        else:
            filtered_srt = video_file.parent / f"{video_file.stem}_filtered.srt"

        # Extract vocabulary words for highlighting
        vocab_words = {word["word"].lower() for word in vocabulary if "word" in word}

        # Read source SRT content
        srt_content = await self.read_srt_file(source_srt)

        # Process content to highlight vocabulary
        filtered_content = self.process_srt_content(srt_content, vocab_words)

        # Write filtered SRT file
        await self.write_srt_file(filtered_srt, filtered_content)

        logger.debug("Generated filtered subtitles", path=str(filtered_srt))
        return str(filtered_srt)

    async def read_srt_file(self, file_path: str) -> str:
        """
        Read SRT file content asynchronously

        Args:
            file_path: Path to SRT file

        Returns:
            SRT file content
        """
        try:
            import aiofiles

            async with aiofiles.open(file_path, encoding="utf-8") as f:
                return await f.read()
        except ImportError:
            logger.warning("aiofiles not available, falling back to sync I/O")
            with open(file_path, encoding="utf-8") as f:
                return f.read()

    async def write_srt_file(self, file_path: Path, content: str) -> None:
        """
        Write SRT file content asynchronously

        Args:
            file_path: Path to SRT file
            content: SRT content to write
        """
        try:
            import aiofiles

            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(content)
        except ImportError:
            logger.warning("aiofiles not available, falling back to sync I/O")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

    def process_srt_content(self, srt_content: str, vocab_words: set[str]) -> str:
        """
        Process SRT content to highlight vocabulary words

        Args:
            srt_content: Original SRT content
            vocab_words: Set of vocabulary words to highlight

        Returns:
            Processed SRT content with highlighted vocabulary
        """
        lines = srt_content.split("\n")
        processed_lines = []

        for line in lines:
            # Skip index lines, timestamp lines, and empty lines
            if line.strip() and not line.strip().isdigit() and "-->" not in line:
                # This is a subtitle text line - highlight vocabulary words
                highlighted_line = self.highlight_vocabulary_in_line(line, vocab_words)
                processed_lines.append(highlighted_line)
            else:
                processed_lines.append(line)

        return "\n".join(processed_lines)

    def highlight_vocabulary_in_line(self, line: str, vocab_words: set[str]) -> str:
        """
        Highlight vocabulary words in a subtitle line

        Args:
            line: Subtitle text line
            vocab_words: Set of vocabulary words to highlight

        Returns:
            Line with vocabulary words highlighted using SRT tags
        """
        # Create a copy of the line to modify
        highlighted_line = line

        # Sort words by length (longest first) to avoid partial matches
        sorted_words = sorted(vocab_words, key=len, reverse=True)

        for word in sorted_words:
            # Create regex pattern for whole words (case insensitive)
            pattern = r"\b" + re.escape(word) + r"\b"

            # Replace with highlighted version using SRT color tags
            def replace_func(match):
                return f'<font color="yellow">{match.group()}</font>'

            highlighted_line = re.sub(pattern, replace_func, highlighted_line, flags=re.IGNORECASE)

        return highlighted_line


def get_subtitle_generation_service() -> SubtitleGenerationService:
    """Returns fresh instance to avoid global state"""
    return SubtitleGenerationService()
