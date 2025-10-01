#!/usr/bin/env python3
"""
LangPlug - German Language Learning Platform
Entry point for the FastAPI server
"""

import logging
from pathlib import Path

import uvicorn

logger = logging.getLogger(__name__)

from core.app import create_app
from core.config import settings

# Create the FastAPI application
app = create_app()

if __name__ == "__main__":
    # Run the server
    # Only watch specific directories to avoid SQLite WAL file spam
    reload_dirs = (
        [
            str(Path(__file__).parent / "api"),
            str(Path(__file__).parent / "core"),
            str(Path(__file__).parent / "services"),
        ]
        if settings.reload
        else None
    )

    # Configure reload with conservative settings to minimize watchfiles spam
    reload_config = {
        "reload": settings.reload,
        "reload_delay": 2.0,  # Add delay to reduce sensitivity
        "reload_dirs": reload_dirs if settings.reload else None,
        "reload_includes": ["**/*.py"] if settings.reload else None,
        "reload_excludes": [
            "**/__pycache__/**",
            "**/*.pyc",
            "**/*.pyo",
            "**/*.db",
            "**/*.db-shm",
            "**/*.db-wal",
            "**/*.db-journal",
            "**/logs/**",
            "**/*.log",
        ]
        if settings.reload
        else None,
    }

    if reload_dirs:
        logger.info(f"Watching directories: {reload_dirs}")

    uvicorn.run(
        "core.app:create_app", host=settings.host, port=settings.port, log_level="info", factory=True, **reload_config
    )
