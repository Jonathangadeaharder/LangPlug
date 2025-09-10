"""
Processing API models
"""
from typing import Optional, List, Literal
from pydantic import BaseModel


class TranscribeRequest(BaseModel):
    video_path: str


class VocabularyWord(BaseModel):
    word: str
    definition: Optional[str] = None
    difficulty_level: str
    known: bool


class ProcessingStatus(BaseModel):
    status: Literal["starting", "processing", "completed", "error"]
    progress: float  # 0-100
    current_step: str
    message: Optional[str] = None
    started_at: Optional[int] = None  # timestamp
    vocabulary: Optional[List[VocabularyWord]] = None  # Vocabulary words for completed chunks
    subtitle_path: Optional[str] = None     # Path to filtered subtitle file


class FilterRequest(BaseModel):
    video_path: str


class TranslateRequest(BaseModel):
    video_path: str
    source_lang: str
    target_lang: str


class ChunkProcessingRequest(BaseModel):
    video_path: str
    start_time: float  # seconds
    end_time: float    # seconds