"""
FastAPI application factory
"""
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI

from .config import settings
from .logging import setup_logging
from .middleware import setup_middleware
from .dependencies import init_services, cleanup_services
from api.routes import auth, videos, processing, vocabulary, debug, user_profile, websocket

# Initialize logging first
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application resources"""
    try:
        logger.info("Starting LangPlug API server...")
        
        # Initialize all services
        init_services()
        
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
    
    # Include API routers without prefix (proxy will handle /api routing)
    app.include_router(auth.router)
    app.include_router(videos.router)
    app.include_router(processing.router)
    app.include_router(vocabulary.router)
    app.include_router(user_profile.router)
    app.include_router(websocket.router)
    
    # Only include debug routes in debug mode
    if settings.debug:
        app.include_router(debug.router)
        logger.info("Debug routes enabled (debug mode)")
    else:
        logger.info("Debug routes disabled (production mode)")
    
    logger.info("FastAPI application created and configured")
    return app