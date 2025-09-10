#!/usr/bin/env python3
"""
Simple startup script to test backend functionality
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test all required imports"""
    print("Testing imports...")
    
    try:
        import fastapi
        print("✓ FastAPI")
    except ImportError as e:
        print(f"✗ FastAPI: {e}")
        return False
        
    try:
        import uvicorn
        print("✓ Uvicorn")
    except ImportError as e:
        print(f"✗ Uvicorn: {e}")
        return False
        
    try:
        from core.config import settings
        print(f"✓ Config (host: {settings.host}, port: {settings.port})")
    except Exception as e:
        print(f"✗ Config: {e}")
        return False
        
    try:
        from core.logging import setup_logging
        logger = setup_logging()
        print("✓ Logging")
    except Exception as e:
        print(f"✗ Logging: {e}")
        return False
        
    return True

def test_database():
    """Test database initialization"""
    print("\nTesting database...")
    
    try:
        from database.unified_migration import run_migrations
        from core.config import settings
        
        db_path = settings.get_database_path()
        print(f"Database path: {db_path}")
        
        # Run migrations
        run_migrations(db_path)
        print("✓ Database migrations")
        
        # Test database manager
        from database.database_manager import DatabaseManager
        db_manager = DatabaseManager(str(settings.get_data_path() / "vocabulary.db"))
        print("✓ Database manager")
        
        return True
    except Exception as e:
        print(f"✗ Database: {e}")
        return False

def test_services():
    """Test service initialization"""
    print("\nTesting services...")
    
    try:
        from database.database_manager import DatabaseManager
        from services.authservice.auth_service import AuthService
        from core.config import settings
        
        # Create services
        db_manager = DatabaseManager(str(settings.get_data_path() / "vocabulary.db"))
        auth_service = AuthService(db_manager)
        print("✓ Core services")
        
        return True
    except Exception as e:
        print(f"✗ Services: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_creation():
    """Test FastAPI app creation"""
    print("\nTesting app creation...")
    
    try:
        from core.app import create_app
        app = create_app()
        print(f"✓ App created: {app.title}")
        return True
    except Exception as e:
        print(f"✗ App creation: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("=== LangPlug Backend Startup Test ===")
    
    tests = [
        ("Imports", test_imports),
        ("Database", test_database), 
        ("Services", test_services),
        ("App Creation", test_app_creation)
    ]
    
    for name, test_func in tests:
        print(f"\n--- {name} ---")
        success = test_func()
        if not success:
            print(f"\n❌ {name} test failed - stopping here")
            return False
            
    print("\n🎉 All tests passed! Backend should be ready to start.")
    
    # Try to start the server
    print("\n--- Starting Server ---")
    try:
        import uvicorn
        from core.app import create_app
        from core.config import settings
        
        app = create_app()
        print(f"Starting server on {settings.host}:{settings.port}")
        
        uvicorn.run(
            app,
            host=settings.host,
            port=settings.port,
            reload=settings.reload
        )
        
    except Exception as e:
        print(f"Server startup failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main()
