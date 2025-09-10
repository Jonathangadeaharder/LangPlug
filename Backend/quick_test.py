#!/usr/bin/env python3
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Test the startup process step by step
def main():
    print("Testing backend startup...")
    
    try:
        # Test imports
        from core.config import settings
        from core.logging import setup_logging
        print("✅ Imports OK")
        
        # Setup logging
        logger = setup_logging()
        print("✅ Logging OK")
        
        # Test database migration
        from database.unified_migration import run_migrations
        db_path = settings.get_database_path()
        print(f"Database path: {db_path}")
        run_migrations(db_path)
        print("✅ Database migrations OK")
        
        # Test services
        from core.dependencies import init_services
        init_services()
        print("✅ Services OK")
        
        # Test app creation
        from core.app import create_app
        app = create_app()
        print("✅ App creation OK")
        
        # Start server
        import uvicorn
        print(f"Starting server on {settings.host}:{settings.port}")
        uvicorn.run(app, host=settings.host, port=settings.port)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main()
