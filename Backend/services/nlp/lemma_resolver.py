"""Utilities for resolving word lemmas using spaCy models."""

from __future__ import annotations

import logging

try:  # pragma: no cover - spaCy may be unavailable in CI
    import spacy  # type: ignore
except Exception:  # pragma: no cover - allow runtime without spaCy
    spacy = None

from core.config import settings
from core.language_preferences import SPACY_MODEL_MAP

logger = logging.getLogger(__name__)


_LANGUAGE_MODEL_OVERRIDES: dict[str, str] = {
    "de": settings.spacy_model_de,
    "en": settings.spacy_model_en,
}

_MODEL_CACHE: dict[str, spacy.Language | None] = {}
_WARNING_EMITTED = False


def _resolve_model_name(language_code: str) -> str:
    language_code = (language_code or "").lower()
    if language_code in _LANGUAGE_MODEL_OVERRIDES:
        return _LANGUAGE_MODEL_OVERRIDES[language_code]
    return SPACY_MODEL_MAP.get(language_code, SPACY_MODEL_MAP["default"])


def _load_model(model_name: str) -> spacy.Language | None:
    global _WARNING_EMITTED

    if model_name in _MODEL_CACHE:
        return _MODEL_CACHE[model_name]

    if spacy is None:
        if not _WARNING_EMITTED:
            logger.warning("spaCy is not installed; lemma resolution is disabled")
            _WARNING_EMITTED = True
        _MODEL_CACHE[model_name] = None
        return None

    try:
        nlp = spacy.load(model_name)
    except Exception as exc:  # pragma: no cover - depends on runtime env
        logger.error("Failed to load spaCy model '%s': %s", model_name, exc)
        nlp = None
    _MODEL_CACHE[model_name] = nlp
    return nlp


def lemmatize_word(word: str, language_code: str) -> str | None:
    """Return the lemma for *word* using spaCy for the given language.

    Returns the lemma in lowercase when available; otherwise ``None``.
    """
    if not word:
        return None

    model_name = _resolve_model_name(language_code)
    nlp = _load_model(model_name)

    if not nlp:
        return None

    doc = nlp(word)
    if not doc:
        return None

    token = doc[0]
    lemma = token.lemma_.strip().lower()
    return lemma or None


__all__ = ["lemmatize_word"]
