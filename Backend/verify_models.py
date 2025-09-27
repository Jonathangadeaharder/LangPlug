#!/usr/bin/env python3
"""Verify and install required models for LangPlug language support."""

import subprocess
import sys
from typing import List, Dict, Tuple

from core.language_preferences import (
    SUPPORTED_TRANSLATION_PAIRS,
    SPACY_MODEL_MAP,
    OPUS_MODEL_MAP,
    resolve_language_runtime_settings
)


def check_spacy_model(model_name: str) -> bool:
    """Check if a spaCy model is installed."""
    try:
        import spacy
        spacy.load(model_name)
        return True
    except (ImportError, OSError):
        return False


def install_spacy_model(model_name: str) -> bool:
    """Install a spaCy model."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "spacy", "download", model_name],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False


def check_transformers_model(model_name: str) -> bool:
    """Check if a Transformers model is accessible."""
    try:
        from transformers import pipeline
        # Try to create a translation pipeline with the model
        translator = pipeline("translation", model=model_name)
        return True
    except Exception:
        return False


def verify_all_models():
    """Verify all required models for supported language pairs."""
    print("Verifying Required Models for LangPlug")
    print("=" * 50)

    # Check spaCy models
    print("\nspaCy Models:")
    missing_spacy = []
    for lang_code, model_name in SPACY_MODEL_MAP.items():
        if lang_code == "default":
            continue

        if check_spacy_model(model_name):
            print(f"  [INSTALLED] {model_name} ({lang_code})")
        else:
            print(f"  [MISSING] {model_name} ({lang_code}) - NOT INSTALLED")
            missing_spacy.append(model_name)

    # Check translation models
    print("\nHelsinki-NLP Translation Models:")
    missing_helsinki = []
    for native, target in SUPPORTED_TRANSLATION_PAIRS:
        runtime = resolve_language_runtime_settings(native, target)
        model_name = runtime["translation_model"]

        print(f"  {native} -> {target}: {model_name}")
        # Note: We can't easily check if these exist without downloading them
        # They will be downloaded on first use by the translation service

    # Print installation instructions
    if missing_spacy:
        print("\nInstallation Instructions:")
        print("\nMissing spaCy models (install these):")
        for model in missing_spacy:
            print(f"  python -m spacy download {model}")

        print("\nOr install all at once:")
        print(f"  python -m spacy download {' '.join(missing_spacy)}")

    print("\nHelsinki-NLP Models:")
    print("These will be automatically downloaded on first use:")
    for native, target in sorted(SUPPORTED_TRANSLATION_PAIRS):
        runtime = resolve_language_runtime_settings(native, target)
        print(f"  {native} -> {target}: {runtime['translation_model']}")

    print("\nFallback Model:")
    print("  facebook/nllb-200-distilled-600M (auto-downloaded)")

    # Print summary
    print("\n" + "=" * 50)
    if missing_spacy:
        print(f"WARNING: {len(missing_spacy)} spaCy models need installation")
        print("Run the installation commands above before using LangPlug")
    else:
        print("SUCCESS: All spaCy models are installed!")

    print(f"Language pairs supported: {len(SUPPORTED_TRANSLATION_PAIRS)}")

    return len(missing_spacy) == 0


def install_missing_spacy_models():
    """Install all missing spaCy models."""
    print("Installing missing spaCy models...")

    missing_models = []
    for lang_code, model_name in SPACY_MODEL_MAP.items():
        if lang_code == "default":
            continue
        if not check_spacy_model(model_name):
            missing_models.append(model_name)

    if not missing_models:
        print("SUCCESS: All spaCy models already installed!")
        return True

    success_count = 0
    for model in missing_models:
        print(f"Installing {model}...")
        if install_spacy_model(model):
            print(f"  SUCCESS: {model} installed successfully")
            success_count += 1
        else:
            print(f"  ERROR: Failed to install {model}")

    print(f"\nInstalled {success_count}/{len(missing_models)} models")
    return success_count == len(missing_models)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Verify and install LangPlug models")
    parser.add_argument("--install", action="store_true", help="Install missing spaCy models")
    parser.add_argument("--check-only", action="store_true", help="Only check, don't install")

    args = parser.parse_args()

    if args.install:
        install_missing_spacy_models()
    else:
        verify_all_models()

        if not args.check_only:
            response = input("\nInstall missing spaCy models now? (y/N): ")
            if response.lower() in ["y", "yes"]:
                install_missing_spacy_models()