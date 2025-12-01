"""
German Lemmatization Service using spaCy
"""

from core.config.logging_config import get_logger

try:
    import spacy

    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

logger = get_logger(__name__)


class LemmatizationService:
    """Service for German word lemmatization"""

    def __init__(self):
        self._nlp: spacy.Language | None = None
        self._cache: dict[str, str] = {}
        self._model_loaded = False

    def _load_model(self) -> bool:
        """Load spaCy German model"""
        if self._model_loaded:
            return True

        if not SPACY_AVAILABLE:
            logger.info("spaCy not available, using simple rules")
            return False

        try:
            # Try to load the German model
            self._nlp = spacy.load("de_core_news_sm")
            self._model_loaded = True
            logger.info("German spaCy model loaded")
            return True
        except Exception as e:
            logger.warning("Could not load spaCy German model", error=str(e))
            return False

    def lemmatize(self, word: str, pos: str | None = None) -> str:
        """
        Lemmatize a German word

        Args:
            word: The word to lemmatize
            pos: Optional part of speech hint (NOUN, VERB, ADJ, etc.)

        Returns:
            The lemma form of the word
        """
        # Check cache first
        cache_key = f"{word}:{pos}" if pos else word
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Load model if needed
        if not self._load_model():
            # If model can't be loaded, use simple rules
            lemma = self._simple_lemmatize(word)
            self._cache[cache_key] = lemma
            return lemma

        try:
            # Process with spaCy
            doc = self._nlp(word)
            if doc and len(doc) > 0:
                token = doc[0]
                lemma = token.lemma_

                # German nouns should keep capitalization
                if token.pos_ == "NOUN" and word[0].isupper():
                    lemma = lemma.capitalize()

                self._cache[cache_key] = lemma
                return lemma
        except Exception as e:
            logger.error("Error lemmatizing word", word=word, error=str(e))

        # Fallback to simple rules
        lemma = self._simple_lemmatize(word)
        self._cache[cache_key] = lemma
        return lemma

    def _handle_special_cases(self, word_lower: str) -> str | None:
        """Handle special case words"""
        if word_lower == "fetter":
            return "fett"
        return None

    def _try_remove_adjective_endings(self, word_lower: str) -> str | None:
        """Try to remove adjective endings and return stem if recognized"""
        adjective_endings = ["er", "e", "es", "en", "em", "sten", "ste", "stes", "stem"]

        for ending in adjective_endings:
            if word_lower.endswith(ending) and len(word_lower) > len(ending) + 2:
                stem = word_lower[: -len(ending)]

                if stem == "fett":
                    return "fett"
                if stem == "gut":
                    return "gut"
                if stem in {"gross", "groß"}:
                    return "groß"

        return None

    def _try_remove_verb_endings(self, word_lower: str) -> str | None:
        """Try to remove verb endings (past participle)"""
        if not (word_lower.startswith("ge") and len(word_lower) > 5):
            return None

        stem = word_lower[2:]
        for ending in ["t", "en"]:
            if stem.endswith(ending):
                base = stem[: -len(ending)]
                if base in ["mach", "sag", "hör", "spiel"]:
                    return base + "en"

        return None

    def _preserve_capitalization(self, word: str, lemma: str) -> str:
        """Preserve capitalization for German nouns"""
        if word[0].isupper():
            return word
        return lemma

    def _simple_lemmatize(self, word: str) -> str:
        """
        Simple rule-based lemmatization for German (Refactored for lower complexity)
        Handles common inflections
        """
        word_lower = word.lower()

        # Try special cases
        special = self._handle_special_cases(word_lower)
        if special:
            return special

        # Try adjective endings
        adjective_lemma = self._try_remove_adjective_endings(word_lower)
        if adjective_lemma:
            return adjective_lemma

        # Try verb endings
        verb_lemma = self._try_remove_verb_endings(word_lower)
        if verb_lemma:
            return verb_lemma

        # Default: preserve capitalization or return lowercase
        return self._preserve_capitalization(word, word_lower)

    def clear_cache(self):
        """Clear the lemmatization cache"""
        self._cache.clear()


def get_lemmatization_service() -> LemmatizationService:
    """Returns fresh instance to avoid global state"""
    return LemmatizationService()
