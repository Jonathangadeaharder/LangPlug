#!/usr/bin/env python3
import sys
import traceback
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def run_with_output():
    """Run the backend and capture all output"""
    try:
        print("Testing backend startup with full error capture...")
        
        # Import and run directly
        from core.config import settings
        from core.logging import setup_logging
        from core.dependencies import init_services
        from core.app import create_app
        
        print("✅ All imports successful")
        
        # Setup logging
        logger = setup_logging()
        print("✅ Logging setup")
        
        # Initialize services
        init_services()
        print("✅ Services initialized")
        
        # Create app
        app = create_app()
        print(f"✅ App created: {app.title}")
        
        # Try to start server
        import uvicorn
        print(f"🚀 Starting server on {settings.host}:{settings.port}")
        uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print(f"Module: {e.name if hasattr(e, 'name') else 'Unknown'}")
        traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Runtime Error: {e}")
        print(f"Error type: {type(e).__name__}")
        traceback.print_exc()

if __name__ == "__main__":
    run_with_output()
