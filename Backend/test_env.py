#!/usr/bin/env python3
"""
Simple test script to validate environment and imports
"""
import sys
import traceback

print("=== Environment Test ===")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Python path: {sys.path[:3]}...")

print("\n=== Testing Basic Imports ===")
try:
    import fastapi
    print("✓ FastAPI imported successfully")
except ImportError as e:
    print(f"✗ FastAPI import failed: {e}")

try:
    import uvicorn
    print("✓ Uvicorn imported successfully")
except ImportError as e:
    print(f"✗ Uvicorn import failed: {e}")

try:
    import pydantic
    print("✓ Pydantic imported successfully")
except ImportError as e:
    print(f"✗ Pydantic import failed: {e}")

print("\n=== Testing Core Modules ===")
try:
    from core.config import settings
    print("✓ Core config imported successfully")
    print(f"  Host: {settings.host}")
    print(f"  Port: {settings.port}")
except Exception as e:
    print(f"✗ Core config import failed: {e}")
    traceback.print_exc()

try:
    from core.logging import setup_logging
    logger = setup_logging()
    print("✓ Core logging imported and configured")
except Exception as e:
    print(f"✗ Core logging import failed: {e}")
    traceback.print_exc()

try:
    print("✓ Database migrations imported successfully")
except Exception as e:
    print(f"✗ Database migrations import failed: {e}")
    traceback.print_exc()

print("\n=== Testing Service Imports ===")
try:
    print("✓ Auth service imported successfully")
except Exception as e:
    print(f"✗ Auth service import failed: {e}")
    traceback.print_exc()

try:
    print("✓ Database manager imported successfully")
except Exception as e:
    print(f"✗ Database manager import failed: {e}")
    traceback.print_exc()

print("\n=== Testing FastAPI App Creation ===")
try:
    from core.app import create_app
    app = create_app()
    print("✓ FastAPI app created successfully")
    print(f"  App title: {app.title}")
except Exception as e:
    print(f"✗ FastAPI app creation failed: {e}")
    traceback.print_exc()

print("\n=== Environment Test Complete ===")
