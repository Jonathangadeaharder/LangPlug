#!/usr/bin/env python3
"""
LangPlug Backend Startup Script with Error Handling
"""

import os
import sys
import traceback
import warnings
from pathlib import Path

# Configure console encoding for Windows compatibility
if sys.platform.startswith("win"):
    import codecs

    # Set stdout and stderr to use UTF-8 encoding
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())
    # Set environment variable for Python to use UTF-8
    os.environ["PYTHONIOENCODING"] = "utf-8"

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    """Main startup function with comprehensive error handling"""

    try:
        # Silence known third-party deprecation warnings until dependencies update
        warnings.filterwarnings(
            "ignore",
            message="pkg_resources is deprecated as an API",
            category=UserWarning,
            module="passlib.pwd",
        )
        warnings.filterwarnings(
            "ignore",
            message="Valid config keys have changed in V2",
            category=UserWarning,
            module="pydantic._internal._config",
        )

        # Step 1: Test imports
        import fastapi
        import uvicorn

        from core.config import settings
        from core.logging_config import setup_logging

        # Step 2: Initialize logging
        setup_logging()

        # Enable debug logging for watchfiles to see which files are changing
        if settings.reload:
            import logging
            from collections.abc import Iterable

            class _WatchfilesSelectiveFilter(logging.Filter):
                """Only surface reload notifications for relevant source changes."""

                def __init__(self, ignored_tokens: Iterable[str], allowed_suffixes: Iterable[str]):
                    super().__init__()
                    self.ignored_tokens = tuple(ignored_tokens)
                    self.allowed_suffixes = tuple(allowed_suffixes)

                def _should_keep_change(self, change: object) -> bool:
                    if not isinstance(change, tuple) or len(change) < 2:
                        return False
                    path = str(change[1]).lower()
                    if any(token in path for token in self.ignored_tokens):
                        return False
                    return path.endswith(self.allowed_suffixes)

                def filter(self, record: logging.LogRecord) -> bool:
                    # Drop generic watchfiles info messages ('4 changes detected')
                    if record.levelno >= logging.INFO and "changes detected" in record.getMessage().lower():
                        return False

                    arg_tail = None
                    if isinstance(record.args, tuple) and record.args:
                        arg_tail = record.args[-1]

                    if isinstance(arg_tail, set):
                        keep = any(self._should_keep_change(change) for change in arg_tail)
                        return keep

                    message = record.getMessage().lower()
                    return not any(token in message for token in self.ignored_tokens)

            log_level_name = os.getenv("WATCHFILES_LOG_LEVEL", "DEBUG").upper()
            log_level = getattr(logging, log_level_name, logging.DEBUG)
            ignored_tokens = [
                ".pytest-db",
                "pycache",
                "test.db",
                "test.db-journal",
                "test.db-wal",
            ]
            allowed_suffixes = [".py", ".pyi"]

            for logger_name in ("watchfiles.main", "watchfiles"):
                logger = logging.getLogger(logger_name)
                logger.setLevel(log_level)
                logger.addFilter(_WatchfilesSelectiveFilter(ignored_tokens, allowed_suffixes))

        # Step 3: Test database and services initialization
        # Skip in CI/test mode to avoid heavy model loading which slows or blocks startup
        if os.getenv("TESTING") == "1":
            pass
        else:
            import asyncio

            from core.dependencies import init_services

            asyncio.run(init_services())

        # Step 4: Create FastAPI app
        from core.app import create_app

        create_app()

        # Step 5: Start server

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

        # Simplified reload configuration - only watch .py files in specific dirs
        if reload_dirs:
            pass

        # Configure reload with conservative settings to minimize watchfiles spam
        reload_excludes = None
        if settings.reload:
            reload_excludes = [
                "**/__pycache__/**",
                "**/*.pyc",
                "**/*.pyo",
                "**/*.db",
                "**/*.db-shm",
                "**/*.db-wal",
                "**/*.db-journal",
                "**/logs/**",
                "**/*.log",
                "**/.pytest-db/**",  # Ignore pytest's SQLite scratch space
                "**\\.pytest-db\\**",  # Windows separator variant
            ]

        reload_config = {
            "reload": settings.reload,
            "reload_delay": 2.0,  # Add delay to reduce sensitivity
            "reload_dirs": reload_dirs if settings.reload else None,
            "reload_includes": ["**/*.py"] if settings.reload else None,
            "reload_excludes": reload_excludes,
        }

        # Use factory pattern for proper reload functionality
        uvicorn.run(
            "core.app:create_app",
            factory=True,
            host=settings.host,
            port=settings.port,
            log_level="warning",
            access_log=False,
            **reload_config,
        )

    except ImportError:
        return 1

    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
