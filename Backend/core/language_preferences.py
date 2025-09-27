"""User language preferences helpers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

from .config import settings

SUPPORTED_LANGUAGES: dict[str, dict[str, str]] = {
    "en": {"name": "English", "flag": "us"},
    "de": {"name": "German", "flag": "de"},
    "es": {"name": "Spanish", "flag": "es"},
    "fr": {"name": "French", "flag": "fr"},
    "zh": {"name": "Chinese", "flag": "cn"},
}

# Supported translation pairs (native -> target)
# Only these combinations have working translation models
SUPPORTED_TRANSLATION_PAIRS: set[tuple[str, str]] = {
    ("es", "de"),  # Spanish native learning German
    ("es", "en"),  # Spanish native learning English
    ("en", "zh"),  # English native learning Chinese
    ("de", "es"),  # German native learning Spanish
    ("de", "fr"),  # German native learning French
}

TRANSCRIPTION_MODEL_MAP: dict[str, str] = {
    "default": "whisper-small",
}

SPACY_MODEL_MAP: dict[str, str] = {
    "de": "de_core_news_sm",
    "en": "en_core_web_sm",
    "es": "es_core_news_sm",
    "fr": "fr_core_news_sm",
    "zh": "zh_core_web_sm",
    "default": "xx_sent_ud_sm",
}


def _default_transcription_model(language_code: str) -> str:
    return TRANSCRIPTION_MODEL_MAP.get(language_code, TRANSCRIPTION_MODEL_MAP["default"])


def _default_spacy_model(language_code: str) -> str:
    return SPACY_MODEL_MAP.get(language_code, SPACY_MODEL_MAP["default"])


# Verified Helsinki-NLP OPUS model mappings for supported pairs
OPUS_MODEL_MAP: dict[tuple[str, str], str] = {
    # Format: (source_language, target_language) -> model_name
    ("de", "es"): "Helsinki-NLP/opus-mt-de-es",      # German -> Spanish
    ("es", "de"): "Helsinki-NLP/opus-mt-es-de",      # Spanish -> German
    ("en", "es"): "Helsinki-NLP/opus-mt-en-es",      # English -> Spanish
    ("es", "en"): "Helsinki-NLP/opus-mt-es-en",      # Spanish -> English
    ("zh", "en"): "Helsinki-NLP/opus-mt-zh-en",      # Chinese -> English
    ("en", "zh"): "Helsinki-NLP/opus-mt-en-zh",      # English -> Chinese
    ("fr", "de"): "Helsinki-NLP/opus-mt-fr-de",      # French -> German
    ("de", "fr"): "Helsinki-NLP/opus-mt-de-fr",      # German -> French
}


def _preferred_opus_model(source_lang: str, target_lang: str) -> str:
    """Return the verified Helsinki-NLP model name for the given language pair."""
    model_key = (source_lang, target_lang)
    if model_key in OPUS_MODEL_MAP:
        return OPUS_MODEL_MAP[model_key]

    # Fallback to the general pattern (may not exist)
    return f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}"

LANGUAGE_PREFERENCES_FILE = "language_preferences.json"
DEFAULT_NATIVE_LANGUAGE = "en"
DEFAULT_TARGET_LANGUAGE = "de"


def _preferences_path(user_id: str) -> Path:
    """Return the path that stores language preferences for a user."""
    user_dir = settings.get_data_path() / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir / LANGUAGE_PREFERENCES_FILE


def load_language_preferences(user_id: str) -> Tuple[str, str]:
    """Load persisted language preferences for a user."""
    path = _preferences_path(user_id)

    if path.exists():
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
            native = data.get("native_language", DEFAULT_NATIVE_LANGUAGE)
            target = data.get("target_language", DEFAULT_TARGET_LANGUAGE)
            native = native if native in SUPPORTED_LANGUAGES else DEFAULT_NATIVE_LANGUAGE
            if target not in SUPPORTED_LANGUAGES or target == native:
                target = DEFAULT_TARGET_LANGUAGE if DEFAULT_TARGET_LANGUAGE != native else DEFAULT_NATIVE_LANGUAGE
            return native, target
        except Exception:  # pragma: no cover - fallback to defaults on failure
            return DEFAULT_NATIVE_LANGUAGE, DEFAULT_TARGET_LANGUAGE

    return DEFAULT_NATIVE_LANGUAGE, DEFAULT_TARGET_LANGUAGE


def save_language_preferences(user_id: str, native: str, target: str) -> None:
    """Persist language preferences for a user."""
    # Validate that this is a supported translation pair
    if not is_translation_pair_supported(native, target):
        raise ValueError(
            f"Translation pair ({native} -> {target}) is not supported. "
            f"Supported pairs: {', '.join(f'{n}->{t}' for n, t in SUPPORTED_TRANSLATION_PAIRS)}"
        )

    payload = {
        "native_language": native,
        "target_language": target,
    }

    path = _preferences_path(user_id)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def is_translation_pair_supported(native: str, target: str) -> bool:
    """Check if a native-target language pair is supported for translation."""
    return (native, target) in SUPPORTED_TRANSLATION_PAIRS


def normalize_language_pair(native: str, target: str) -> Tuple[str, str]:
    """Normalize language codes to supported ones with fallbacks."""
    native_code = native if native in SUPPORTED_LANGUAGES else DEFAULT_NATIVE_LANGUAGE
    target_code = target if target in SUPPORTED_LANGUAGES else DEFAULT_TARGET_LANGUAGE

    # Ensure the pair is supported for translation
    if not is_translation_pair_supported(native_code, target_code):
        # Fallback to default supported pair
        native_code, target_code = DEFAULT_NATIVE_LANGUAGE, DEFAULT_TARGET_LANGUAGE
        if not is_translation_pair_supported(native_code, target_code):
            # If even default isn't supported, use Spanish->German as primary fallback
            native_code, target_code = "es", "de"

    return native_code, target_code


def resolve_language_runtime_settings(native: str, target: str) -> Dict[str, Any]:
    """Derive runtime configuration (models, language metadata) for a language pair."""
    native_code, target_code = normalize_language_pair(native, target)
    source_language = target_code
    target_language = native_code

    runtime: Dict[str, Any] = {
        "native": native_code,
        "target": target_code,
        "translation_service": "opus",
        "translation_model": _preferred_opus_model(source_language, target_language),
        "translation_fallback_service": "nllb",
        "translation_fallback_model": "facebook/nllb-200-distilled-600M",
        "transcription_service": _default_transcription_model(target_code),
        "spacy_models": {
            "target": _default_spacy_model(target_code),
            "native": _default_spacy_model(native_code),
        },
    }

    return runtime
