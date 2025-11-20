"""
FastAPI application factory
"""

import sys
import warnings
from contextlib import asynccontextmanager
from datetime import datetime

# Configure asyncio event loop for Windows subprocess support BEFORE any async operations
if sys.platform == "win32":
    import asyncio

    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI

# Suppress pkg_resources deprecation warning from passlib
# This is a known issue with passlib that will be fixed when they migrate away from pkg_resources
warnings.filterwarnings("ignore", message="pkg_resources is deprecated", category=UserWarning)

from api.routes import (
    auth,
    debug,
    game,
    parallel_transcription_routes,
    processing,
    progress,
    quiz_routes,
    srt_utilities,
    test,
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

        def _log_cleanup_result(task: "asyncio.Task[None]") -> None:
            try:
                task.result()
            except Exception as cleanup_error:
                logger.warning("Cleanup task failed: %s", cleanup_error, exc_info=True)

        try:
            cleanup_task = asyncio.create_task(cleanup_services())
            cleanup_task.add_done_callback(_log_cleanup_result)
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

    # Set up security middleware (CORS, logging, validation)
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

    # Readiness check endpoint - returns whether services are fully initialized
    @app.get("/readiness")
    async def readiness_check():
        """
        Readiness check endpoint - verifies that all services are initialized

        Returns 200 when ready, 503 when still initializing
        """
        from .task_dependencies import is_services_ready

        ready = is_services_ready()

        if ready:
            return {
                "status": "ready",
                "message": "All services initialized and ready to handle requests",
                "timestamp": datetime.now().isoformat(),
            }
        else:
            from fastapi import Response

            return Response(
                status_code=503,
                content='{"status":"initializing","message":"Services are still initializing. Please wait."}',
                media_type="application/json",
            )

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
    app.include_router(parallel_transcription_routes.router, prefix="/api/processing")
    app.include_router(vocabulary.router, prefix="/api/vocabulary")
    app.include_router(quiz_routes.router, prefix="/api")
    app.include_router(user_profile.router, prefix="/api/profile")
    app.include_router(websocket.router, prefix="/api/ws")
    app.include_router(progress.router, prefix="/api/progress")
    app.include_router(game.router, prefix="/api/game")
    app.include_router(srt_utilities.router)  # Already includes /api/srt prefix

    # Only include debug and test routes in debug mode
    if settings.debug:
        app.include_router(debug.router, prefix="/api/debug")
        app.include_router(test.router, prefix="/api/test")
        logger.info("Debug and test routes enabled (debug mode)")
    else:
        logger.info("Debug and test routes disabled (production mode)")

    logger.info("FastAPI application created and configured")
    return app


# Create the app instance
app = create_app()
