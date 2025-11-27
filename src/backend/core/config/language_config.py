"""
Centralized language configuration for vocabulary processing.

Provides single source of truth for:
- Language-specific stopwords
- Common words to filter
- Language detection patterns
"""

from typing import Final

# German stopwords - common words to exclude from vocabulary learning
GERMAN_STOPWORDS: Final[frozenset[str]] = frozenset({
    # Articles
    "der", "die", "das", "ein", "eine", "einer", "eines", "einem", "einen",
    # Pronouns
    "ich", "du", "er", "sie", "es", "wir", "ihr", "sie", "Sie",
    "mich", "dich", "sich", "uns", "euch",
    "mir", "dir", "ihm", "ihr", "uns", "euch", "ihnen", "Ihnen",
    "mein", "dein", "sein", "unser", "euer",
    # Demonstratives
    "dieser", "diese", "dieses", "jener", "jene", "jenes",
    # Relative pronouns
    "welcher", "welche", "welches",
    # Conjunctions
    "und", "oder", "aber", "sondern", "denn", "doch", "jedoch",
    "weil", "dass", "ob", "wenn", "als", "obwohl", "damit",
    # Prepositions
    "in", "im", "an", "am", "auf", "aus", "bei", "mit", "nach",
    "von", "zu", "zum", "zur", "um", "durch", "für", "gegen",
    "ohne", "bis", "unter", "über", "vor", "hinter", "neben", "zwischen",
    # Common verbs (conjugated forms)
    "ist", "sind", "war", "waren", "bin", "bist", "sein", "gewesen",
    "hat", "haben", "habe", "hatte", "hatten", "gehabt",
    "wird", "werden", "wurde", "wurden", "geworden",
    "kann", "können", "konnte", "konnten", "gekonnt",
    "muss", "müssen", "musste", "mussten", "gemusst",
    "soll", "sollen", "sollte", "sollten", "gesollt",
    "will", "wollen", "wollte", "wollten", "gewollt",
    "darf", "dürfen", "durfte", "durften", "gedurft",
    "mag", "mögen", "mochte", "mochten", "gemocht",
    # Adverbs
    "dann", "also", "nur", "auch", "noch", "schon", "bereits",
    "immer", "nie", "oft", "selten", "manchmal", "vielleicht",
    "wahrscheinlich", "sicher", "bestimmt", "wirklich", "eigentlich",
    "ganz", "sehr", "ziemlich", "etwas", "nichts",
    # Question words
    "was", "wer", "wo", "wann", "warum", "wie", "woher", "wohin",
    # Numbers as words
    "eins", "zwei", "drei", "vier", "fünf", "sechs", "sieben", "acht", "neun", "zehn",
    # Quantifiers
    "viel", "viele", "wenig", "wenige", "mehr", "weniger", "alle", "alles",
    "einige", "manche", "jeder", "jede", "jedes", "kein", "keine",
    # Other common words
    "ja", "nein", "nicht", "kein", "keine", "keinen", "keinem", "keiner",
    "hier", "dort", "da", "hin", "her", "so", "gerade", "jetzt", "heute",
    "gestern", "morgen", "bald", "gleich", "mal", "eben",
})

# English stopwords
ENGLISH_STOPWORDS: Final[frozenset[str]] = frozenset({
    # Articles
    "a", "an", "the",
    # Pronouns
    "i", "me", "my", "mine", "myself",
    "you", "your", "yours", "yourself", "yourselves",
    "he", "him", "his", "himself",
    "she", "her", "hers", "herself",
    "it", "its", "itself",
    "we", "us", "our", "ours", "ourselves",
    "they", "them", "their", "theirs", "themselves",
    "who", "whom", "whose", "which", "what", "that", "this", "these", "those",
    # Common verbs
    "is", "am", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having",
    "do", "does", "did", "doing", "done",
    "will", "would", "shall", "should", "can", "could", "may", "might", "must",
    # Prepositions
    "in", "on", "at", "to", "for", "of", "with", "by", "from", "up", "about",
    "into", "over", "after", "beneath", "under", "above",
    # Conjunctions
    "and", "but", "or", "nor", "so", "yet", "both", "either", "neither",
    "because", "although", "while", "if", "unless", "until", "when", "where",
    # Adverbs
    "not", "only", "just", "also", "very", "too", "quite", "rather",
    "always", "never", "often", "sometimes", "usually", "now", "then",
    "here", "there", "where", "when", "why", "how",
    # Other
    "all", "each", "every", "some", "any", "no", "none", "more", "most", "other",
    "such", "own", "same", "than", "as",
})

