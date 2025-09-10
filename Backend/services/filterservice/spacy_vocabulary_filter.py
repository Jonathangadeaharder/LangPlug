"""
SpaCy-based Vocabulary Filter
Uses spaCy's POS tagging and NER to filter out proper nouns and non-vocabulary words
"""

import logging
import spacy
from .interface import FilteredWord, WordStatus
from .filter_chain import BaseSubtitleFilter

logger = logging.getLogger(__name__)


class SpacyVocabularyFilter(BaseSubtitleFilter):
    """
    Advanced vocabulary filter using spaCy for:
    - POS tagging to identify proper nouns (PROPN)
    - Named Entity Recognition for persons, organizations, locations
    - Better handling of proper vocabulary vs non-vocabulary words
    """
    
    def __init__(self, language: str = "en"):
        super().__init__()
        self.language = language
        self._nlp = None
        
        # Language model mapping (using small models for initial setup)
        self._models = {
            "en": "en_core_web_sm",
            "de": "de_core_news_sm", 
            "es": "es_core_news_sm"
        }
        
        # Initialize spaCy model
        self._load_model()
        
        # Common interjections that might not be caught by POS tagging
        self._interjections = {
            "oh", "ah", "um", "uh", "er", "eh", "mm", "hmm", "hm",
            "yeah", "yep", "nah", "nope", "mhm", "aha", "ooh", "aah",
            "wow", "whoa", "duh", "huh", "tsk", "pfft", "shh", "psst"
        }
        
        # Statistics
        self._proper_nouns_filtered = 0
        self._named_entities_filtered = 0
        self._interjections_filtered = 0
        self._short_words_filtered = 0
        self._non_alphabetic_filtered = 0
    
    def _load_model(self):
        """Load the appropriate spaCy model for the language"""
        model_name = self._models.get(self.language, "en_core_web_sm")
        
        try:
            # Try to load the model
            self._nlp = spacy.load(model_name)
            logger.info(f"Successfully loaded spaCy model: {model_name}")
        except OSError as e:
            # Model not found - provide clear installation instructions
            error_msg = (
                f"SpaCy model '{model_name}' not found. "
                f"Please install it by running: python -m spacy download {model_name}"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            # Other spaCy loading errors
            error_msg = f"Failed to load spaCy model '{model_name}': {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    @property
    def filter_name(self) -> str:
        return f"SpacyVocabularyFilter({self.language})"
    
    def _should_filter_word(self, word: FilteredWord, subtitle) -> bool:
        """Check if word should be filtered using spaCy analysis"""
        text = word.text.strip()
        
        # Filter very short words (< 3 characters)
        if len(text) < 3:
            self._short_words_filtered += 1
            return True
        
        # Filter common interjections (fallback for spaCy limitations)
        if text.lower() in self._interjections:
            self._interjections_filtered += 1
            return True
        
        # Filter non-alphabetic content
        if not text.replace("'", "").replace("-", "").isalpha():
            self._non_alphabetic_filtered += 1
            return True
        
        # Use spaCy for advanced analysis
        doc = self._nlp(text)
        if not doc:
            return True
            
        token = doc[0]
        
        # Filter proper nouns (PROPN tag)
        if token.pos_ == "PROPN":
            # Additional check: common capitalized words should not be filtered
            if not self._is_common_capitalized_word(text):
                self._proper_nouns_filtered += 1
                return True
        
        # Filter named entities
        if token.ent_type_ in ["PERSON", "ORG", "GPE", "LOC"]:
            self._named_entities_filtered += 1
            return True
        
        # Keep normal vocabulary words
        if token.pos_ in ["NOUN", "VERB", "ADJ", "ADV"]:
            return False
        
        # Filter other POS tags that are not learning vocabulary
        if token.pos_ in ["PRON", "DET", "ADP", "CONJ", "CCONJ", "SCONJ", "PART", "INTJ"]:
            return True
        
        return False
    
    def _is_common_capitalized_word(self, word: str) -> bool:
        """Check if capitalized word is common rather than proper name"""
        common_capitalized = {
            "I", "The", "This", "That", "These", "Those", "What", "Where",
            "When", "Why", "How", "Who", "Which", "Can", "Could", "Would",
            "Should", "Will", "May", "Might", "Must", "Do", "Does", "Did"
        }
        return word in common_capitalized
    
    def _get_filter_status(self):
        return WordStatus.FILTERED_INVALID
    
    def _get_filter_reason(self, word: FilteredWord) -> str:
        """Get detailed filter reason using spaCy analysis"""
        text = word.text.strip()
        
        if len(text) < 3:
            return "Too short"
        elif text.lower() in self._interjections:
            return "Interjection/filler"
        elif not text.replace("'", "").replace("-", "").isalpha():
            return "Non-alphabetic content"
        else:
            # Analyze with spaCy
            doc = self._nlp(text)
            if doc:
                token = doc[0]
                if token.pos_ == "PROPN":
                    return "Proper noun"
                elif token.ent_type_ in ["PERSON", "ORG", "GPE", "LOC"]:
                    return f"Named entity ({token.ent_type_})"
                elif token.pos_ in ["PRON", "DET", "ADP", "CONJ", "CCONJ", "SCONJ", "PART", "INTJ"]:
                    return f"Non-vocabulary POS ({token.pos_})"
        
        return "Non-vocabulary word"
    
    def get_statistics(self):
        base_stats = super().get_statistics()
        base_stats.update({
            "proper_nouns_filtered": self._proper_nouns_filtered,
            "named_entities_filtered": self._named_entities_filtered,
            "interjections_filtered": self._interjections_filtered,
            "short_words_filtered": self._short_words_filtered,
            "non_alphabetic_filtered": self._non_alphabetic_filtered,
            "language": self.language
        })
        return base_stats