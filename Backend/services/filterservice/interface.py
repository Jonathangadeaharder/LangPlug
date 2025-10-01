"""
Subtitle Filtering Service Interface
Chain of Command pattern for processing subtitles
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WordStatus(Enum):
    """Status of a word during filtering"""

    ACTIVE = "active"  # Word should be shown/learned
    FILTERED_INVALID = "invalid"  # Not proper vocabulary (oh, ah, names)
    FILTERED_KNOWN = "known"  # User already knows this word
    FILTERED_OTHER = "other"  # Other filtering reasons


@dataclass
class FilteredWord:
    """A word with its filtering status"""

    text: str
    start_time: float
    end_time: float
    status: WordStatus = WordStatus.ACTIVE
    filter_reason: str | None = None
    confidence: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FilteredSubtitle:
    """A subtitle with filtered words"""

    original_text: str
    start_time: float
    end_time: float
    words: list[FilteredWord]

    @property
    def active_words(self) -> list[FilteredWord]:
        """Get only words that should be shown to user"""
        return [w for w in self.words if w.status == WordStatus.ACTIVE]

    @property
    def active_text(self) -> str:
        """Get text with only active words"""
        return " ".join(w.text for w in self.active_words)

    @property
    def has_learning_content(self) -> bool:
        """Check if subtitle has words to learn"""
        return len(self.active_words) > 1

    @property
    def is_blocker(self) -> bool:
        """Check if this is a single-word blocker"""
        return len(self.active_words) == 1

    @property
    def is_empty(self) -> bool:
        """Check if subtitle is empty after filtering"""
        return len(self.active_words) == 0


@dataclass
class FilteringResult:
    """Result of subtitle filtering process"""

    learning_subtitles: list[FilteredSubtitle]  # Subtitles with 2+ active words
    blocker_words: list[FilteredWord]  # Single words that block learning
    empty_subtitles: list[FilteredSubtitle]  # Completely filtered subtitles
    statistics: dict[str, Any] = field(default_factory=dict)


class ISubtitleFilter(ABC):
    """
    Interface for individual subtitle filters
    Each filter processes subtitles in the chain
    """

    @abstractmethod
    def filter(self, subtitles: list[FilteredSubtitle]) -> list[FilteredSubtitle]:
        """
        Apply this filter to the subtitles

        Args:
            subtitles: List of subtitles to filter

        Returns:
            Processed subtitles (may modify word statuses)
        """
        pass

    @property
    @abstractmethod
    def filter_name(self) -> str:
        """Name of this filter for logging/debugging"""
        pass

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about this filter's processing"""
        return {}


class IUserVocabularyService(ABC):
    """
    Interface for authenticated user vocabulary data service
    Provides information about user's known vocabulary with authentication required
    """

    @abstractmethod
    def is_word_known(self, session_token: str, user_id: str, word: str, language: str = "en") -> bool:
        """
        Check if user knows a specific word

        Args:
            session_token: Authentication session token
            user_id: User identifier
            word: Word to check
            language: Language code

        Returns:
            True if user knows the word

        Raises:
            AuthenticationError: If session is invalid or user lacks permission
        """
        pass

    @abstractmethod
    def get_known_words(self, session_token: str, user_id: str, language: str = "en") -> set[str]:
        """
        Get all words known by user

        Args:
            session_token: Authentication session token
            user_id: User identifier
            language: Language code

        Returns:
            Set of known words

        Raises:
            AuthenticationError: If session is invalid or user lacks permission
        """
        pass

    @abstractmethod
    def mark_word_learned(self, session_token: str, user_id: str, word: str, language: str = "en") -> bool:
        """
        Mark word as learned by user

        Args:
            session_token: Authentication session token
            user_id: User identifier
            word: Word to mark as learned
            language: Language code

        Returns:
            Success status

        Raises:
            AuthenticationError: If session is invalid or user lacks permission
        """
        pass

    @abstractmethod
    def get_learning_level(self, session_token: str, user_id: str) -> str:
        """
        Get user's current learning level (A1, A2, B1, etc.)

        Args:
            session_token: Authentication session token
            user_id: User identifier

        Returns:
            Learning level code

        Raises:
            AuthenticationError: If session is invalid or user lacks permission
        """
        pass


# Helper functions for creating FilteredSubtitle from transcription results
def create_filtered_subtitle_from_segment(segment) -> FilteredSubtitle:
    """
    Create FilteredSubtitle from transcription segment

    Args:
        segment: Transcription segment with start_time, end_time, text

    Returns:
        FilteredSubtitle with words marked as ACTIVE initially
    """
    # Simple word tokenization - could be enhanced with proper NLP
    words = segment.text.split()
    word_duration = (segment.end_time - segment.start_time) / max(len(words), 1)

    filtered_words = []
    for i, word in enumerate(words):
        # Clean up word (remove punctuation for processing)
        clean_word = word.strip('.,!?";:').lower()

        word_start = segment.start_time + (i * word_duration)
        word_end = word_start + word_duration

        filtered_words.append(
            FilteredWord(text=clean_word, start_time=word_start, end_time=word_end, status=WordStatus.ACTIVE)
        )

    return FilteredSubtitle(
        original_text=segment.text, start_time=segment.start_time, end_time=segment.end_time, words=filtered_words
    )
