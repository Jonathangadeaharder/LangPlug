"""
Translation service interfaces for abstraction and dependency inversion
"""

from abc import ABC, abstractmethod
from typing import Any

from utils.srt_parser import SRTSegment

from .base import IAsyncService


class ITranslationService(IAsyncService):
    """Interface for translation services"""

    @abstractmethod
    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate text from source to target language

        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            Translated text
        """
        pass

    @abstractmethod
    def translate_batch(self, texts: list[str], source_lang: str, target_lang: str) -> list[dict[str, Any]]:
        """
        Translate multiple texts in batch

        Args:
            texts: List of texts to translate
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            List of translation results
        """
        pass

    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if translation service is properly initialized"""
        pass


class IChunkTranslationService(ABC):
    """Interface for chunk-specific translation operations"""

    @abstractmethod
    def get_translation_service(
        self, source_lang: str, target_lang: str, quality: str = "standard"
    ) -> ITranslationService:
        """
        Get or create translation service for language pair

        Args:
            source_lang: Source language code
            target_lang: Target language code
            quality: Translation quality level

        Returns:
            Translation service instance
        """
        pass

    @abstractmethod
    async def build_translation_segments(
        self,
        task_id: str,
        task_progress: dict[str, Any],
        srt_file_path: str,
        vocabulary: list[Any],
        language_preferences: dict[str, Any],
    ) -> list[SRTSegment]:
        """
        Build translation segments for vocabulary words

        Args:
            task_id: Processing task identifier
            task_progress: Progress tracking dictionary
            srt_file_path: Path to SRT subtitle file
            vocabulary: List of vocabulary words to translate
            language_preferences: User language preferences

        Returns:
            List of translated SRT segments
        """
        pass

    @abstractmethod
    def segments_overlap(
        self, seg1_start: float, seg1_end: float, seg2_start: float, seg2_end: float, threshold: float = 0.5
    ) -> bool:
        """
        Check if two time segments overlap significantly

        Args:
            seg1_start: Start time of first segment
            seg1_end: End time of first segment
            seg2_start: Start time of second segment
            seg2_end: End time of second segment
            threshold: Minimum overlap ratio to consider significant

        Returns:
            True if segments overlap significantly
        """
        pass


class ISelectiveTranslationService(ABC):
    """Interface for selective translation based on known words"""

    @abstractmethod
    async def apply_selective_translations(
        self,
        srt_path: str,
        known_words: list[str],
        target_language: str,
        user_level: str,
        user_id: str,
    ) -> dict[str, Any]:
        """
        Apply selective translations excluding known words

        Args:
            srt_path: Path to SRT file
            known_words: List of words user already knows
            target_language: Target language code
            user_level: User's language level
            user_id: User identifier

        Returns:
            Translation analysis results
        """
        pass

    @abstractmethod
    async def refilter_for_translations(
        self,
        srt_path: str,
        user_id: str,
        known_words: list[str],
        user_level: str,
        target_language: str,
    ) -> dict[str, Any]:
        """
        Re-filter subtitles for translation needs

        Args:
            srt_path: Path to SRT file
            user_id: User identifier
            known_words: List of known words to exclude
            user_level: User's language level
            target_language: Target language code

        Returns:
            Filtering and translation analysis results
        """
        pass
