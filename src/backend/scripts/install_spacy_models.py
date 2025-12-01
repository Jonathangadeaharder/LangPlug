#!/usr/bin/env python
"""
Script to download and install Spacy language models.
Run this after pip install to set up NLP models.

Usage:
    python scripts/install_spacy_models.py
    
Or via pip post-install hook in setup.py/pyproject.toml.
"""

import subprocess
import sys


# Spacy models required for LangPlug
SPACY_MODELS = [
    "de_core_news_lg",  # German - large model for better accuracy
    "en_core_web_sm",   # English - small model sufficient for basic tasks
]


def install_spacy_model(model_name: str) -> bool:
    """Install a Spacy model using spacy download command."""
    print(f"[INFO] Installing Spacy model: {model_name}")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "spacy", "download", model_name],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"[OK] Successfully installed {model_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to install {model_name}: {e.stderr}")
        return False


def main():
    """Install all required Spacy models."""
    print("=" * 60)
    print("Installing Spacy language models for LangPlug")
    print("=" * 60)
    
    success_count = 0
    for model in SPACY_MODELS:
        if install_spacy_model(model):
            success_count += 1
    
    print("=" * 60)
    print(f"Installed {success_count}/{len(SPACY_MODELS)} models")
    
    if success_count < len(SPACY_MODELS):
        print("[WARN] Some models failed to install. Check errors above.")
        sys.exit(1)
    else:
        print("[OK] All Spacy models installed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
