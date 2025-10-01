"""
Vocabulary domain models and DTOs
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VocabularyWordBase(BaseModel):
    """Base vocabulary word model"""

    word: str
    lemma: str
    language: str = "de"
    difficulty_level: str
    part_of_speech: str | None = None
    gender: str | None = None
    translation_en: str | None = None
    translation_native: str | None = None
    pronunciation: str | None = None
    notes: str | None = None
    frequency_rank: int | None = None


class VocabularyWordResponse(VocabularyWordBase):
    """Vocabulary word response model"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class UserVocabularyProgressBase(BaseModel):
    """Base user vocabulary progress model"""

    is_known: bool
    confidence_level: int = 0
    review_count: int = 0


class UserVocabularyProgressResponse(UserVocabularyProgressBase):
    """User vocabulary progress response model"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    vocabulary_id: int
    lemma: str
    language: str
    first_seen_at: datetime
    last_reviewed_at: datetime | None = None
    vocabulary: VocabularyWordResponse | None = None


class VocabularySearchRequest(BaseModel):
    """Vocabulary search request"""

    query: str
    language: str = "de"
    limit: int = 20


class VocabularyByLevelRequest(BaseModel):
    """Request vocabulary by difficulty level"""

    level: str
    language: str = "de"
    skip: int = 0
    limit: int = 100


class MarkWordRequest(BaseModel):
    """Mark word as known/unknown request"""

    vocabulary_id: int
    is_known: bool


class BulkMarkWordsRequest(BaseModel):
    """Bulk mark words request"""

    vocabulary_ids: list[int]
    is_known: bool


class VocabularyStatsResponse(BaseModel):
    """Vocabulary statistics response"""

    total_reviewed: int
    known_words: int
    unknown_words: int
    percentage_known: float
    level_breakdown: dict | None = None


class WordNotFoundRequest(BaseModel):
    """Report word not found in vocabulary"""

    word: str
    lemma: str | None = None
    language: str = "de"
    context: str | None = None
