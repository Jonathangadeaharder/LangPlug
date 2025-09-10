"""
Vocabulary API models
"""
from typing import Optional, List, Dict
from pydantic import BaseModel


class VocabularyWord(BaseModel):
    word: str
    definition: Optional[str] = None
    difficulty_level: str
    known: bool = False


class MarkKnownRequest(BaseModel):
    word: str
    known: bool


class VocabularyLibraryWord(BaseModel):
    id: int
    word: str
    difficulty_level: str
    part_of_speech: str
    definition: Optional[str] = None
    known: bool = False


class VocabularyLevel(BaseModel):
    level: str
    words: List[VocabularyLibraryWord]
    total_count: int
    known_count: int


class BulkMarkRequest(BaseModel):
    level: str
    known: bool


class VocabularyStats(BaseModel):
    levels: Dict[str, Dict[str, int]]
    total_words: int
    total_known: int