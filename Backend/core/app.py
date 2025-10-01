"""
FastAPI application factory
"""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI

from api.routes import (
    auth,
    debug,
    game,
    processing,
    progress,
    srt_utilities,
    user_profile,
    videos,
    vocabulary,
    websocket,
)

from .config import settings
from .contract_middleware import setup_contract_validation
from .dependencies import cleanup_services, init_services
from .exception_handlers import setup_exception_handlers
from .logging_config import configure_logging, get_logger
from .middleware import setup_middleware
from .security_middleware import setup_security_middleware
from .sentry_config import configure_sentry

# Initialize logging and Sentry
configure_logging()
configure_sentry()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application resources"""
    try:
        # Import os at the beginning
        import os

        from .config import settings

        # Log startup information including port
        port = int(os.environ.get("LANGPLUG_PORT", settings.port))
        host = settings.host
        logger.info(f"Starting LangPlug API server on http://{host}:{port}...")

        # Initialize all services (skip in test mode)
        if os.environ.get("TESTING") != "1":
            await init_services()
        else:
            logger.info("Skipping service initialization in test mode")

        logger.info(f"LangPlug API server started successfully on port {port}")
        yield

    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        raise
    finally:
        logger.info("Shutting down LangPlug API server...")
        # Note: cleanup_services is async but called in sync context during shutdown
        # This is acceptable as it's a cleanup operation
        import asyncio

        try:
            asyncio.create_task(cleanup_services())
        except RuntimeError:
            # If no event loop is running, skip cleanup
            pass
        logger.info("LangPlug API server shut down complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    # Create FastAPI app
    app = FastAPI(
        title="LangPlug API",
        description="German Language Learning Platform API",
        version="1.0.0",
        lifespan=lifespan,
        debug=settings.debug,
    )

    # Set up middleware (CORS, logging, error handling)
    setup_middleware(app)

    # Set up security middleware
    setup_security_middleware(app, settings)

    # Set up contract validation (only in debug mode for development)
    if settings.debug:
        setup_contract_validation(app, validate_requests=True, validate_responses=True, log_violations=True)

    # Set up exception handlers
    setup_exception_handlers(app)

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "debug": settings.debug,
        }

    # Simple test endpoint
    @app.get("/test")
    async def test_endpoint():
        """Simple test endpoint"""
        return {"message": "Test endpoint is working!", "timestamp": datetime.now().isoformat()}

    # Include FastAPI-Users authentication routes
    from .auth import UserCreate, UserRead, auth_backend, fastapi_users

    app.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/api/auth", tags=["auth"])
    app.include_router(
        fastapi_users.get_register_router(UserRead, UserCreate),
        prefix="/api/auth",
        tags=["auth"],
    )

    # Include API routers with /api prefix
    app.include_router(auth.router, prefix="/api/auth")
    app.include_router(videos.router, prefix="/api/videos")
    app.include_router(processing.router, prefix="/api/process")
    app.include_router(vocabulary.router, prefix="/api/vocabulary")
    app.include_router(user_profile.router, prefix="/api/profile")
    app.include_router(websocket.router, prefix="/api/ws")
    app.include_router(progress.router, prefix="/api/progress")
    app.include_router(game.router, prefix="/api/game")
    app.include_router(srt_utilities.router)  # Already includes /api/srt prefix

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
