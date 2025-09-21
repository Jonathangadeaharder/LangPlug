"""
Vocabulary API models
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict


class VocabularyWord(BaseModel):
    word: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="The vocabulary word"
    )
    definition: str | None = Field(
        None,
        max_length=500,
        description="Definition of the word"
    )
    difficulty_level: str = Field(
        ...,
        pattern=r"^(A1|A2|B1|B2|C1|C2)$",
        description="CEFR difficulty level (A1, A2, B1, B2, C1, C2)"
    )
    known: bool = Field(
        False,
        description="Whether the user knows this word"
    )

    @field_validator('word')
    @classmethod
    def validate_word(cls, v):
        if not v.strip():
            raise ValueError('Word cannot be empty or whitespace')
        return v.strip().lower()


class MarkKnownRequest(BaseModel):
    word: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="The word to mark as known/unknown"
    )
    known: bool = Field(
        ...,
        description="Whether to mark the word as known (true) or unknown (false)"
    )

    @field_validator('word')
    @classmethod
    def validate_word(cls, v):
        if not v.strip():
            raise ValueError('Word cannot be empty or whitespace')
        return v.strip().lower()


class VocabularyLibraryWord(BaseModel):
    id: int = Field(
        ...,
        gt=0,
        description="Unique identifier for the vocabulary word"
    )
    word: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="The vocabulary word"
    )
    difficulty_level: str = Field(
        ...,
        pattern=r"^(A1|A2|B1|B2|C1|C2)$",
        description="CEFR difficulty level (A1, A2, B1, B2, C1, C2)"
    )
    part_of_speech: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Part of speech (noun, verb, adjective, etc.)"
    )
    definition: str | None = Field(
        None,
        max_length=500,
        description="Definition of the word"
    )
    known: bool = Field(
        False,
        description="Whether the user knows this word"
    )


class VocabularyLevel(BaseModel):
    level: str = Field(
        ...,
        pattern=r"^(A1|A2|B1|B2|C1|C2)$",
        description="CEFR difficulty level (A1, A2, B1, B2, C1, C2)"
    )
    words: list[VocabularyLibraryWord] = Field(
        ...,
        description="List of vocabulary words at this level"
    )
    total_count: int = Field(
        ...,
        ge=0,
        description="Total number of words at this level"
    )
    known_count: int = Field(
        ...,
        ge=0,
        description="Number of known words at this level"
    )

    @field_validator('known_count')
    @classmethod
    def validate_known_count(cls, v, info):
        if 'total_count' in info.data and v > info.data['total_count']:
            raise ValueError('Known count cannot exceed total count')
        return v


class BulkMarkRequest(BaseModel):
    level: str = Field(
        ...,
        pattern=r"^(A1|A2|B1|B2|C1|C2)$",
        description="CEFR difficulty level to mark (A1, A2, B1, B2, C1, C2)"
    )
    known: bool = Field(
        ...,
        description="Whether to mark all words in the level as known (true) or unknown (false)"
    )


class VocabularyStats(BaseModel):
    levels: dict[str, dict[str, int]] = Field(
        ...,
        description="Statistics by CEFR level with total and known counts"
    )
    total_words: int = Field(
        ...,
        ge=0,
        description="Total number of vocabulary words across all levels"
    )
    total_known: int = Field(
        ...,
        ge=0,
        description="Total number of known words across all levels"
    )

    @field_validator('total_known')
    @classmethod
    def validate_total_known(cls, v, info):
        if 'total_words' in info.data and v > info.data['total_words']:
            raise ValueError('Total known cannot exceed total words')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "levels": {
                    "A1": {"total": 100, "known": 80},
                    "A2": {"total": 150, "known": 60},
                    "B1": {"total": 200, "known": 40}
                },
                "total_words": 450,
                "total_known": 180
            }
        }
    )
