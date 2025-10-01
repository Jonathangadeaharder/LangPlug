"""
Value objects for the vocabulary domain.
These are immutable objects that represent concepts without identity.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class Language:
    """Value object representing a language"""

    code: str  # ISO 639-1 code (e.g., "de", "en")
    name: str  # Human-readable name (e.g., "German", "English")
    native_name: str | None = None  # Native name (e.g., "Deutsch")

    def __post_init__(self):
        if not self.code or len(self.code) != 2:
            raise ValueError("Language code must be a 2-character ISO 639-1 code")
        if not self.name or not self.name.strip():
            raise ValueError("Language name cannot be empty")

    @property
    def is_german(self) -> bool:
        """Check if this is German"""
        return self.code.lower() == "de"

    @property
    def is_english(self) -> bool:
        """Check if this is English"""
        return self.code.lower() == "en"


@dataclass(frozen=True)
class WordFrequency:
    """Value object representing word frequency data"""

    rank: int  # Frequency rank (1 = most common)
    frequency: float | None = None  # Relative frequency (0.0 to 1.0)
    corpus_size: int | None = None  # Size of corpus used for frequency calculation

    def __post_init__(self):
        if self.rank <= 0:
            raise ValueError("Frequency rank must be positive")
        if self.frequency is not None and not (0.0 <= self.frequency <= 1.0):
            raise ValueError("Frequency must be between 0.0 and 1.0")

    @property
    def is_common(self) -> bool:
        """Check if word is common (top 1000)"""
        return self.rank <= 1000

    @property
    def is_rare(self) -> bool:
        """Check if word is rare (rank > 10000)"""
        return self.rank > 10000

    @property
    def frequency_category(self) -> str:
        """Get frequency category"""
        if self.rank <= 100:
            return "very_common"
        elif self.rank <= 1000:
            return "common"
        elif self.rank <= 5000:
            return "moderate"
        elif self.rank <= 10000:
            return "uncommon"
        else:
            return "rare"


@dataclass(frozen=True)
class LearningMetrics:
    """Value object representing learning performance metrics"""

    accuracy: float  # Success rate (0.0 to 1.0)
    response_time_ms: int  # Average response time in milliseconds
    retention_rate: float  # How well the knowledge is retained (0.0 to 1.0)
    effort_score: float  # Subjective difficulty (0.0 to 1.0)

    def __post_init__(self):
        if not (0.0 <= self.accuracy <= 1.0):
            raise ValueError("Accuracy must be between 0.0 and 1.0")
        if self.response_time_ms < 0:
            raise ValueError("Response time cannot be negative")
        if not (0.0 <= self.retention_rate <= 1.0):
            raise ValueError("Retention rate must be between 0.0 and 1.0")
        if not (0.0 <= self.effort_score <= 1.0):
            raise ValueError("Effort score must be between 0.0 and 1.0")

    @property
    def is_excellent(self) -> bool:
        """Check if performance is excellent"""
        return self.accuracy >= 0.9 and self.retention_rate >= 0.8

    @property
    def needs_improvement(self) -> bool:
        """Check if performance needs improvement"""
        return self.accuracy < 0.6 or self.retention_rate < 0.5

    @property
    def performance_grade(self) -> str:
        """Get performance grade"""
        if self.is_excellent:
            return "A"
        elif self.accuracy >= 0.8 and self.retention_rate >= 0.7:
            return "B"
        elif self.accuracy >= 0.7 and self.retention_rate >= 0.6:
            return "C"
        elif self.accuracy >= 0.6 and self.retention_rate >= 0.5:
            return "D"
        else:
            return "F"


@dataclass(frozen=True)
class SpacedRepetitionInterval:
    """Value object representing spaced repetition timing"""

    interval: timedelta
    ease_factor: float  # Multiplier for next interval (typically 1.3-2.5)
    repetition_number: int  # How many times this item has been reviewed

    def __post_init__(self):
        if self.interval.total_seconds() <= 0:
            raise ValueError("Interval must be positive")
        if not (1.0 <= self.ease_factor <= 3.0):
            raise ValueError("Ease factor must be between 1.0 and 3.0")
        if self.repetition_number < 0:
            raise ValueError("Repetition number cannot be negative")

    def calculate_next_interval(self, quality: int) -> "SpacedRepetitionInterval":
        """Calculate next repetition interval based on response quality (0-5)"""
        if not (0 <= quality <= 5):
            raise ValueError("Quality must be between 0 and 5")

        # SM-2 algorithm implementation
        if quality < 3:
            # Incorrect response, reset to 1 day
            return SpacedRepetitionInterval(
                interval=timedelta(days=1), ease_factor=max(1.3, self.ease_factor - 0.2), repetition_number=0
            )

        # Correct response
        new_ease = self.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        new_ease = max(1.3, new_ease)

        if self.repetition_number == 0:
            new_interval = timedelta(days=1)
        elif self.repetition_number == 1:
            new_interval = timedelta(days=6)
        else:
            days = int(self.interval.days * new_ease)
            new_interval = timedelta(days=max(1, days))

        return SpacedRepetitionInterval(
            interval=new_interval, ease_factor=new_ease, repetition_number=self.repetition_number + 1
        )

    @property
    def is_overdue(self) -> bool:
        """Check if review is overdue"""
        return datetime.utcnow() > (datetime.utcnow() - self.interval)


@dataclass(frozen=True)
class WordFormVariation:
    """Value object representing different forms of a word"""

    lemma: str  # Base form
    forms: dict[str, str]  # Form type -> form (e.g., {"plural": "words", "past": "worked"})

    def __post_init__(self):
        if not self.lemma or not self.lemma.strip():
            raise ValueError("Lemma cannot be empty")

    def get_form(self, form_type: str) -> str | None:
        """Get a specific word form"""
        return self.forms.get(form_type)

    @property
    def all_forms(self) -> list[str]:
        """Get all word forms including lemma"""
        forms = [self.lemma]
        forms.extend(self.forms.values())
        return list(set(forms))  # Remove duplicates

    def matches_any_form(self, word: str) -> bool:
        """Check if word matches any form"""
        word_lower = word.lower().strip()
        return word_lower in [form.lower().strip() for form in self.all_forms]


@dataclass(frozen=True)
class SemanticContext:
    """Value object representing semantic context of a word"""

    domain: str | None = None  # e.g., "technology", "medicine", "daily_life"
    register: str | None = None  # e.g., "formal", "informal", "colloquial"
    emotional_valence: str | None = None  # e.g., "positive", "negative", "neutral"
    usage_frequency: str | None = None  # e.g., "archaic", "modern", "emerging"

    @property
    def is_formal(self) -> bool:
        """Check if word is formal register"""
        return self.register == "formal"

    @property
    def is_specialized(self) -> bool:
        """Check if word belongs to a specialized domain"""
        specialized_domains = {"medicine", "law", "technology", "science", "academic"}
        return self.domain in specialized_domains

    @property
    def context_tags(self) -> list[str]:
        """Get all context tags as a list"""
        tags = []
        if self.domain:
            tags.append(f"domain:{self.domain}")
        if self.register:
            tags.append(f"register:{self.register}")
        if self.emotional_valence:
            tags.append(f"valence:{self.emotional_valence}")
        if self.usage_frequency:
            tags.append(f"usage:{self.usage_frequency}")
        return tags


@dataclass(frozen=True)
class LearningSession:
    """Value object representing a learning session"""

    session_id: str
    started_at: datetime
    ended_at: datetime | None = None
    session_type: str = "practice"  # "practice", "review", "test", "game"

    def __post_init__(self):
        if not self.session_id:
            raise ValueError("Session ID cannot be empty")
        if self.ended_at and self.ended_at < self.started_at:
            raise ValueError("End time cannot be before start time")

    @property
    def duration(self) -> timedelta | None:
        """Get session duration"""
        if self.ended_at:
            return self.ended_at - self.started_at
        return None

    @property
    def is_active(self) -> bool:
        """Check if session is still active"""
        return self.ended_at is None

    @property
    def duration_minutes(self) -> int | None:
        """Get duration in minutes"""
        if self.duration:
            return int(self.duration.total_seconds() / 60)
        return None
