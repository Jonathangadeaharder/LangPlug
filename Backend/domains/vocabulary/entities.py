"""
Domain entities for the vocabulary domain.
These represent core business concepts independent of infrastructure concerns.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from core.enums import CEFRLevel, ConfidenceLevel, WordType

# Alias for domain-specific naming (same as CEFRLevel)
DifficultyLevel = CEFRLevel


@dataclass
class VocabularyWord:
    """Domain entity representing a vocabulary word"""

    id: int | None
    word: str
    lemma: str
    language: str
    difficulty_level: DifficultyLevel
    word_type: WordType
    definition: str | None = None
    example_sentence: str | None = None
    pronunciation: str | None = None
    etymology: str | None = None
    frequency_rank: int | None = None
    translations: dict[str, str] | None = None
    related_words: list[str] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self):
        """Validate entity after initialization"""
        if not self.word or not self.word.strip():
            raise ValueError("Word cannot be empty")
        if not self.lemma or not self.lemma.strip():
            raise ValueError("Lemma cannot be empty")
        if not self.language or len(self.language) != 2:
            raise ValueError("Language must be a 2-character ISO code")

    @property
    def is_german(self) -> bool:
        """Check if word is German"""
        return self.language.lower() == "de"

    @property
    def is_beginner_level(self) -> bool:
        """Check if word is beginner level (A1/A2)"""
        return self.difficulty_level in [DifficultyLevel.A1, DifficultyLevel.A2]

    @property
    def is_advanced_level(self) -> bool:
        """Check if word is advanced level (C1/C2)"""
        return self.difficulty_level in [DifficultyLevel.C1, DifficultyLevel.C2]

    def get_translation(self, target_language: str) -> str | None:
        """Get translation for target language"""
        if self.translations:
            return self.translations.get(target_language)
        return None

    def add_translation(self, language: str, translation: str) -> None:
        """Add translation for a language"""
        if self.translations is None:
            self.translations = {}
        self.translations[language] = translation

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "word": self.word,
            "lemma": self.lemma,
            "language": self.language,
            "difficulty_level": self.difficulty_level.value,
            "word_type": self.word_type.value,
            "definition": self.definition,
            "example_sentence": self.example_sentence,
            "pronunciation": self.pronunciation,
            "etymology": self.etymology,
            "frequency_rank": self.frequency_rank,
            "translations": self.translations,
            "related_words": self.related_words,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class UserVocabularyProgress:
    """Domain entity representing user's progress with a vocabulary word"""

    id: int | None
    user_id: int
    vocabulary_word: VocabularyWord
    is_known: bool
    confidence_level: ConfidenceLevel
    review_count: int = 0
    correct_count: int = 0
    incorrect_count: int = 0
    first_learned_at: datetime | None = None
    last_reviewed_at: datetime | None = None
    next_review_at: datetime | None = None
    difficulty_adjustment: float = 1.0
    learning_streak: int = 0
    notes: str | None = None

    def __post_init__(self):
        """Validate entity after initialization"""
        if self.user_id <= 0:
            raise ValueError("User ID must be positive")
        if self.review_count < 0:
            raise ValueError("Review count cannot be negative")
        if self.correct_count < 0:
            raise ValueError("Correct count cannot be negative")
        if self.incorrect_count < 0:
            raise ValueError("Incorrect count cannot be negative")

    @property
    def success_rate(self) -> float:
        """Calculate success rate for this word"""
        total_attempts = self.correct_count + self.incorrect_count
        if total_attempts == 0:
            return 0.0
        return self.correct_count / total_attempts

    @property
    def needs_review(self) -> bool:
        """Check if word needs review based on schedule"""
        if self.next_review_at is None:
            return True
        return datetime.utcnow() >= self.next_review_at

    @property
    def is_mastered(self) -> bool:
        """Check if word is considered mastered"""
        return self.confidence_level == ConfidenceLevel.MASTERED and self.success_rate >= 0.9 and self.review_count >= 5

    def mark_correct(self) -> None:
        """Mark a correct answer and update statistics"""
        self.correct_count += 1
        self.review_count += 1
        self.learning_streak += 1
        self.last_reviewed_at = datetime.utcnow()

        # Improve confidence if streak is good
        if self.learning_streak >= 3 and self.confidence_level.value < ConfidenceLevel.MASTERED.value:
            new_level = ConfidenceLevel(min(self.confidence_level.value + 1, ConfidenceLevel.MASTERED.value))
            self.confidence_level = new_level

    def mark_incorrect(self) -> None:
        """Mark an incorrect answer and update statistics"""
        self.incorrect_count += 1
        self.review_count += 1
        self.learning_streak = 0
        self.last_reviewed_at = datetime.utcnow()

        # Decrease confidence
        if self.confidence_level.value > ConfidenceLevel.UNKNOWN.value:
            new_level = ConfidenceLevel(max(self.confidence_level.value - 1, ConfidenceLevel.UNKNOWN.value))
            self.confidence_level = new_level

    def calculate_next_review(self) -> datetime:
        """Calculate when this word should be reviewed next"""
        base_interval_hours = {
            ConfidenceLevel.UNKNOWN: 1,
            ConfidenceLevel.WEAK: 4,
            ConfidenceLevel.MODERATE: 12,
            ConfidenceLevel.STRONG: 48,
            ConfidenceLevel.MASTERED: 168,  # 1 week
        }

        interval = base_interval_hours[self.confidence_level]
        # Adjust based on success rate
        if self.success_rate < 0.5:
            interval = int(interval * 0.5)
        elif self.success_rate > 0.8:
            interval = int(interval * 1.5)

        from datetime import timedelta

        return datetime.utcnow() + timedelta(hours=interval)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "vocabulary_word": self.vocabulary_word.to_dict(),
            "is_known": self.is_known,
            "confidence_level": self.confidence_level.value,
            "review_count": self.review_count,
            "correct_count": self.correct_count,
            "incorrect_count": self.incorrect_count,
            "success_rate": self.success_rate,
            "first_learned_at": self.first_learned_at.isoformat() if self.first_learned_at else None,
            "last_reviewed_at": self.last_reviewed_at.isoformat() if self.last_reviewed_at else None,
            "next_review_at": self.next_review_at.isoformat() if self.next_review_at else None,
            "difficulty_adjustment": self.difficulty_adjustment,
            "learning_streak": self.learning_streak,
            "notes": self.notes,
            "needs_review": self.needs_review,
            "is_mastered": self.is_mastered,
        }


