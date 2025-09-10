#!/usr/bin/env python3
"""Simple step-by-step import test"""
import sys
import traceback
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_step_by_step():
    """Test imports one by one"""
    steps = [
        ("Basic FastAPI", lambda: __import__('fastapi')),
        ("Basic uvicorn", lambda: __import__('uvicorn')),
        ("Core config", lambda: __import__('core.config')),
        ("Core logging", lambda: __import__('core.logging')),
        ("Core dependencies", lambda: __import__('core.dependencies')),
        ("Core app", lambda: __import__('core.app')),
        ("API routes auth", lambda: __import__('api.routes.auth')),
        ("API routes videos", lambda: __import__('api.routes.videos')),
        ("API routes processing", lambda: __import__('api.routes.processing')),
        ("API routes vocabulary", lambda: __import__('api.routes.vocabulary')),
        ("API routes debug", lambda: __import__('api.routes.debug')),
        ("API routes user_profile", lambda: __import__('api.routes.user_profile')),
        ("API routes websocket", lambda: __import__('api.routes.websocket')),
        ("Auth service", lambda: __import__('services.authservice.auth_service')),
        ("Database manager", lambda: __import__('database.database_manager')),
    ]
    
    for step_name, test_func in steps:
        try:
            print(f"Testing {step_name}...", end=" ")
            test_func()
            print("✅")
        except Exception as e:
            print(f"❌ ERROR: {e}")
            print(f"Full error for {step_name}:")
            traceback.print_exc()
            return False
    
    return True

if __name__ == "__main__":
    print("=== Step-by-step Import Test ===")
    success = test_step_by_step()
    
    if success:
        print("\n🎉 All imports successful!")
        try:
            from core.logging import setup_logging
            from core.dependencies import init_services
            from core.app import create_app
            
            setup_logging()
            init_services()
            app = create_app()
            print(f"✅ App created successfully: {app.title}")
        except Exception as e:
            print(f"❌ App creation failed: {e}")
            traceback.print_exc()
    else:
        print("\n❌ Import test failed!")
