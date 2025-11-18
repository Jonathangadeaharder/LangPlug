"""Task and lifecycle dependencies for FastAPI"""

from .logging_config import get_logger

logger = get_logger(__name__)

# Global task progress registry for background tasks
_task_progress_registry: dict = {}

# Global readiness flag - tracks whether services are fully initialized
_services_ready: bool = False


def get_task_progress_registry() -> dict:
    """
    Get task progress registry for background tasks

    Note:
        Returns reference to global registry without caching.
        Previously used @lru_cache which caused test state pollution.
    """
    return _task_progress_registry


def is_services_ready() -> bool:
    """Check if all services are initialized and ready to handle requests"""
    return _services_ready


async def init_services():
    """Initialize all services on startup"""
    global _services_ready

    logger.info("[STARTUP] Initializing services...")
    logger.info("[STARTUP] This may take 5-10 minutes on first run to download AI models")

    try:
        # Initialize authentication services
        logger.info("[STARTUP] Step 1/5: Initializing authentication services...")
        from .auth_dependencies import init_auth_services

        init_auth_services()
        logger.info("[STARTUP] Authentication services initialized")

        # Initialize database tables
        logger.info("[STARTUP] Step 2/5: Initializing database...")
        from .database import init_db

        await init_db()
        logger.info("[STARTUP] Database initialized successfully")

        # Initialize transcription service
        logger.info("[STARTUP] Step 3/5: Initializing transcription service...")
        from .config import settings
        from .service_dependencies import get_transcription_service

        logger.info(f"[STARTUP] Using transcription model: {settings.transcription_service}")
        get_transcription_service()
        logger.info("[STARTUP] Transcription service ready")

        # Initialize translation service
        logger.info("[STARTUP] Step 4/5: Initializing translation service...")
        from .service_dependencies import get_translation_service

        logger.info(f"[STARTUP] Using translation model: {settings.translation_service}")
        get_translation_service()
        logger.info("[STARTUP] Translation service ready")

        # Initialize task progress registry
        logger.info("[STARTUP] Step 5/5: Initializing task registry...")
        get_task_progress_registry()

        # Mark services as ready
        _services_ready = True
        logger.info("[STARTUP] All services initialized successfully!")
        logger.info("[STARTUP] Server is ready to handle requests")

    except Exception as e:
        _services_ready = False
        logger.error(f"[STARTUP] Failed to initialize services: {e}", exc_info=True)
        raise


async def cleanup_services():
    """Cleanup services on shutdown"""
    logger.info("Cleaning up services...")

    # Cleanup authentication services
    from .auth_dependencies import cleanup_auth_services

    cleanup_auth_services()

    # Close database engine
    from .database import engine

    await engine.dispose()

    # Clear task progress registry content (not cache, as we removed @lru_cache)
    _task_progress_registry.clear()

    logger.info("Service cleanup complete")


__all__ = ["cleanup_services", "get_task_progress_registry", "init_services", "is_services_ready"]
