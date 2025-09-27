#!/usr/bin/env python3
"""Install all required spaCy models for LangPlug."""

import subprocess
import sys
from core.language_preferences import SPACY_MODEL_MAP


def install_spacy_model(model_name: str) -> bool:
    """Install a spaCy model."""
    try:
        print(f"Installing {model_name}...")
        result = subprocess.run(
            [sys.executable, "-m", "spacy", "download", model_name],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per model
        )

        if result.returncode == 0:
            print(f"  SUCCESS: {model_name} installed")
            return True
        else:
            print(f"  ERROR: {model_name} failed - {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ERROR: {model_name} timed out")
        return False
    except Exception as e:
        print(f"  ERROR: {model_name} failed - {e}")
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
    print("Installing required spaCy models for LangPlug")
    print("=" * 50)

    models_to_install = []
    already_installed = []

    # Check which models need installation
    for lang_code, model_name in SPACY_MODEL_MAP.items():
        if lang_code == "default":
            continue

        if check_spacy_model(model_name):
            print(f"  [SKIP] {model_name} already installed")
            already_installed.append(model_name)
        else:
            models_to_install.append(model_name)

    if not models_to_install:
        print(f"\nSUCCESS: All {len(already_installed)} spaCy models already installed!")
        return True

    print(f"\nInstalling {len(models_to_install)} missing models...")

    # Install missing models
    success_count = 0
    failed_models = []

    for model_name in models_to_install:
        if install_spacy_model(model_name):
            success_count += 1
        else:
            failed_models.append(model_name)

    # Print summary
    print("\n" + "=" * 50)
    print(f"Installation Summary:")
    print(f"  Already installed: {len(already_installed)}")
    print(f"  Successfully installed: {success_count}")
    print(f"  Failed: {len(failed_models)}")

    if failed_models:
        print(f"\nFailed models (install manually):")
        for model in failed_models:
            print(f"  python -m spacy download {model}")
        return False
    else:
        print(f"\nSUCCESS: All required spaCy models are now installed!")
        return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nInstallation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)