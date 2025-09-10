import logging

logger = logging.getLogger(__name__)

Lemmatization Filter
Converts words to their lemmatized forms using spaCy
This filter should run before the user knowledge filter since the database contains lemmas
"""

import spacy
from typing import List
from .interface import FilteredSubtitle, FilteredWord
from .filter_chain import BaseSubtitleFilter


class LemmatizationFilter(BaseSubtitleFilter):
    """
    Lemmatization filter that converts words to their base forms using spaCy.
    This filter should be applied before the user knowledge filter since
    the vocabulary database stores lemmatized forms.
    
    Examples:
    - "running" -> "run"
    - "better" -> "good"
    - "mice" -> "mouse"
    - "children" -> "child"
    """
    
    def __init__(self, language: str = "en"):
        super().__init__()
        self.language = language
        self._nlp = None
        
        # Language model mapping
        self._models = {
            "en": "en_core_web_lg",
            "de": "de_core_news_lg", 
            "es": "es_core_news_lg"
        }
        
        # Initialize spaCy model
        self._load_model()
        
        # Statistics
        self._words_lemmatized = 0
        self._unchanged_words = 0
    
    def _load_model(self):
        """Load the appropriate spaCy model for the language"""
        model_name = self._models.get(self.language, "en_core_web_lg")
        try:
            self._nlp = spacy.load(model_name)
        except OSError:
            # Fallback to English if model not available
            logger.warning(f"{model_name} not found, falling back to en_core_web_lg")
            self._nlp = spacy.load("en_core_web_lg")
    
    @property
    def filter_name(self) -> str:
        return f"LemmatizationFilter({self.language})"
    
    def filter(self, subtitles: List[FilteredSubtitle]) -> List[FilteredSubtitle]:
        """Apply lemmatization to all words in subtitles"""
        self._processed_words = 0
        self._filtered_words = 0  # This filter doesn't filter, just transforms
        self._words_lemmatized = 0
        self._unchanged_words = 0
        
        for subtitle in subtitles:
            for word in subtitle.words:
                self._processed_words += 1
                
                # Only lemmatize active words
                if word.status.value == "active":
                    original_text = word.text
                    lemmatized_text = self._lemmatize_word(original_text)
                    
                    # Update word text to lemmatized form
                    word.text = lemmatized_text
                    
                    # Track statistics
                    if original_text != lemmatized_text:
                        self._words_lemmatized += 1
                        # Store original form for reference if needed
                        word.original_form = original_text
                    else:
                        self._unchanged_words += 1
        
        return subtitles
    
    def _lemmatize_word(self, word_text: str) -> str:
        """Lemmatize a single word using spaCy"""
        # Handle empty or very short text
        if not word_text or len(word_text.strip()) == 0:
            return word_text
        
        try:
            # Process the word with spaCy
            doc = self._nlp(word_text.strip())
            if doc and len(doc) > 0:
                # Return the lemma of the first token
                lemma = doc[0].lemma_
                
                # Handle spaCy's tendency to return "-PRON-" for pronouns
                if lemma == "-PRON-":
                    return word_text.lower()
                
                # Return lemmatized form in lowercase for consistency
                return lemma.lower()
            else:
                return word_text.lower()
        except Exception:
            # Fallback to original word if lemmatization fails
            return word_text.lower()
    
    def get_statistics(self):
        """Get lemmatization statistics"""
        base_stats = super().get_statistics()
        base_stats.update({
            "words_lemmatized": self._words_lemmatized,
            "unchanged_words": self._unchanged_words,
            "lemmatization_rate": self._words_lemmatized / max(self._processed_words, 1),
            "language": self.language
        })
        return base_stats