"""
Core Enumerations

Centralized location for all application-wide enums to eliminate magic strings.
Domain-specific enums may remain in their respective domain modules.
"""

from enum import Enum


class CEFRLevel(str, Enum):
    """Common European Framework of Reference for Languages (CEFR) levels"""

    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"
    UNKNOWN = "unknown"

    @classmethod
    def from_str(cls, value: str) -> "CEFRLevel":
        """Convert string to enum, with fallback to UNKNOWN"""
        try:
            return cls(value.upper())
        except (ValueError, AttributeError):
            return cls.UNKNOWN

    @classmethod
    def all_levels(cls) -> list[str]:
        """Get list of all valid levels (excluding UNKNOWN)"""
        return [level.value for level in cls if level != cls.UNKNOWN]


class GameType(str, Enum):
    """Types of game sessions"""

    VOCABULARY = "vocabulary"
    LISTENING = "listening"
    COMPREHENSION = "comprehension"


class GameDifficulty(str, Enum):
    """Game difficulty levels"""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class GameSessionStatus(str, Enum):
    """Game session statuses"""

    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    ABANDONED = "abandoned"


class ProcessingStatus(str, Enum):
    """Video/audio processing statuses"""

    PENDING = "pending"
    STARTING = "starting"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    """Background task statuses"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class QuestionType(str, Enum):
    """Game question types"""

    MULTIPLE_CHOICE = "multiple_choice"
    FILL_BLANK = "fill_blank"
    TRANSLATION = "translation"
    LISTENING = "listening"


class WordType(str, Enum):
    """Parts of speech for vocabulary words"""

    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"
    PREPOSITION = "preposition"
    CONJUNCTION = "conjunction"
    ARTICLE = "article"
    PRONOUN = "pronoun"
    INTERJECTION = "interjection"
    UNKNOWN = "unknown"


class ConfidenceLevel(int, Enum):
    """User confidence levels for vocabulary knowledge"""

    UNKNOWN = 0
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    MASTERED = 4


class FilterDecision(str, Enum):
    """Vocabulary filtering decisions"""

    ACTIVE = "active"  # Word should be shown/learned
    SKIP = "skip"  # Word should be skipped (too easy/hard)
    KNOWN = "known"  # Word already known by user


__all__ = [
    "CEFRLevel",
    "GameType",
    "GameDifficulty",
    "GameSessionStatus",
    "ProcessingStatus",
    "TaskStatus",
    "QuestionType",
    "WordType",
    "ConfidenceLevel",
    "FilterDecision",
]
