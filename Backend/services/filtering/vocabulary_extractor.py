"""
Vocabulary Extractor - Extracts and builds vocabulary words from subtitles
Extracted from filtering_handler.py for better separation of concerns
"""

import logging
import tempfile
from pathlib import Path
from typing import Any

from api.models.processing import VocabularyWord
from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor
from services.filterservice.interface import FilteredSubtitle, FilteringResult
from services.interfaces.base import IService
from services.nlp.lemma_resolver import lemmatize_word

logger = logging.getLogger(__name__)


class VocabularyExtractor(IService):
    """Service responsible for extracting vocabulary from subtitles"""

    def __init__(self, subtitle_processor: DirectSubtitleProcessor = None):
        self.subtitle_processor = subtitle_processor or DirectSubtitleProcessor()

    async def apply_filtering(
        self,
        subtitles: list[FilteredSubtitle],
        task_progress: dict[str, Any],
        task_id: str,
        user_id: str,
        user_level: str,
        target_language: str,
    ) -> FilteringResult:
        """Apply vocabulary filtering to subtitle collection"""
        task_progress[task_id].progress = 40.0
        task_progress[task_id].current_step = "Applying vocabulary filtering..."
        task_progress[task_id].message = f"Processing {len(subtitles)} subtitles"

        try:
            # Use subtitle processor for filtering
            logger.info(f"Processing {len(subtitles)} subtitles for user {user_id}")

            # For now, create a simple SRT content from subtitles
            srt_content = self._create_srt_content(subtitles)

            # Use secure temp directory (cross-platform)
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".srt", prefix=f"temp_{task_id}_", encoding="utf-8", delete=False
            ) as temp_file:
                temp_file.write(srt_content)
                temp_srt_path = temp_file.name

            try:
                # Process with subtitle processor
                filtering_result = await self.subtitle_processor.process_subtitles(
                    temp_srt_path, user_id, user_level=user_level, target_language=target_language
                )
            finally:
                # Clean up temp file
                Path(temp_srt_path).unlink(missing_ok=True)

            logger.info(
                f"Filtering completed: {len(filtering_result.blocker_words) if filtering_result else 0} blockers found"
            )
            return filtering_result

        except Exception as e:
            logger.error(f"Error during filtering: {e}")
            raise

    async def build_vocabulary_words(
        self, filtering_result: FilteringResult, task_progress: dict[str, Any], task_id: str
    ) -> list[VocabularyWord]:
        """Build vocabulary word objects from filtering results"""
        task_progress[task_id].progress = 60.0
        task_progress[task_id].current_step = "Building vocabulary words..."
        task_progress[task_id].message = "Processing filtered words"

        vocabulary_words = []

        if not filtering_result or not filtering_result.blocker_words:
            logger.warning("No blocker words found in filtering result")
            return vocabulary_words

        for blocker_word in filtering_result.blocker_words:
            try:
                # Create vocabulary word object
                vocab_word = VocabularyWord(
                    word=blocker_word.word,
                    difficulty_level=getattr(blocker_word, "difficulty", "A1"),
                    semantic_category=getattr(blocker_word, "pos", None),
                    # Add lemmatization
                    lemma=lemmatize_word(blocker_word.word),
                )
                vocabulary_words.append(vocab_word)

            except Exception as e:
                logger.warning(f"Error creating vocabulary word for '{blocker_word.word}': {e}")
                continue

        logger.info(f"Built {len(vocabulary_words)} vocabulary words")
        return vocabulary_words

    async def extract_blocking_words(
        self, srt_path: str, user_id: str, user_level: str = "A1", target_language: str = "de"
    ) -> list[dict[str, Any]]:
        """Extract blocking words from SRT file"""
        try:
            logger.info(f"Extracting blocking words from {srt_path}")

            # Use subtitle processor to get blocking words
            filtering_result = await self.subtitle_processor.process_subtitles(
                srt_path, user_id, user_level=user_level, target_language=target_language
            )

            if not filtering_result or not filtering_result.blocker_words:
                logger.warning("No blocking words found")
                return []

            # Convert to dictionary format
            blocking_words = []
            for blocker_word in filtering_result.blocker_words:
                word_dict = {
                    "word": blocker_word.word,
                    "difficulty": getattr(blocker_word, "difficulty", "unknown"),
                    "pos": getattr(blocker_word, "pos", ""),
                    "contexts": getattr(blocker_word, "contexts", []),
                    "frequency": getattr(blocker_word, "frequency", 0),
                    "lemma": lemmatize_word(blocker_word.word),
                }
                blocking_words.append(word_dict)

            logger.info(f"Extracted {len(blocking_words)} blocking words")
            return blocking_words

        except Exception as e:
            logger.error(f"Error extracting blocking words: {e}")
            return []

    def generate_candidate_forms(self, word_text: str, language: str = "de") -> set[str]:
        """Generate candidate word forms for lookup"""
        candidates = {word_text, word_text.lower()}

        if language == "de":
            candidates.update(self._german_heuristic_forms(word_text))

        return candidates

    def _german_heuristic_forms(self, word_text: str) -> set[str]:
        """Generate German-specific word form candidates"""
        forms = set()
        lower_word = word_text.lower()

        # Common German endings to try removing
        suffixes_to_remove = [
            "en",
            "er",
            "es",
            "e",
            "n",
            "r",
            "s",
            "t",
            "ung",
            "keit",
            "heit",
            "lich",
            "ig",
            "isch",
            "los",
            "voll",
            "bar",
            "sam",
            "haft",
        ]

        for suffix in suffixes_to_remove:
            if lower_word.endswith(suffix) and len(lower_word) > len(suffix) + 2:
                candidate = lower_word[: -len(suffix)]
                forms.add(candidate)

        return forms

    def _create_srt_content(self, subtitles: list[FilteredSubtitle]) -> str:
        """Create SRT content from FilteredSubtitle objects"""
        srt_lines = []
        for index, subtitle in enumerate(subtitles, start=1):
            srt_lines.append(str(index))
            srt_lines.append(f"{subtitle.start_time} --> {subtitle.end_time}")
            srt_lines.append(subtitle.original_text)
            srt_lines.append("")  # Empty line between entries

        return "\n".join(srt_lines)

    async def health_check(self) -> dict[str, Any]:
        """Perform health check for the vocabulary extractor service"""
        return {
            "service": "VocabularyExtractor",
            "status": "healthy",
            "subtitle_processor": "available",
            "lemmatizer": "available",
        }

    async def initialize(self) -> None:
        """Initialize vocabulary extractor service resources"""
        logger.info("VocabularyExtractor initialized")

    async def cleanup(self) -> None:
        """Cleanup vocabulary extractor service resources"""
        logger.info("VocabularyExtractor cleanup completed")
