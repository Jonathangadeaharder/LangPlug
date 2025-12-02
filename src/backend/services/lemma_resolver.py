"""Utilities for resolving word lemmas using spaCy models."""

from __future__ import annotations

try:
    import spacy  # type: ignore
except ImportError as exc:
    raise RuntimeError("spaCy is required for lemmatization. Install it with: pip install spacy") from exc

from core.config import settings
from core.config.logging_config import get_logger
from core.language_preferences import SPACY_MODEL_MAP

logger = get_logger(__name__)


_MODEL_CACHE: dict[str, spacy.Language] = {}


def _resolve_model_name(language_code: str) -> str:
    """Resolve spaCy model name for a given language code.

    Uses dynamic settings for configured languages so that debug-time
    overrides (e.g. switching to de_core_news_sm) are honored.
    """
    language_code = (language_code or "").lower()

    # Build a mapping that incorporates settings overrides
    language_to_model = {
        "de": settings.spacy_model_de or SPACY_MODEL_MAP.get("de", SPACY_MODEL_MAP["default"]),
        "en": settings.spacy_model_en or SPACY_MODEL_MAP.get("en", SPACY_MODEL_MAP["default"]),
        # Add more overrides here if needed
    }
    # Use the override mapping first, then fall back to SPACY_MODEL_MAP
    return language_to_model.get(language_code, SPACY_MODEL_MAP.get(language_code, SPACY_MODEL_MAP["default"]))


def _load_model(model_name: str) -> spacy.Language:
    """Load spaCy model, fail early if unavailable"""
    if model_name in _MODEL_CACHE:
        return _MODEL_CACHE[model_name]

    try:
        nlp = spacy.load(model_name)
        logger.info("Loaded spaCy model successfully", model=model_name)
    except OSError as exc:
        logger.error(
            "[SPACY MODEL ERROR] Cannot load model - vocabulary filtering disabled",
            model=model_name,
            fix=f"python -m spacy download {model_name}",
            error=str(exc),
        )
        raise RuntimeError(
            f"Failed to load spaCy model '{model_name}'. Install it with: python -m spacy download {model_name}"
        ) from exc
    except Exception as exc:
        logger.error(
            "[SPACY ERROR] Unexpected error loading model",
            model=model_name,
            error=str(exc),
        )
        raise RuntimeError(
            f"Failed to load spaCy model '{model_name}'. Install it with: python -m spacy download {model_name}"
        ) from exc

    _MODEL_CACHE[model_name] = nlp
    return nlp


def lemmatize_word(word: str, language_code: str) -> str:
    """Return the lemma for *word* using spaCy for the given language.

    Returns the lemma in lowercase.
    Raises RuntimeError if spaCy model is unavailable or lemmatization fails.
    """
    if not word:
        raise ValueError("Cannot lemmatize empty word")

    model_name = _resolve_model_name(language_code)
    nlp = _load_model(model_name)

    doc = nlp(word)
    if not doc or len(doc) == 0:
        raise RuntimeError(f"spaCy failed to tokenize word '{word}'")

    token = doc[0]
    lemma = token.lemma_.strip().lower()

    if not lemma:
        raise RuntimeError(f"spaCy returned empty lemma for word '{word}'")

    return lemma


def is_proper_name(word: str, language_code: str) -> bool:
    """Check if a word is a proper name using spaCy NER and POS tagging.

    Returns True if the word is:
    - Tagged as PROPN (proper noun)
    - Recognized as a named entity (PER, ORG, LOC, GPE, etc.)

    Proper names should not be included in vocabulary learning.
    """
    if not word:
        return False

    model_name = _resolve_model_name(language_code)
    nlp = _load_model(model_name)

    doc = nlp(word)
    if not doc or len(doc) == 0:
        return False

    token = doc[0]

    # Check if POS tag is proper noun
    if token.pos_ == "PROPN":
        logger.debug("Word '%s' detected as proper noun (POS=PROPN)", word)
        return True

    # Check if recognized as named entity
    # Common NER labels: PER (person), ORG (organization), LOC (location), GPE (geopolitical entity)
    if doc.ents:
        for ent in doc.ents:
            if token.i >= ent.start and token.i < ent.end:
                logger.debug("Word '%s' detected as named entity (label=%s)", word, ent.label_)
                return True

    return False


__all__ = ["is_proper_name", "lemmatize_word"]
