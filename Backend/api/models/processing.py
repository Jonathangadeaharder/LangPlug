"""
Processing API models
"""
from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime
from .vocabulary import VocabularyWord


class TranscribeRequest(BaseModel):
    video_path: str = Field(
        ...,
        min_length=1,
        description="Path to the video file to transcribe"
    )
    
    @validator('video_path')
    def validate_video_path(cls, v):
        if not v.strip():
            raise ValueError('Video path cannot be empty or whitespace')
        # Check for common video file extensions
        valid_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}
        if not any(v.lower().endswith(ext) for ext in valid_extensions):
            raise ValueError(f'Path must end with a valid video extension: {", ".join(valid_extensions)}')
        return v


# VocabularyWord is imported from vocabulary.py to avoid duplication


class ProcessingStatus(BaseModel):
    status: Literal["starting", "processing", "completed", "error"] = Field(
        ...,
        description="Current processing status"
    )
    progress: float = Field(
        ...,
        ge=0,
        le=100,
        description="Processing progress percentage (0-100)"
    )
    current_step: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Description of the current processing step"
    )
    message: Optional[str] = Field(
        None,
        max_length=500,
        description="Additional status message or error details"
    )
    started_at: Optional[int] = Field(
        None,
        ge=0,
        description="Unix timestamp when processing started"
    )
    vocabulary: Optional[List[VocabularyWord]] = Field(
        None,
        description="Vocabulary words extracted from completed chunks"
    )
    subtitle_path: Optional[str] = Field(
        None,
        description="Path to German transcription subtitle file (yellow)"
    )
    translation_path: Optional[str] = Field(
        None,
        description="Path to English translation subtitle file (white)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "status": "processing",
                "progress": 45.5,
                "current_step": "Transcribing audio segment 3/8",
                "message": "Processing video chunks...",
                "started_at": 1640995200,
                "vocabulary": None,
                "subtitle_path": "/subtitles/video_german.srt",
                "translation_path": "/subtitles/video_english.srt"
            }
        }


class FilterRequest(BaseModel):
    video_path: str = Field(
        ...,
        min_length=1,
        description="Path to the video file to filter subtitles for"
    )
    
    @validator('video_path')
    def validate_video_path(cls, v):
        if not v.strip():
            raise ValueError('Video path cannot be empty or whitespace')
        return v


class TranslateRequest(BaseModel):
    video_path: str = Field(
        ...,
        min_length=1,
        description="Path to the video file to translate subtitles for"
    )
    source_lang: str = Field(
        ...,
        min_length=2,
        max_length=5,
        pattern=r"^[a-z]{2}(-[A-Z]{2})?$",
        description="Source language code (e.g., 'de', 'en-US')"
    )
    target_lang: str = Field(
        ...,
        min_length=2,
        max_length=5,
        pattern=r"^[a-z]{2}(-[A-Z]{2})?$",
        description="Target language code (e.g., 'en', 'de-DE')"
    )
    
    @validator('video_path')
    def validate_video_path(cls, v):
        if not v.strip():
            raise ValueError('Video path cannot be empty or whitespace')
        return v
    
    @validator('target_lang')
    def validate_different_languages(cls, v, values):
        if 'source_lang' in values and v == values['source_lang']:
            raise ValueError("Target language must be different from source language")
        return v


class FullPipelineRequest(BaseModel):
    video_path: str = Field(
        ...,
        min_length=1,
        description="Path to the video file to process"
    )
    source_lang: str = Field(
        "de",
        min_length=2,
        max_length=5,
        pattern=r"^[a-z]{2}(-[A-Z]{2})?$",
        description="Source language code (e.g., 'de', 'en-US')"
    )
    target_lang: str = Field(
        "en",
        min_length=2,
        max_length=5,
        pattern=r"^[a-z]{2}(-[A-Z]{2})?$",
        description="Target language code (e.g., 'en', 'de-DE')"
    )
    
    @validator('video_path')
    def validate_video_path(cls, v):
        if not v.strip():
            raise ValueError('Video path cannot be empty or whitespace')
        return v
    
    @validator('source_lang', 'target_lang')
    def validate_language_codes(cls, v):
        # List of valid ISO 639-1 language codes
        valid_codes = {'en', 'de', 'es', 'fr', 'it', 'pt', 'ru', 'ja', 'ko', 'zh', 'ar', 'hi', 'nl', 'sv', 'no', 'da', 'fi', 'pl', 'cs', 'hu', 'ro', 'bg', 'hr', 'sk', 'sl', 'et', 'lv', 'lt', 'mt', 'ga', 'cy', 'eu', 'ca', 'gl', 'tr', 'el', 'he', 'fa', 'ur', 'th', 'vi', 'id', 'ms', 'tl', 'sw', 'am', 'zu', 'xh', 'af', 'is', 'fo', 'kl'}
        base_code = v.split('-')[0].lower()
        if base_code not in valid_codes:
            raise ValueError(f'Invalid language code: {v}')
        return v
    
    @validator('target_lang')
    def validate_different_languages(cls, v, values):
        if 'source_lang' in values and v == values['source_lang']:
            raise ValueError('Source and target languages must be different')
        return v


class ChunkProcessingRequest(BaseModel):
    video_path: str = Field(
        ...,
        min_length=1,
        description="Path to the video file to process"
    )
    start_time: float = Field(
        ...,
        ge=0,
        description="Start time of the chunk in seconds"
    )
    end_time: float = Field(
        ...,
        gt=0,
        description="End time of the chunk in seconds"
    )
    
    @validator('video_path')
    def validate_video_path(cls, v):
        if not v.strip():
            raise ValueError('Video path cannot be empty or whitespace')
        return v
    
    @validator('end_time')
    def validate_time_range(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be greater than start time')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "video_path": "/videos/Superstore/S01/E01.mp4",
                "start_time": 120.5,
                "end_time": 180.0
            }
        }