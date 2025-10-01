"""
Processing API models
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .vocabulary import VocabularyWord


class TranscribeRequest(BaseModel):
    video_path: str = Field(..., min_length=1, description="Path to the video file to transcribe")


# VocabularyWord is imported from vocabulary.py to avoid duplication


class ProcessingStatus(BaseModel):
    status: Literal["starting", "processing", "completed", "error"] = Field(
        ..., description="Current processing status"
    )
    progress: float = Field(..., ge=0, le=100, description="Processing progress percentage (0-100)")
    current_step: str = Field(
        ..., min_length=1, max_length=200, description="Description of the current processing step"
    )
    message: str | None = Field(None, max_length=500, description="Additional status message or error details")
    started_at: int | None = Field(None, ge=0, description="Unix timestamp when processing started")
    vocabulary: list[VocabularyWord] | None = Field(
        None, description="Vocabulary words extracted from completed chunks"
    )
    subtitle_path: str | None = Field(None, description="Path to German transcription subtitle file (yellow)")
    translation_path: str | None = Field(None, description="Path to English translation subtitle file (white)")

    model_config = ConfigDict(
        # Allow extra fields for flexibility (background tasks may add custom fields)
        extra="allow",
        # Validate on assignment to catch issues when setting vocabulary
        validate_assignment=True,
        json_schema_extra={
            "example": {
                "status": "processing",
                "progress": 45.5,
                "current_step": "Transcribing audio segment 3/8",
                "message": "Processing video chunks...",
                "started_at": 1640995200,
                "vocabulary": None,
                "subtitle_path": "/subtitles/video_german.srt",
                "translation_path": "/subtitles/video_english.srt",
            }
        },
    )


class FilterRequest(BaseModel):
    video_path: str = Field(..., min_length=1, description="Path to the video file to filter subtitles for")


class TranslateRequest(BaseModel):
    video_path: str = Field(..., min_length=1, description="Path to the video file to translate subtitles for")
    source_lang: str = Field(
        ...,
        min_length=2,
        max_length=5,
        pattern=r"^[a-z]{2}(-[A-Z]{2})?$",
        description="Source language code (e.g., 'de', 'en-US')",
    )
    target_lang: str = Field(
        ...,
        min_length=2,
        max_length=5,
        pattern=r"^[a-z]{2}(-[A-Z]{2})?$",
        description="Target language code (e.g., 'en', 'de-DE')",
    )


class FullPipelineRequest(BaseModel):
    video_path: str = Field(..., min_length=1, description="Path to the video file to process")
    source_lang: str = Field(
        "de",
        min_length=2,
        max_length=5,
        pattern=r"^[a-z]{2}(-[A-Z]{2})?$",
        description="Source language code (e.g., 'de', 'en-US')",
    )
    target_lang: str = Field(
        "en",
        min_length=2,
        max_length=5,
        pattern=r"^[a-z]{2}(-[A-Z]{2})?$",
        description="Target language code (e.g., 'en', 'de-DE')",
    )


class ChunkProcessingRequest(BaseModel):
    video_path: str = Field(..., min_length=1, description="Path to the video file to process")
    start_time: float = Field(..., ge=0, description="Start time of the chunk in seconds")
    end_time: float = Field(..., gt=0, description="End time of the chunk in seconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"video_path": "/videos/Superstore/S01/E01.mp4", "start_time": 120.5, "end_time": 180.0}
        }
    )
