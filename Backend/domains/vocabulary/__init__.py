"""
Vocabulary Domain Module

This module contains the vocabulary domain implementation following Domain-Driven Design principles.
It includes entities, value objects, domain services, events, and repository interfaces.
"""

# Entities
# Domain Services
from .domain_services import LearningProgressCalculator, SpacedRepetitionScheduler, VocabularyDifficultyAnalyzer
from .entities import (
    ConfidenceLevel,
    DifficultyLevel,
    LearningSession,
    UserVocabularyProgress,
    VocabularyWord,
    WordType,
)

# Events
from .events import (
    DomainEvent,
    EventBus,
    EventType,
    LevelCompletedEvent,
    ProgressUpdatedEvent,
    StreakAchievedEvent,
    VocabularyAddedEvent,
    WordForgottenEvent,
    WordLearnedEvent,
    WordMasteredEvent,
    get_event_bus,
    publish_event,
)

# Repository Interfaces
from .repositories import (
    LearningSessionDomainRepository,
    UserProgressDomainRepository,
    VocabularyDomainRepository,
    VocabularyDomainUnitOfWork,
)

# Value Objects
from .value_objects import (
    Language,
    LearningMetrics,
    SemanticContext,
    SpacedRepetitionInterval,
    WordFormVariation,
    WordFrequency,
)

__all__ = [
    "ConfidenceLevel",
    "DifficultyLevel",
    # Events
    "DomainEvent",
    "EventBus",
    "EventType",
    # Value Objects
    "Language",
    "LearningMetrics",
    "LearningProgressCalculator",
    "LearningSession",
    "LearningSessionDomainRepository",
    "LevelCompletedEvent",
    "ProgressUpdatedEvent",
    "SemanticContext",
    "SpacedRepetitionInterval",
    "SpacedRepetitionScheduler",
    "StreakAchievedEvent",
    "UserProgressDomainRepository",
    "UserVocabularyProgress",
    "VocabularyAddedEvent",
    # Domain Services
    "VocabularyDifficultyAnalyzer",
    # Repository Interfaces
    "VocabularyDomainRepository",
    "VocabularyDomainUnitOfWork",
    # Entities
    "VocabularyWord",
    "WordForgottenEvent",
    "WordFormVariation",
    "WordFrequency",
    "WordLearnedEvent",
    "WordMasteredEvent",
    "WordType",
    "get_event_bus",
    "publish_event",
]
