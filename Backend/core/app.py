"""
FastAPI application factory
"""
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI

from .config import settings
from .logging_config import setup_logging
from .middleware import setup_middleware
from .dependencies import init_services, cleanup_services
from api.routes import auth, videos, processing, vocabulary, debug, user_profile, websocket, logs, progress, game

# Initialize logging first
log_file = setup_logging()
import logging
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application resources"""
    try:
        logger.info("Starting LangPlug API server...")
        
        # Initialize all services
        await init_services()
        
        logger.info("LangPlug API server started successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        raise
    finally:
        logger.info("Shutting down LangPlug API server...")
        cleanup_services()
        logger.info("LangPlug API server shut down complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    # Create FastAPI app
    app = FastAPI(
        title="LangPlug API",
        description="German Language Learning Platform API",
        version="1.0.0",
        lifespan=lifespan,
        debug=settings.debug
    )
    
    # Set up middleware (CORS, logging, error handling)
    setup_middleware(app)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy", 
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "debug": settings.debug
        }
    
    # Simple test endpoint
    @app.get("/test")
    async def test_endpoint():
        """Simple test endpoint"""
        return {"message": "Test endpoint is working!", "timestamp": datetime.now().isoformat()}
    
    # Include API routers with /api prefix
    app.include_router(auth.router, prefix="/api/auth")
    app.include_router(videos.router, prefix="/api/videos")
    app.include_router(processing.router, prefix="/api/process")
    app.include_router(vocabulary.router, prefix="/api/vocabulary")
    app.include_router(user_profile.router, prefix="/api/profile")
    app.include_router(websocket.router, prefix="/api/ws")
    app.include_router(logs.router, prefix="/api/logs")
    app.include_router(progress.router, prefix="/api/progress")
    app.include_router(game.router, prefix="/api/game")
    
    # Only include debug routes in debug mode
    if settings.debug:
        app.include_router(debug.router, prefix="/api/debug")
        logger.info("Debug routes enabled (debug mode)")
    else:
        logger.info("Debug routes disabled (production mode)")
    
    logger.info("FastAPI application created and configured")
    return app


# Create the app instance
app = create_app()