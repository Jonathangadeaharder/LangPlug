#!/usr/bin/env python3
"""Check latest versions using PyPI JSON API (faster)."""

import json
import urllib.request

PACKAGES = [
    "pydantic",
    "sqlalchemy",
    "transformers",
    "torch",
    "spacy",
    "protobuf",
    "sentencepiece",
    "opencv-python",
    "sentry-sdk",
    "psutil",
    "pyyaml",
    "websockets",
    "rich",
    "pandas",
    "numpy",
    "hypothesis",
    "mypy",
    "ruff",
]

print("Checking versions via PyPI JSON API:\n")  # noqa: T201
for package in PACKAGES:
    try:
        url = f"https://pypi.org/pypi/{package}/json"
        with urllib.request.urlopen(url, timeout=5) as response:  # noqa: S310
            data = json.loads(response.read())
            version = data["info"]["version"]
            print(f"{package:20} {version}")  # noqa: T201
    except Exception as e:
        print(f"{package:20} ERROR: {e}")  # noqa: T201
