"""
Vocabulary Filter
Filters out non-vocabulary words (interjections, proper names, etc.)
"""

import re
from .interface import FilteredWord, WordStatus
from .filter_chain import BaseSubtitleFilter


class VocabularyFilter(BaseSubtitleFilter):
    """
    Filters out words that are not proper vocabulary for learning:
    - Interjections (oh, ah, um, uh, etc.)
    - Proper names (capitalized words)
    - Non-alphabetic content (numbers, symbols)
    - Very short words (1-2 characters)
    """

    def __init__(self, language: str = "en"):
        super().__init__()
        self.language = language

        # Language-specific interjections and filler words
        self._interjections = self._get_language_interjections(language)

        # Patterns for identifying non-vocabulary content
        self._proper_name_pattern = re.compile(r"^[A-Z][a-z]+$")
        self._non_alphabetic_pattern = re.compile(r"^[^a-zA-Z]*$")
        self._contains_numbers = re.compile(r"\d")

        # Statistics
        self._interjection_count = 0
        self._proper_name_count = 0
        self._short_word_count = 0
        self._non_alphabetic_count = 0

    def _get_language_interjections(self, language: str) -> set:
        """Get language-specific interjections and filler words"""
        interjections = {
            "en": {
                "oh",
                "ah",
                "um",
                "uh",
                "er",
                "eh",
                "mm",
                "hmm",
                "hm",
                "yeah",
                "yep",
                "nah",
                "nope",
                "mhm",
                "aha",
                "ooh",
                "aah",
                "wow",
                "whoa",
                "duh",
                "huh",
                "tsk",
                "pfft",
                "shh",
                "psst",
                "like",
                "basically",
                "literally",
                "actually",
                "obviously",
            },
            "de": {
                "äh",
                "ähm",
                "hmm",
                "hm",
                "oh",
                "ah",
                "ach",
                "na",
                "naja",
                "genau",
                "eigentlich",
                "übrigens",
                "sozusagen",
                "gewissermaßen",
                "quasi",
                "irgendwie",
                "halt",
                "eben",
                "mal",
                "doch",
                "ja",
                "nee",
                "ne",
                "hä",
                "ähem",
                "tja",
                "also",
                "so",
                "nun",
                "pst",
                "sch",
                "ups",
                "oops",
                "autsch",
                "au",
                "aua",
            },
            "es": {
                "eh",
                "ehm",
                "ah",
                "oh",
                "este",
                "bueno",
                "pues",
                "vamos",
                "mira",
                "sabes",
                "claro",
                "obviamente",
                "básicamente",
                "literalmente",
                "realmente",
                "entonces",
                "así",
                "vale",
                "venga",
                "hombre",
                "tío",
                "ay",
                "uy",
                "ups",
                "auch",
                "mmm",
                "hmm",
                "shh",
                "psst",
            },
        }

        return interjections.get(language, interjections["en"])

    @property
    def filter_name(self) -> str:
        return f"VocabularyFilter({self.language})"

    def _should_filter_word(self, word: FilteredWord, subtitle) -> bool:
        """Check if word should be filtered as non-vocabulary"""
        text = word.text.lower().strip()
        original_text = word.text.strip()

        # Filter very short words (< 3 characters)
        if len(text) < 3:
            self._short_word_count += 1
            return True

        # Filter interjections
        if text in self._interjections:
            self._interjection_count += 1
            return True

        # Filter non-alphabetic content
        if self._non_alphabetic_pattern.match(text) or self._contains_numbers.search(
            text
        ):
            self._non_alphabetic_count += 1
            return True

        # Filter likely proper names
        if self._proper_name_pattern.match(
            original_text
        ) and not self._is_common_capitalized_word(original_text):
            self._proper_name_count += 1
            return True

        return False

    def _is_common_capitalized_word(self, word: str) -> bool:
        """Check if capitalized word is common rather than proper name"""
        common_capitalized = {
            "I",
            "The",
            "This",
            "That",
            "These",
            "Those",
            "What",
            "Where",
            "When",
            "Why",
            "How",
            "Who",
            "Which",
            "Can",
            "Could",
            "Would",
        }
        return word in common_capitalized

    def _get_filter_status(self):
        return WordStatus.FILTERED_INVALID

    def _get_filter_reason(self, word: FilteredWord) -> str:
        text = word.text.lower().strip()

        if len(text) < 3:
            return "Too short"
        elif text in self._interjections:
            return "Interjection/filler"
        elif self._non_alphabetic_pattern.match(text) or self._contains_numbers.search(
            text
        ):
            return "Non-alphabetic content"
        elif self._proper_name_pattern.match(word.text.strip()):
            return "Likely proper name"
        else:
            return "Non-vocabulary word"

    def get_statistics(self):
        base_stats = super().get_statistics()
        base_stats.update(
            {
                "interjections_filtered": self._interjection_count,
                "proper_names_filtered": self._proper_name_count,
                "short_words_filtered": self._short_word_count,
                "non_alphabetic_filtered": self._non_alphabetic_count,
                "language": self.language,
            }
        )
        return base_stats