@dataclass
class LearningSession:
    """Domain entity representing a learning session"""

    id: int | None
    user_id: int
    session_type: str  # "review", "learning", "game"
    language: str
    difficulty_level: DifficultyLevel | None = None
    words_studied: list[VocabularyWord] = None
    correct_answers: int = 0
    incorrect_answers: int = 0
    session_duration_minutes: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    notes: str | None = None

    def __post_init__(self):
        if self.words_studied is None:
            self.words_studied = []

    @property
    def accuracy(self) -> float:
        """Calculate session accuracy"""
        total = self.correct_answers + self.incorrect_answers
        if total == 0:
            return 0.0
        return self.correct_answers / total

    @property
    def is_completed(self) -> bool:
        """Check if session is completed"""
        return self.completed_at is not None

    def add_word_result(self, word: VocabularyWord, correct: bool) -> None:
        """Add result for a word in this session"""
        if word not in self.words_studied:
            self.words_studied.append(word)

        if correct:
            self.correct_answers += 1
        else:
            self.incorrect_answers += 1

    def complete_session(self) -> None:
        """Mark session as completed"""
        if self.completed_at is None:
            self.completed_at = datetime.utcnow()
            if self.started_at:
                duration = self.completed_at - self.started_at
                self.session_duration_minutes = int(duration.total_seconds() / 60)
