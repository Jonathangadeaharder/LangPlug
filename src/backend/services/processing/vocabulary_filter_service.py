"""
Vocabulary Filter Service
Handles vocabulary filtering from subtitles for chunk processing
"""

import uuid
from typing import Any

from core.config.logging_config import get_logger
from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor
from services.vocabulary import (
    get_vocabulary_progress_service,
    get_vocabulary_query_service,
    get_vocabulary_service,
    get_vocabulary_stats_service,
)

logger = get_logger(__name__)

# UUID namespace for vocabulary words (deterministic UUIDs)
VOCABULARY_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


class VocabularyFilterService:
    """Service for filtering vocabulary from subtitles"""

    def __init__(self):
        # Initialize vocabulary service for DirectSubtitleProcessor
        query_service = get_vocabulary_query_service()
        progress_service = get_vocabulary_progress_service()
        stats_service = get_vocabulary_stats_service()
        vocab_service = get_vocabulary_service(query_service, progress_service, stats_service)

        self.subtitle_processor = DirectSubtitleProcessor(vocab_service=vocab_service)

    async def filter_vocabulary_from_srt(
        self,
        srt_file_path: str,
        user: Any,
        language_preferences: dict[str, Any],
        db_session: Any,
        task_id: str | None = None,
        task_progress: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Filter vocabulary from SRT file using subtitle processor

        Args:
            srt_file_path: Path to SRT file
            user: Authenticated user object
            language_preferences: User language preferences
            db_session: Database session (required)
            task_id: Optional task ID for progress tracking
            task_progress: Optional progress tracking dictionary

        Returns:
            List of vocabulary words for learning
        """
        if db_session is None:
            raise ValueError("Database session is required for filter_vocabulary_from_srt")

        logger.debug("Filtering vocabulary", path=srt_file_path)

        # Update progress: Start processing (35% -> 40%)
        if task_id and task_progress:
            task_progress[task_id].progress = 40
            task_progress[task_id].message = "Processing subtitle segments"

        # Use subtitle processor to filter vocabulary
        filter_result = await self.subtitle_processor.process_srt_file(
            srt_file_path=srt_file_path,
            user_id=str(user.id),
            db=db_session,
            user_level=language_preferences.get("level", "A1"),
            language=language_preferences.get("target", "de"),
        )

        # Update progress: Extracting vocabulary (40% -> 55%)
        if task_id and task_progress:
            task_progress[task_id].progress = 55
            task_progress[task_id].message = "Extracting vocabulary words"

        # Extract vocabulary from filter result
        vocabulary = self.extract_vocabulary_from_result(filter_result)

        if not vocabulary:
            self.debug_empty_vocabulary(filter_result, srt_file_path)

        # Update progress: Vocabulary extracted (55% -> 65%)
        if task_id and task_progress:
            task_progress[task_id].progress = 65
            task_progress[task_id].message = f"Found {len(vocabulary)} learning words"

        logger.debug("Filtered vocabulary", count=len(vocabulary))
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

        if not filter_result:
            return vocabulary

        # Extract vocabulary from blocking_words (single unknown words per subtitle)
        if "blocking_words" in filter_result:
            for word in filter_result.get("blocking_words", []):
                vocabulary.append(self._create_vocabulary_word_dict(word))

        # ALSO extract vocabulary from learning_subtitles (subtitles with 2+ unknown words)
        if "learning_subtitles" in filter_result:
            for subtitle in filter_result.get("learning_subtitles", []):
                # Extract active words from the subtitle
                active_words = subtitle.active_words if hasattr(subtitle, "active_words") else []
                for word in active_words:
                    vocabulary.append(self._create_vocabulary_word_dict(word))

        return vocabulary

    def _create_vocabulary_word_dict(self, word: Any) -> dict[str, Any]:
        """
        Create vocabulary word dictionary with proper UUID concept_id

        Args:
            word: VocabularyWord Pydantic model or dict from srt_file_handler

        Returns:
            Dictionary matching frontend VocabularyWord type with valid UUID concept_id
        """
        # Check if word is already a VocabularyWord Pydantic model or dict
        if hasattr(word, "model_dump"):
            # It's a Pydantic model - convert to dict
            word_dict = word.model_dump()
            word_text = word_dict.get("word", "")
            lemma = word_dict.get("lemma", None)
            difficulty = word_dict.get("difficulty_level", "C2")
            translation = word_dict.get("translation", None)
        elif isinstance(word, dict):
            # It's already a dict
            word_text = word.get("word", "")
            lemma = word.get("lemma", None)
            difficulty = word.get("difficulty_level", "C2")
            translation = word.get("translation", None)
        else:
            # Fallback: treat as FilteredWord with metadata
            word_text = word.text if hasattr(word, "text") else str(word)
            metadata = getattr(word, "metadata", {})
            lemma = metadata.get("lemma", None)
            difficulty = metadata.get("difficulty_level", "C2")
            translation = getattr(word, "translation", None)

        # Generate deterministic UUID based on lemma (or word) + difficulty
        identifier = f"{lemma or word_text}-{difficulty}"
        concept_id = str(uuid.uuid5(VOCABULARY_NAMESPACE, identifier))

        return {
            # Required fields matching frontend VocabularyWord type
            "concept_id": concept_id,  # Valid UUID string
            "word": word_text,
            "difficulty_level": difficulty,
            # Optional fields
            "translation": translation,
            "lemma": lemma,  # spaCy-generated lemma
            "semantic_category": None,
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
        logger.warning("No vocabulary found", path=srt_file_path)

        if filter_result:
            logger.debug("Filter result", learning=len(filter_result.get("learning_subtitles", [])))


def get_vocabulary_filter_service() -> VocabularyFilterService:
    """Returns fresh instance to avoid global state"""
    return VocabularyFilterService()
