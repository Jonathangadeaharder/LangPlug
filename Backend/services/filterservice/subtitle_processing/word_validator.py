"""
Word Validator Service
Handles validation of words for vocabulary learning
"""

import logging
import re

logger = logging.getLogger(__name__)


class WordValidator:
    """Service for validating words for vocabulary learning"""

    def __init__(self):
        # Pre-compiled patterns for efficiency
        self._proper_name_pattern = re.compile(r"^[A-Z][a-z]+$")
        self._non_alphabetic_pattern = re.compile(r"^[^a-zA-Z]*$")
        self._contains_numbers = re.compile(r"\d")

        # Language-specific interjections (German)
        self._german_interjections = {
            "ach",
            "ah",
            "äh",
            "ähm",
            "also",
            "eh",
            "hm",
            "hmm",
            "na",
            "oh",
            "oje",
            "ok",
            "okay",
            "so",
            "tja",
            "uh",
            "uhm",
            "um",
            "ups",
            "wow",
            "ja",
            "nein",
            "doch",
            "hallo",
            "hey",
            "hi",
            "tschüss",
            "bye",
        }

        # Language-specific interjections mapping
        self._interjections_by_language = {
            "de": self._german_interjections,
            "en": {"ah", "oh", "um", "uh", "hmm", "hm", "okay", "ok", "hey", "hi", "bye", "wow"},
            "es": {"ah", "oh", "eh", "hola", "adiós", "ok", "bueno", "pues"},
        }

    def is_valid_vocabulary_word(self, word_text: str, language: str = "de") -> bool:
        """
        Check if word is valid for vocabulary learning

        Args:
            word_text: Word text to validate
            language: Language code

        Returns:
            True if word is valid vocabulary, False otherwise
        """
        return not self.is_non_vocabulary_word(word_text, language)

    def is_non_vocabulary_word(self, word_text: str, language: str = "de") -> bool:
        """
        Check if word should be filtered as non-vocabulary

        Args:
            word_text: Word text to check
            language: Language code

        Returns:
            True if word should be filtered out
        """
        # Very short words
        if len(word_text) <= 2:
            return True

        # Contains numbers
        if self._contains_numbers.search(word_text):
            return True

        # Non-alphabetic content
        if self._non_alphabetic_pattern.match(word_text):
            return True

        # Language-specific interjections
        if self.is_interjection(word_text, language):
            return True

        # Proper names (basic check)
        return bool(self.is_proper_name(word_text))

    def is_interjection(self, word_text: str, language: str = "de") -> bool:
        """
        Check if word is an interjection

        Args:
            word_text: Word text to check
            language: Language code

        Returns:
            True if word is an interjection
        """
        interjections = self._interjections_by_language.get(language, set())
        return word_text.lower() in interjections

    def is_proper_name(self, word_text: str) -> bool:
        """
        Check if word appears to be a proper name (basic heuristic)

        Args:
            word_text: Word text to check

        Returns:
            True if word appears to be a proper name
        """
        return bool(self._proper_name_pattern.match(word_text))

    def is_valid_length(self, word_text: str, min_length: int = 3) -> bool:
        """
        Check if word meets minimum length requirement

        Args:
            word_text: Word text to check
            min_length: Minimum word length (default 3)

        Returns:
            True if word meets length requirement
        """
        return len(word_text) >= min_length

    def get_validation_reason(self, word_text: str, language: str = "de") -> str | None:
        """
        Get the reason why a word is invalid (if it is)

        Args:
            word_text: Word text to check
            language: Language code

        Returns:
            Reason string if invalid, None if valid
        """
        if len(word_text) <= 2:
            return "Too short (≤ 2 characters)"

        if self._contains_numbers.search(word_text):
            return "Contains numbers"

        if self._non_alphabetic_pattern.match(word_text):
            return "Non-alphabetic"

        if self.is_interjection(word_text, language):
            return f"Interjection ({language})"

        if self.is_proper_name(word_text):
            return "Proper name"

        return None


# Singleton instance
word_validator = WordValidator()
