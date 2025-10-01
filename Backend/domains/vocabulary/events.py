"""
Domain events for the vocabulary domain.
Events represent things that have happened in the domain.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from .entities import DifficultyLevel, UserVocabularyProgress, VocabularyWord


class EventType(Enum):
    """Types of domain events"""

    WORD_LEARNED = "word_learned"
    WORD_MASTERED = "word_mastered"
    WORD_FORGOTTEN = "word_forgotten"
    LEVEL_COMPLETED = "level_completed"
    STREAK_ACHIEVED = "streak_achieved"
    VOCABULARY_ADDED = "vocabulary_added"
    PROGRESS_UPDATED = "progress_updated"


@dataclass
class DomainEvent:
    """Base class for all domain events"""

    event_id: str | None = None
    event_type: EventType | None = None
    occurred_at: datetime | None = None
    user_id: int | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if not self.event_id:
            import uuid

            self.event_id = str(uuid.uuid4())
        if not self.occurred_at:
            self.occurred_at = datetime.utcnow()


@dataclass
class WordLearnedEvent(DomainEvent):
    """Event fired when a user learns a new word"""

    vocabulary_word: VocabularyWord | None = None
    confidence_level: str | None = None
    learning_session_id: str | None = None

    def __post_init__(self):
        super().__post_init__()
        self.event_type = EventType.WORD_LEARNED


@dataclass
class WordMasteredEvent(DomainEvent):
    """Event fired when a user masters a word (high confidence + multiple correct answers)"""

    vocabulary_word: VocabularyWord | None = None
    success_rate: float | None = None
    review_count: int | None = None
    time_to_master_days: int | None = None

    def __post_init__(self):
        super().__post_init__()
        self.event_type = EventType.WORD_MASTERED


@dataclass
class WordForgottenEvent(DomainEvent):
    """Event fired when a user forgets a previously known word"""

    vocabulary_word: VocabularyWord | None = None
    previous_confidence_level: str | None = None
    incorrect_streak: int | None = None

    def __post_init__(self):
        super().__post_init__()
        self.event_type = EventType.WORD_FORGOTTEN


@dataclass
class LevelCompletedEvent(DomainEvent):
    """Event fired when a user completes a difficulty level"""

    difficulty_level: DifficultyLevel | None = None
    words_mastered: int | None = None
    completion_percentage: float | None = None
    time_to_complete_days: int | None = None

    def __post_init__(self):
        super().__post_init__()
        self.event_type = EventType.LEVEL_COMPLETED


@dataclass
class StreakAchievedEvent(DomainEvent):
    """Event fired when a user achieves a learning streak milestone"""

    streak_days: int | None = None
    milestone_type: str | None = None  # "daily", "weekly", "monthly"
    total_words_reviewed: int | None = None

    def __post_init__(self):
        super().__post_init__()
        self.event_type = EventType.STREAK_ACHIEVED


@dataclass
class VocabularyAddedEvent(DomainEvent):
    """Event fired when new vocabulary is added to the system"""

    vocabulary_word: VocabularyWord | None = None
    source: str | None = None  # "manual", "import", "discovered"
    batch_id: str | None = None

    def __post_init__(self):
        super().__post_init__()
        self.event_type = EventType.VOCABULARY_ADDED


@dataclass
class ProgressUpdatedEvent(DomainEvent):
    """Event fired when user progress is updated"""

    progress: UserVocabularyProgress | None = None
    previous_confidence: str | None = None
    action: str = "review"  # "review", "learn", "practice"

    def __post_init__(self):
        super().__post_init__()
        self.event_type = EventType.PROGRESS_UPDATED


class EventBus:
    """Simple event bus for domain events"""

    def __init__(self):
        self._handlers = {}
        self._events = []

    def register_handler(self, event_type: EventType, handler):
        """Register an event handler"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def publish(self, event: DomainEvent):
        """Publish a domain event"""
        self._events.append(event)

        # Call handlers for this event type
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                # Log error but don't fail the domain operation
                import logging

                logging.error(f"Error handling event {event.event_type}: {e}")

    def get_events(self) -> list:
        """Get all published events"""
        return self._events.copy()

    def clear_events(self):
        """Clear all events"""
        self._events.clear()


# Global event bus instance
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Get the global event bus"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def publish_event(event: DomainEvent):
    """Convenience function to publish an event"""
    bus = get_event_bus()
    bus.publish(event)
