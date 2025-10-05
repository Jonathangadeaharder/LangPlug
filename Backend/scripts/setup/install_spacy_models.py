#!/usr/bin/env python3
"""Install all required spaCy models for LangPlug."""

import subprocess
import sys

from core.language_preferences import SPACY_MODEL_MAP


def install_spacy_model(model_name: str) -> bool:
    """Install a spaCy model."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "spacy", "download", model_name],
            check=False,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout per model
        )

        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False


def check_spacy_model(model_name: str) -> bool:
    """Check if a spaCy model is installed."""
    try:
        import spacy

        spacy.load(model_name)
        return True
    except (ImportError, OSError):
        return False


def main():
    """Install all required spaCy models."""

    models_to_install = []
    already_installed = []

    # Check which models need installation
    for lang_code, model_name in SPACY_MODEL_MAP.items():
        if lang_code == "default":
            continue

        if check_spacy_model(model_name):
            already_installed.append(model_name)
        else:
            models_to_install.append(model_name)

    if not models_to_install:
        return True

    # Install missing models
    success_count = 0
    failed_models = []

    for model_name in models_to_install:
        if install_spacy_model(model_name):
            success_count += 1
        else:
            failed_models.append(model_name)

    # Print summary

    if failed_models:
        for _model in failed_models:
            pass
        return False
    else:
        return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception:
        sys.exit(1)
