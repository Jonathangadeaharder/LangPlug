"""
Progress Data Transfer Objects
API request/response models for user progress tracking
"""

from datetime import date, datetime

from pydantic import BaseModel, Field


class UserProgressDTO(BaseModel):
    """DTO for user learning progress"""

    total_words: int = Field(default=0, ge=0, description="Total words encountered")
    known_words: int = Field(default=0, ge=0, description="Words marked as known")
    learning_words: int = Field(default=0, ge=0, description="Words currently learning")
    mastered_words: int = Field(default=0, ge=0, description="Words fully mastered")
    review_due: int = Field(default=0, ge=0, description="Words due for review")
    daily_streak: int = Field(default=0, ge=0, description="Consecutive days of activity")
    total_study_time: int = Field(default=0, ge=0, description="Total study time in minutes")
    level: str | None = Field(None, description="Current CEFR level (A1-C2)")
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Overall progress (0-100%)")


class DailyProgressDTO(BaseModel):
    """DTO for daily progress entry"""

    entry_date: date = Field(..., description="Date of progress entry")
    words_learned: int = Field(default=0, ge=0, description="Words learned on this day")
    words_reviewed: int = Field(default=0, ge=0, description="Words reviewed on this day")
    study_time_minutes: int = Field(default=0, ge=0, description="Study time in minutes")
    accuracy: float | None = Field(None, ge=0.0, le=100.0, description="Quiz accuracy percentage")
    created_at: datetime | None = Field(None, description="Entry creation timestamp")
