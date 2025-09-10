#!/usr/bin/env python3
"""
Test backend startup with detailed output
"""
import sys
import traceback
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_startup():
    """Test if backend can start successfully"""
    print("=== Testing Backend Startup ===")
    
    try:
        # Test basic imports
        print("1. Testing imports...")
        from core.config import settings
        from core.logging import setup_logging
        print("   ✅ Basic imports OK")
        
        # Setup logging
        print("2. Setting up logging...")
        logger = setup_logging()
        print("   ✅ Logging OK")
        
        # Test services initialization
        print("3. Testing services initialization...")
        from core.dependencies import init_services
        init_services()
        print("   ✅ Services initialized")
        
        # Test app creation
        print("4. Testing app creation...")
        from core.app import create_app
        app = create_app()
        print(f"   ✅ App created: {app.title}")
        
        # Test that we can start uvicorn (don't actually start it)
        print("5. Validating server config...")
        print(f"   Host: {settings.host}")
        print(f"   Port: {settings.port}")
        print(f"   Debug: {settings.debug}")
        print("   ✅ Config OK")
        
        print("\n🎉 Backend startup test PASSED!")
        print("Backend should start successfully now.")
        return True
        
    except Exception as e:
        print(f"\n❌ Backend startup test FAILED: {e}")
        print("\n🔍 Full traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_startup()
    if success:
        print("\n▶️ Starting backend server...")
        try:
            import uvicorn
            from core.app import create_app
            from core.config import settings
            
            app = create_app()
            print(f"Starting on {settings.host}:{settings.port}")
            uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")
        except KeyboardInterrupt:
            print("\n⏹️ Server stopped by user")
        except Exception as e:
            print(f"\n❌ Server failed to start: {e}")
            traceback.print_exc()
    else:
        print("\n⚠️ Fix the issues above before starting the server")
        sys.exit(1)
