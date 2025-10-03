"""
Vocabulary Data Transfer Objects
Clean API representations without database dependencies with input validation
"""

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.enums import CEFRLevel

# Valid language codes (ISO 639-1)
VALID_LANGUAGES = {"de", "en", "es", "fr", "it", "pt", "ru", "zh", "ja", "ko"}


class VocabularyWordDTO(BaseModel):
    """DTO for vocabulary word representation with validation"""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    word: str = Field(min_length=1, max_length=200, description="The vocabulary word")
    lemma: str | None = Field(None, max_length=200, description="Base form of the word")
    difficulty_level: str = Field(description="CEFR difficulty level")
    language: str = Field(min_length=2, max_length=5, description="ISO 639-1 language code")
    part_of_speech: str | None = Field(None, max_length=50)
    frequency: int | None = Field(None, ge=0, description="Word frequency rank")
    example_sentence: str | None = Field(None, max_length=1000)
    definition: str | None = Field(None, max_length=2000)
    is_known: bool | None = None

    @field_validator("word", "lemma")
    @classmethod
    def validate_word(cls, v: str | None) -> str | None:
        """Validate word contains only valid characters"""
        if v is None:
            return v
        # Allow letters, numbers, hyphens, apostrophes, and spaces
        if not re.match(r"^[\w\s\-'äöüÄÖÜßàâéèêëïîôùûç]+$", v, re.UNICODE):
            raise ValueError("Word contains invalid characters")
        return v.strip()

    @field_validator("difficulty_level")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        """Validate difficulty level"""
        valid_levels = {level.value for level in CEFRLevel}
        if v not in valid_levels:
            raise ValueError(f"Invalid difficulty level. Must be one of {valid_levels}")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language code"""
        v_lower = v.lower()
        if v_lower not in VALID_LANGUAGES:
            raise ValueError(f"Invalid language code. Must be one of {VALID_LANGUAGES}")
        return v_lower


class UserProgressDTO(BaseModel):
    """DTO for user vocabulary progress with validation"""

    model_config = ConfigDict(from_attributes=True)

    user_id: int = Field(gt=0, description="User ID")
    word: str = Field(min_length=1, max_length=200)
    language: str = Field(min_length=2, max_length=5)
    is_known: bool
    last_reviewed: str | None = Field(None, max_length=50)
    review_count: int = Field(default=0, ge=0)
    confidence_level: float | None = Field(None, ge=0.0, le=1.0)

    @field_validator("word")
    @classmethod
    def validate_word(cls, v: str) -> str:
        """Validate word contains only valid characters"""
        if not re.match(r"^[\w\s\-'äöüÄÖÜßàâéèêëïîôùûç]+$", v, re.UNICODE):
            raise ValueError("Word contains invalid characters")
        return v.strip()

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language code"""
        v_lower = v.lower()
        if v_lower not in VALID_LANGUAGES:
            raise ValueError(f"Invalid language code. Must be one of {VALID_LANGUAGES}")
        return v_lower


class VocabularyLibraryDTO(BaseModel):
    """DTO for vocabulary library response with validation"""

    model_config = ConfigDict(from_attributes=True)

    total_count: int = Field(ge=0)
    words: list[VocabularyWordDTO]
    page: int = Field(default=1, ge=1, le=10000)
    per_page: int = Field(default=100, ge=1, le=1000)
    has_more: bool = False


class VocabularySearchDTO(BaseModel):
    """DTO for vocabulary search results with query sanitization"""

    model_config = ConfigDict(from_attributes=True)

    query: str = Field(min_length=1, max_length=200, description="Search query")
    results: list[VocabularyWordDTO]
    total_matches: int = Field(ge=0)
    search_time_ms: float | None = Field(None, ge=0)

    @field_validator("query")
    @classmethod
    def sanitize_query(cls, v: str) -> str:
        """Sanitize search query to prevent SQL injection"""
        # Remove any SQL special characters and trim
        sanitized = re.sub(r"[;\'\"\\]", "", v)
        sanitized = sanitized.strip()
        if not sanitized:
            raise ValueError("Query cannot be empty after sanitization")
        return sanitized


class VocabularyStatsDTO(BaseModel):
    """DTO for vocabulary statistics with validation"""

    model_config = ConfigDict(from_attributes=True)

    total_words: int = Field(ge=0)
    known_words: int = Field(ge=0)
    unknown_words: int = Field(ge=0)
    level_distribution: dict = Field(default_factory=dict)
    recent_progress: list[UserProgressDTO] = Field(default_factory=list, max_length=100)
