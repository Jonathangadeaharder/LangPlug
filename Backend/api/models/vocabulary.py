"""
Vocabulary API models for multilingual support
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class VocabularyWord(BaseModel):
    """Single vocabulary word with translations"""

    concept_id: UUID | None = Field(None, description="Unique identifier (optional, will be deprecated)")
    word: str = Field(..., min_length=1, max_length=100, description="The vocabulary word in target language")
    translation: str | None = Field(None, max_length=100, description="Translation in user's preferred language")
    lemma: str | None = Field(None, max_length=100, description="Base form of the word")
    difficulty_level: str = Field(..., pattern=r"^(A1|A2|B1|B2|C1|C2)$", description="CEFR difficulty level")
    semantic_category: str | None = Field(
        None, max_length=50, description="Part of speech (noun, verb, adjective, etc.)"
    )
    domain: str | None = Field(None, max_length=50, description="Domain category (education, technology, etc.)")
    gender: str | None = Field(None, max_length=10, description="Gender (der/die/das for German, el/la for Spanish)")
    plural_form: str | None = Field(None, max_length=100, description="Plural form if applicable")
    pronunciation: str | None = Field(None, max_length=200, description="IPA or phonetic representation")
    notes: str | None = Field(None, max_length=500, description="Grammar notes, usage notes, etc.")
    known: bool = Field(False, description="Whether the user knows this word")

    model_config = ConfigDict(
        # Forbid extra fields - will raise ValidationError if dict has unexpected keys
        extra="forbid",
        # Validate on assignment to catch issues early
        validate_assignment=True,
        # Strict mode - stricter type checking
        strict=False,  # Keep False for flexibility with string/UUID conversion
        # Custom JSON schema for OpenAPI documentation
        json_schema_extra={
            "example": {
                "concept_id": "550e8400-e29b-41d4-a716-446655440000",
                "word": "Haus",
                "translation": "house",
                "lemma": "haus",
                "difficulty_level": "A1",
                "semantic_category": "noun",
                "domain": "housing",
                "gender": "das",
                "known": False,
            }
        },
    )


class MarkKnownRequest(BaseModel):
    """Request to mark a word as known/unknown"""

    concept_id: UUID = Field(..., description="Unique concept identifier")
    known: bool = Field(..., description="Whether to mark the word as known (true) or unknown (false)")


class VocabularyLibraryWord(BaseModel):
    """Vocabulary word for library display with full details"""

    concept_id: UUID = Field(..., description="Unique concept identifier")
    word: str = Field(..., min_length=1, max_length=100, description="The vocabulary word in target language")
    translation: str | None = Field(None, max_length=100, description="Translation in user's preferred language")
    lemma: str | None = Field(None, max_length=100, description="Base form of the word")
    difficulty_level: str = Field(..., pattern=r"^(A1|A2|B1|B2|C1|C2)$", description="CEFR difficulty level")
    semantic_category: str | None = Field(
        None, max_length=50, description="Part of speech (noun, verb, adjective, etc.)"
    )
    domain: str | None = Field(None, max_length=50, description="Domain category")
    gender: str | None = Field(None, max_length=10, description="Gender for gendered languages")
    plural_form: str | None = Field(None, max_length=100, description="Plural form if applicable")
    pronunciation: str | None = Field(None, max_length=200, description="Pronunciation guide")
    notes: str | None = Field(None, max_length=500, description="Additional notes")
    known: bool = Field(False, description="Whether the user knows this word")


class VocabularyLevel(BaseModel):
    """Vocabulary words grouped by CEFR level"""

    level: str = Field(..., pattern=r"^(A1|A2|B1|B2|C1|C2)$", description="CEFR difficulty level")
    target_language: str = Field(..., min_length=2, max_length=5, description="Target language code (de, es, en, etc.)")
    translation_language: str | None = Field(None, min_length=2, max_length=5, description="Translation language code")
    words: list[VocabularyLibraryWord] = Field(..., description="List of vocabulary words at this level")
    total_count: int = Field(..., ge=0, description="Total number of words at this level")
    known_count: int = Field(..., ge=0, description="Number of known words at this level")


class BulkMarkRequest(BaseModel):
    """Request to bulk mark words as known/unknown"""

    level: str = Field(..., pattern=r"^(A1|A2|B1|B2|C1|C2)$", description="CEFR difficulty level to mark")
    target_language: str = Field(..., min_length=2, max_length=5, description="Target language code (de, es, en, etc.)")
    known: bool = Field(..., description="Whether to mark all words as known (true) or unknown (false)")


class VocabularyStats(BaseModel):
    """Vocabulary statistics across all levels"""

    levels: dict[str, dict[str, int]] = Field(..., description="Statistics by CEFR level with total and known counts")
    target_language: str = Field(..., min_length=2, max_length=5, description="Target language code")
    translation_language: str | None = Field(None, min_length=2, max_length=5, description="Translation language code")
    total_words: int = Field(..., ge=0, description="Total number of vocabulary words across all levels")
    total_known: int = Field(..., ge=0, description="Total number of known words across all levels")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "levels": {
                    "A1": {"total_words": 100, "user_known": 80},
                    "A2": {"total_words": 150, "user_known": 60},
                    "B1": {"total_words": 200, "user_known": 40},
                },
                "target_language": "de",
                "translation_language": "es",
                "total_words": 450,
                "total_known": 180,
            }
        }
    )


class LanguageRequest(BaseModel):
    """Request for language-specific operations"""

    target_language: str = Field(..., min_length=2, max_length=5, description="Target language code (de, es, en, etc.)")
    translation_language: str | None = Field(None, min_length=2, max_length=5, description="Translation language code")


class SupportedLanguage(BaseModel):
    """Supported language information"""

    code: str = Field(..., min_length=2, max_length=5, description="Language code (de, es, en, etc.)")
    name: str = Field(..., min_length=1, max_length=50, description="Language name in English")
    native_name: str | None = Field(None, max_length=50, description="Language name in native script")
    is_active: bool = Field(True, description="Whether the language is currently supported")


class LanguagesResponse(BaseModel):
    """Response containing supported languages"""

    languages: list[SupportedLanguage] = Field(..., description="List of supported languages")


class TranslationPair(BaseModel):
    """Translation pair for vocabulary import"""

    german: str = Field(..., min_length=1, max_length=100, description="German word")
    spanish: str = Field(..., min_length=1, max_length=100, description="Spanish translation")
    difficulty_level: str = Field(..., pattern=r"^(A1|A2|B1|B2|C1|C2)$", description="CEFR difficulty level")


class ImportRequest(BaseModel):
    """Request to import vocabulary data"""

    translation_pairs: list[TranslationPair] = Field(
        ..., min_length=1, description="List of translation pairs to import"
    )
    overwrite_existing: bool = Field(False, description="Whether to overwrite existing concepts")
