#!/usr/bin/env python3
"""Check latest versions of all dependencies from PyPI."""

import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

PACKAGES = [
    # Core Web Framework
    "fastapi",
    "pydantic",
    "pydantic-settings",
    "python-multipart",
    "uvicorn",
    # Authentication & Security
    "fastapi-users",
    "argon2-cffi",
    "python-jose",
    "passlib",
    # Database
    "sqlalchemy",
    "aiosqlite",
    "alembic",
    # AI/ML Core
    "openai-whisper",
    "transformers",
    "torch",
    "spacy",
    "sentencepiece",
    "protobuf",
    # Audio/Video
    "moviepy",
    "pydub",
    "opencv-python",
    "ffmpeg-python",
    # Subtitle Processing
    "pysrt",
    "webvtt-py",
    # Monitoring & Logging
    "structlog",
    "sentry-sdk",
    # Utilities
    "psutil",
    "websockets",
    "pyyaml",
    "rich",
    "tqdm",
    "pandas",
    "numpy",
    # Testing
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
    "pytest-xdist",
    "pytest-timeout",
    "hypothesis",
    "pytest-env",
    "httpx",
    "respx",
    "anyio",
    "trio",
    "freezegun",
    "responses",
    # Code Quality
    "pre-commit",
    "ruff",
    "mypy",
    "bandit",
    "detect-secrets",
    "radon",
    "wily",
    "lizard",
    # Type Stubs
    "types-requests",
    "types-PyYAML",
]


def get_latest_version(package: str) -> tuple[str, str]:
    """Get latest version from PyPI."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "index", "versions", package],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Parse output like "fastapi (0.116.1)"
        for line in result.stdout.split("\n"):
            if package in line and "Available versions:" in result.stdout:
                # Extract first version from "Available versions: 0.116.1, 0.116.0, ..."
                versions_line = [
                    version_line for version_line in result.stdout.split("\n") if "Available versions:" in version_line
                ]
                if versions_line:
                    versions = versions_line[0].split("Available versions:")[1].strip()
                    latest = versions.split(",")[0].strip()
                    return (package, latest)
        return (package, "ERROR: Could not parse version")
    except Exception as e:
        return (package, f"ERROR: {e}")


print("Checking latest versions from PyPI (this may take 1-2 minutes)...\n")  # noqa: T201

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(get_latest_version, pkg): pkg for pkg in PACKAGES}
    results = {}

    for future in as_completed(futures):
        package, version = future.result()
        results[package] = version
        print(f"[OK] {package}: {version}")  # noqa: T201

print("\n" + "=" * 80)  # noqa: T201
print("Summary:")  # noqa: T201
print("=" * 80)  # noqa: T201
for package in sorted(PACKAGES):
    version = results.get(package, "NOT CHECKED")
    print(f"{package:30} {version}")  # noqa: T201
