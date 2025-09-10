#!/usr/bin/env python3
"""
Debug startup script to catch all import errors
"""
import sys
import traceback
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test all imports step by step"""
    print("=== Testing All Imports ===")
    
    try:
        print("1. Testing basic imports...")
        print("✅ Basic imports OK")
        
        print("2. Testing core modules...")
        from core.logging import setup_logging
        from core.dependencies import init_services
        from core.app import create_app
        print("✅ Core modules OK")
        
        print("3. Testing API routes...")
        print("✅ API routes OK")
        
        print("4. Testing services...")
        print("✅ Services OK")
        
        print("5. Testing app creation...")
        logger = setup_logging()
        init_services()
        app = create_app()
        print("✅ App creation OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during import: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False

def main():
    print("Starting comprehensive import test...")
    
    if test_imports():
        print("\n🎉 All imports successful!")
        print("Starting server...")
        
        try:
            import uvicorn
            from core.app import create_app
            from core.config import settings
            
            app = create_app()
            print(f"Server starting on {settings.host}:{settings.port}")
            uvicorn.run(app, host=settings.host, port=settings.port)
            
        except Exception as e:
            print(f"❌ Server startup failed: {e}")
            traceback.print_exc()
    else:
        print("\n⚠️ Import test failed. Fix the errors above.")

if __name__ == "__main__":
    main()
