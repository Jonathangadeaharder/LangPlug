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
    print("🚀 Starting LangPlug Backend...")
    
    try:
        # Step 1: Test imports
        print("📦 Testing imports...")
        import fastapi
        import uvicorn
        from core.config import settings
        from core.logging import setup_logging
        print("✅ Basic imports successful")
        
        # Step 2: Initialize logging
        print("📝 Setting up logging...")
        logger = setup_logging()
        print("✅ Logging configured")
        
        # Step 3: Test database and services initialization
        print("🗄️ Initializing services...")
        from core.dependencies import init_services
        init_services()
        print("✅ Services initialized")
        
        # Step 4: Create FastAPI app
        print("🌐 Creating FastAPI application...")
        from core.app import create_app
        app = create_app()
        print(f"✅ App created: {app.title}")
        
        # Step 5: Start server
        print(f"🎯 Starting server on {settings.host}:{settings.port}")
        print("📱 Backend will be available at:")
        print(f"   • Health check: http://{settings.host}:{settings.port}/health")
        print(f"   • API docs: http://{settings.host}:{settings.port}/docs")
        print("🔑 Default admin credentials: admin / admin")
        print("\n⚡ Server starting...")
        
        uvicorn.run(
            app,
            host=settings.host,
            port=settings.port,
            reload=settings.reload,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        return 1
        
    except Exception as e:
        print(f"❌ Startup Error: {e}")
        print("\n🔍 Full error traceback:")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
