"""
Vocabulary Filter Service
Handles vocabulary filtering from subtitles for chunk processing
"""

import logging
import uuid
from typing import Any

from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor

logger = logging.getLogger(__name__)

# UUID namespace for vocabulary words (deterministic UUIDs)
VOCABULARY_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


class VocabularyFilterService:
    """Service for filtering vocabulary from subtitles"""

    def __init__(self):
        self.subtitle_processor = DirectSubtitleProcessor()

    async def filter_vocabulary_from_srt(
        self, srt_file_path: str, user: Any, language_preferences: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Filter vocabulary from SRT file using subtitle processor

        Args:
            srt_file_path: Path to SRT file
            user: Authenticated user object
            language_preferences: User language preferences

        Returns:
            List of vocabulary words for learning
        """
        logger.info(f"Filtering vocabulary from {srt_file_path}")

        # Use subtitle processor to filter vocabulary
        filter_result = await self.subtitle_processor.process_srt_file(
            srt_file_path,
            str(user.id),
            user_level=language_preferences.get("level", "A1"),
            language=language_preferences.get("target", "de"),
        )

        # Extract vocabulary from filter result
        vocabulary = self.extract_vocabulary_from_result(filter_result)

        if not vocabulary:
            self.debug_empty_vocabulary(filter_result, srt_file_path)

        logger.info(f"Filtered {len(vocabulary)} vocabulary words")
        return vocabulary

    def extract_vocabulary_from_result(self, filter_result: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Extract vocabulary list from filter result

        Args:
            filter_result: Result from subtitle processor

        Returns:
            List of vocabulary word dictionaries matching frontend VocabularyWord type
        """
        vocabulary = []

        if filter_result and "blocking_words" in filter_result:
            vocabulary = [self._create_vocabulary_word_dict(word) for word in filter_result.get("blocking_words", [])]

        return vocabulary

    def _create_vocabulary_word_dict(self, word: Any) -> dict[str, Any]:
        """
        Create vocabulary word dictionary with proper UUID concept_id

        Args:
            word: Filtered word object

        Returns:
            Dictionary matching frontend VocabularyWord type with valid UUID concept_id
        """
        # Extract word text
        word_text = word.text if hasattr(word, "text") else (word.word if hasattr(word, "word") else str(word))

        # Extract from metadata (where word_filter.py stores them)
        metadata = getattr(word, "metadata", {})
        lemma = metadata.get("lemma", None)
        difficulty = metadata.get("difficulty_level", "unknown")

        # Generate deterministic UUID based on lemma (or word) + difficulty
        # This ensures same word gets same UUID across sessions
        identifier = f"{lemma or word_text}-{difficulty}"
        concept_id = str(uuid.uuid5(VOCABULARY_NAMESPACE, identifier))

        return {
            # Required fields matching frontend VocabularyWord type
            "concept_id": concept_id,  # Valid UUID string
            "word": word_text,
            "difficulty_level": difficulty,
            # Optional fields
            "translation": getattr(word, "translation", None),
            "lemma": lemma,  # spaCy-generated lemma from word_filter.py
            "semantic_category": metadata.get("part_of_speech", None),
            "domain": None,
            "known": False,  # User will mark as known in vocabulary game
        }

    def debug_empty_vocabulary(self, filter_result: dict[str, Any], srt_file_path: str) -> None:
        """
        Log debug information when no vocabulary is found

        Args:
            filter_result: Result from subtitle processor
            srt_file_path: Path to SRT file
        """
        logger.warning(f"No vocabulary found in {srt_file_path}")
        logger.debug(f"Filter result keys: {filter_result.keys() if filter_result else 'None'}")

        if filter_result:
            logger.debug(f"Learning subtitles: {len(filter_result.get('learning_subtitles', []))}")
            logger.debug(f"Empty subtitles: {len(filter_result.get('empty_subtitles', []))}")
            logger.debug(f"Statistics: {filter_result.get('statistics', {})}")


# Singleton instance
vocabulary_filter_service = VocabularyFilterService()
