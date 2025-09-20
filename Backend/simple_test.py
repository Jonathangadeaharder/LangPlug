#!/usr/bin/env python3
"""
Simple test script to check if basic imports work
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("Testing basic imports...")
    try:
        import fastapi
        print("FastAPI import successful")
    except Exception as e:
        print(f"FastAPI import failed: {e}")
        return 1
    
    try:
        import uvicorn
        print("Uvicorn import successful")
    except Exception as e:
        print(f"Uvicorn import failed: {e}")
        return 1
    
    try:
        from core.config import settings
        print("Settings import successful")
        print(f"Host: {settings.host}")
        print(f"Port: {settings.port}")
    except Exception as e:
        print(f"Settings import failed: {e}")
        return 1
    
    print("All basic imports successful")
    return 0

if __name__ == "__main__":
    exit(main())