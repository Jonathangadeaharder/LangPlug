"""Test data builders following the builder pattern for consistent test data creation."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class CEFRLevel(str, Enum):
    """CEFR levels for vocabulary testing."""

    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


@dataclass
class TestUser:
    """Test user data structure."""

    id: str | None = None
    username: str = ""
    email: str = ""
    password: str = "TestPass123!"
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime | None = None
    last_login: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {"username": self.username, "email": self.email, "password": self.password}


@dataclass
class TestVocabularyWord:
    """Test vocabulary concept data structure."""

    id: str | None = None
    word: str = ""
    level: str = "A1"
    language_code: str = "de"
    frequency_rank: int | None = None
    created_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {
            "word": self.word,
            "level": self.level,
            "language_code": self.language_code,
            "frequency_rank": self.frequency_rank,
        }


class UserBuilder:
    """Builder for creating test users with sensible defaults."""

    def __init__(self):
        self._reset()

    def _reset(self):
        """Reset builder to default state."""
        unique_id = str(uuid.uuid4())[:8]
        self._user = TestUser(
            id=str(uuid.uuid4()),
            username=f"testuser_{unique_id}",
            email=f"test_{unique_id}@example.com",
            created_at=datetime.now(UTC),
        )

    def with_username(self, username: str) -> UserBuilder:
        """Set custom username."""
        self._user.username = username
        return self

    def with_email(self, email: str) -> UserBuilder:
        """Set custom email."""
        self._user.email = email
        return self

    def with_password(self, password: str) -> UserBuilder:
        """Set custom password."""
        self._user.password = password
        return self

    def as_admin(self) -> UserBuilder:
        """Make user a superuser."""
        self._user.is_superuser = True
        return self

    def as_inactive(self) -> UserBuilder:
        """Make user inactive."""
        self._user.is_active = False
        return self

    def with_last_login(self, last_login: datetime | None = None) -> UserBuilder:
        """Set last login time."""
        self._user.last_login = last_login or datetime.now(UTC)
        return self

    def build(self) -> TestUser:
        """Build the user instance."""
        user = self._user
        self._reset()
        return user


class VocabularyWordBuilder:
    """Builder for creating test vocabulary concepts."""

    def __init__(self):
        self._reset()

    def _reset(self):
        """Reset builder to default state."""
        self._concept = TestVocabularyWord(
            id=str(uuid.uuid4()), word=f"testword_{str(uuid.uuid4())[:8]}", created_at=datetime.now(UTC)
        )

    def with_word(self, word: str) -> VocabularyWordBuilder:
        """Set custom word."""
        self._concept.word = word
        return self

    def with_level(self, level: CEFRLevel) -> VocabularyWordBuilder:
        """Set CEFR level."""
        self._concept.level = level.value
        return self

    def with_language(self, language_code: str) -> VocabularyWordBuilder:
        """Set language code."""
        self._concept.language_code = language_code
        return self

    def with_frequency_rank(self, rank: int) -> VocabularyWordBuilder:
        """Set frequency rank."""
        self._concept.frequency_rank = rank
        return self

    def build(self) -> TestVocabularyWord:
        """Build the concept instance."""
        concept = self._concept
        self._reset()
        return concept


class TestDataSets:
    """Predefined test data sets for common testing scenarios."""

    @staticmethod
    def create_basic_user() -> TestUser:
        """Create a basic test user."""
        return UserBuilder().build()

    @staticmethod
    def create_admin_user() -> TestUser:
        """Create an admin test user."""
        return UserBuilder().as_admin().build()

    @staticmethod
    def create_german_vocabulary_set() -> list[TestVocabularyWord]:
        """Create a set of German vocabulary words."""
        return [
            VocabularyWordBuilder()
            .with_word("das Haus")
            .with_level(CEFRLevel.A1)
            .with_language("de")
            .with_frequency_rank(100)
            .build(),
            VocabularyWordBuilder()
            .with_word("die Katze")
            .with_level(CEFRLevel.A1)
            .with_language("de")
            .with_frequency_rank(150)
            .build(),
            VocabularyWordBuilder()
            .with_word("verstehen")
            .with_level(CEFRLevel.A2)
            .with_language("de")
            .with_frequency_rank(300)
            .build(),
        ]

    @staticmethod
    def create_multilevel_vocabulary() -> dict[str, list[TestVocabularyWord]]:
        """Create vocabulary words across different CEFR levels."""
        return {
            "A1": [
                VocabularyWordBuilder().with_word("ich").with_level(CEFRLevel.A1).with_language("de").build(),
                VocabularyWordBuilder().with_word("du").with_level(CEFRLevel.A1).with_language("de").build(),
            ],
            "B1": [
                VocabularyWordBuilder().with_word("jedoch").with_level(CEFRLevel.B1).with_language("de").build(),
                VocabularyWordBuilder().with_word("obwohl").with_level(CEFRLevel.B1).with_language("de").build(),
            ],
            "C1": [
                VocabularyWordBuilder().with_word("diesbezüglich").with_level(CEFRLevel.C1).with_language("de").build()
            ],
        }


# Convenience functions for quick data creation
def create_user(**kwargs) -> TestUser:
    """Create a user with optional overrides."""
    builder = UserBuilder()
    user = builder.build()
    for key, value in kwargs.items():
        if hasattr(user, key):
            setattr(user, key, value)
    return user


def create_vocabulary_word(**kwargs) -> TestVocabularyWord:
    """Create a vocabulary word with optional overrides."""
    builder = VocabularyWordBuilder()
    word = builder.build()
    for key, value in kwargs.items():
        if hasattr(word, key):
            setattr(word, key, value)
    return word
