#!/usr/bin/env python3
"""
LangPlug Backend Startup Script with Error Handling
"""
import sys
import traceback
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Main startup function with comprehensive error handling"""
    print("Starting LangPlug Backend...")

    try:
        # Step 1: Test imports
        print("Testing imports...")
        import fastapi
        import uvicorn

        from core.config import settings
        from core.logging_config import setup_logging
        print("Basic imports successful")

        # Step 2: Initialize logging
        print("Setting up logging...")
        setup_logging()
        print("Logging configured")

        # Enable debug logging for watchfiles to see which files are changing
        if settings.reload:
            import logging
            logging.getLogger("watchfiles.main").setLevel(logging.DEBUG)
            logging.getLogger("watchfiles").setLevel(logging.DEBUG)

        # Step 3: Test database and services initialization
        print("Initializing services...")
        import asyncio

        from core.dependencies import init_services
        asyncio.run(init_services())
        print("Services initialized")

        # Step 4: Create FastAPI app
        print("Creating FastAPI application...")
        from core.app import create_app
        app = create_app()
        print(f"App created: {app.title}")

        # Step 5: Start server
        print(f"Starting server on {settings.host}:{settings.port}")
        print("Backend will be available at:")
        print(f"   • Health check: http://{settings.host}:{settings.port}/health")
        print(f"   • API docs: http://{settings.host}:{settings.port}/docs")
        print("Default admin credentials: admin / admin")
        print("\nServer starting...")

        # Only watch specific directories to avoid SQLite WAL file spam
        reload_dirs = [
            str(Path(__file__).parent / "api"),
            str(Path(__file__).parent / "core"),
            str(Path(__file__).parent / "services")
        ] if settings.reload else None

        # Simplified reload configuration - only watch .py files in specific dirs
        if reload_dirs:
            print(f"Watching directories: {reload_dirs}")

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
                "**/*.log"
            ] if settings.reload else None
        }

        # Use factory pattern for proper reload functionality
        uvicorn.run(
            "core.app:create_app",
            factory=True,
            host=settings.host,
            port=settings.port,
            log_level="info",
            **reload_config
        )

    except ImportError as e:
        print(f"Import Error: {e}")
        print("Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        return 1

    except Exception as e:
        print(f"Startup Error: {e}")
        print("\nFull error traceback:")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