# Spanish stopwords
SPANISH_STOPWORDS: Final[frozenset[str]] = frozenset({
    # Articles
    "el", "la", "los", "las", "un", "una", "unos", "unas",
    # Pronouns
    "yo", "tu", "el", "ella", "nosotros", "vosotros", "ellos", "ellas",
    "me", "te", "se", "nos", "os", "le", "les", "lo", "la",
    "mi", "tu", "su", "nuestro", "vuestro",
    # Common verbs
    "es", "son", "era", "fueron", "ser", "sido",
    "ha", "han", "haber", "habido", "tiene", "tienen", "tener",
    "esta", "estan", "estar", "estado",
    # Prepositions
    "a", "de", "en", "con", "por", "para", "sin", "sobre", "entre",
    # Conjunctions
    "y", "e", "o", "u", "pero", "sino", "aunque", "porque", "que", "si",
    # Adverbs
    "no", "si", "muy", "mas", "menos", "ya", "aun", "tambien", "solo",
    # Other
    "como", "cuando", "donde", "quien", "cual", "este", "ese", "aquel",
})

# Mapping of language codes to their stopwords
STOPWORDS_BY_LANGUAGE: Final[dict[str, frozenset[str]]] = {
    "de": GERMAN_STOPWORDS,
    "en": ENGLISH_STOPWORDS,
    "es": SPANISH_STOPWORDS,
}

# Minimum word length for vocabulary consideration
MIN_WORD_LENGTH: Final[int] = 3

# Maximum word length (likely not a real word if longer)
MAX_WORD_LENGTH: Final[int] = 50


def get_stopwords(language: str) -> frozenset[str]:
    """
    Get stopwords for a specific language.
    
    Args:
        language: ISO 639-1 language code (e.g., 'de', 'en', 'es')
        
    Returns:
        Frozenset of stopwords for the language, empty set if not supported
    """
    return STOPWORDS_BY_LANGUAGE.get(language.lower(), frozenset())


def is_stopword(word: str, language: str) -> bool:
    """
    Check if a word is a stopword in the given language.
    
    Args:
        word: Word to check (case-insensitive)
        language: ISO 639-1 language code
        
    Returns:
        True if word is a stopword
    """
    return word.lower() in get_stopwords(language)


def filter_stopwords(words: list[str], language: str) -> list[str]:
    """
    Filter out stopwords from a list of words.
    
    Args:
        words: List of words to filter
        language: ISO 639-1 language code
        
    Returns:
        List with stopwords removed
    """
    stopwords = get_stopwords(language)
    return [w for w in words if w.lower() not in stopwords]


def is_valid_vocabulary_word(word: str, language: str) -> bool:
    """
    Check if a word is valid for vocabulary learning.
    
    Criteria:
    - Length between MIN_WORD_LENGTH and MAX_WORD_LENGTH
    - Not a stopword
    - Contains only valid characters for the language
    
    Args:
        word: Word to validate
        language: ISO 639-1 language code
        
    Returns:
        True if word is valid for vocabulary
    """
    if len(word) < MIN_WORD_LENGTH or len(word) > MAX_WORD_LENGTH:
        return False
    
    if is_stopword(word, language):
        return False
    
    return True


__all__ = [
    "ENGLISH_STOPWORDS",
    "GERMAN_STOPWORDS",
    "MAX_WORD_LENGTH",
    "MIN_WORD_LENGTH",
    "SPANISH_STOPWORDS",
    "STOPWORDS_BY_LANGUAGE",
    "filter_stopwords",
    "get_stopwords",
    "is_stopword",
    "is_valid_vocabulary_word",
]
