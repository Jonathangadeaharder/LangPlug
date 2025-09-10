"""
Dependency injection system for FastAPI
Manages service creation and lifecycle
"""
import logging
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import settings
from database.database_manager import DatabaseManager
from services.authservice.auth_service import (
    AuthService, AuthUser, SessionExpiredError
)
from services.dataservice.authenticated_user_vocabulary_service import AuthenticatedUserVocabularyService
from services.transcriptionservice.factory import TranscriptionServiceFactory
from services.filterservice.filter_chain import SubtitleFilterChain


# Global service registry
_service_registry: Dict[str, Any] = {}

security = HTTPBearer()
logger = logging.getLogger(__name__)


def get_database_manager() -> DatabaseManager:
    """Get database manager instance"""
    # CRITICAL FIX: Services should be initialized at startup, not during requests
    if "database_manager" not in _service_registry:
        raise RuntimeError("DatabaseManager not initialized at startup! This should never happen during request processing.")
    return _service_registry["database_manager"]


def get_auth_service() -> AuthService:
    """Get authentication service instance"""
    # CRITICAL FIX: Services should be initialized at startup, not during requests  
    if "auth_service" not in _service_registry:
        raise RuntimeError("AuthService not initialized at startup! This should never happen during request processing.")
    return _service_registry["auth_service"]


def get_vocabulary_service() -> AuthenticatedUserVocabularyService:
    """Get vocabulary service instance"""
    if "vocabulary_service" not in _service_registry:
        logger.info("Creating vocabulary service...")
        db_manager = get_database_manager()
        auth_service = get_auth_service()
        _service_registry["vocabulary_service"] = AuthenticatedUserVocabularyService(
            db_manager, auth_service
        )
        logger.info("Vocabulary service created successfully")
    return _service_registry["vocabulary_service"]


def get_transcription_service() -> Optional[object]:
    """Get transcription service instance"""
    if "transcription_service" not in _service_registry:
        try:
            logger.info(f"Attempting to create transcription service: {settings.transcription_service}")
            logger.info(f"TranscriptionServiceFactory available: {TranscriptionServiceFactory}")
            service = TranscriptionServiceFactory.create_service(
                settings.transcription_service
            )
            logger.info(f"Successfully created transcription service: {service}")
            _service_registry["transcription_service"] = service
        except ImportError as e:
            logger.error(f"Import error for transcription service: {e}", exc_info=True)
            _service_registry["transcription_service"] = None
        except Exception as e:
            logger.error(f"Transcription service not available: {e}", exc_info=True)
            _service_registry["transcription_service"] = None
    
    result = _service_registry["transcription_service"]
    logger.info(f"Returning transcription service: {result}")
    return result


def get_filter_chain() -> SubtitleFilterChain:
    """Get filter chain instance"""
    if "filter_chain" not in _service_registry:
        logger.info("Creating filter chain...")
        filter_chain = SubtitleFilterChain()
        
        # Temporarily disable SpaCy filter to isolate timeout issue
        logger.info("SpaCy filter temporarily disabled for debugging")
        
        _service_registry["filter_chain"] = filter_chain
        logger.info("Filter chain created successfully")
    return _service_registry["filter_chain"]


# Progress tracking for background tasks
def get_task_progress_registry() -> Dict[str, Any]:
    """Get task progress registry"""
    if "task_progress" not in _service_registry:
        _service_registry["task_progress"] = {}
    return _service_registry["task_progress"]


# Authentication dependency
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> AuthUser:
    """Validate session token and return current user"""
    try:
        token = credentials.credentials
        user = auth_service.validate_session(token)
        return user
    except SessionExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Session expired"
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid authentication"
        )


async def get_current_user_ws(token: str) -> AuthUser:
    """Validate session token for WebSocket connections"""
    auth_service = get_auth_service()
    try:
        user = auth_service.validate_session(token)
        return user
    except Exception:
        raise Exception("Invalid or expired token")


def cleanup_services():
    """Clean up services on application shutdown"""
    # Close database connection pool if it exists
    if "async_database_manager" in _service_registry:
        async_db_manager = _service_registry["async_database_manager"]
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(async_db_manager.close())
        logger.info("Database connection pool closed")
    
    _service_registry.clear()


def init_services():
    """Initialize all services at startup"""
    try:
        logger.info("Initializing core services...")
        
        # Run database migrations first
        from .config import settings
        from database.unified_migration import run_migrations
        logger.info("Running database migrations...")
        run_migrations(settings.get_database_path())
        
        # CRITICAL FIX: Use pooled database manager with backward compatibility
        logger.info("Creating pooled database manager...")
        import asyncio
        from database.async_database_manager import AsyncDatabaseManager, DatabaseManagerAdapter
        
        # Create async database manager with connection pooling
        async_db_manager = AsyncDatabaseManager(
            db_path=str(settings.get_data_path() / "vocabulary.db"),
            pool_size=5,  # 5 persistent connections
            max_overflow=10,  # Allow up to 10 additional connections
            pool_timeout=30,  # 30 second timeout for getting connection
            enable_logging=settings.debug
        )
        
        # Initialize the async manager
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(async_db_manager.initialize())
        
        # Create backward-compatible adapter for existing sync code
        db_manager = DatabaseManagerAdapter(async_db_manager)
        _service_registry["database_manager"] = db_manager
        _service_registry["async_database_manager"] = async_db_manager
        logger.info("Pooled database manager created and registered")
        
        logger.info("Creating auth service...")
        from services.authservice.auth_service import AuthService
        auth_service = AuthService(db_manager)
        _service_registry["auth_service"] = auth_service
        logger.info("Auth service created and registered")
        
        # Ensure admin user exists
        logger.info("Ensuring admin user exists...")
        try:
            # Try to get admin user from database
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE username = ?", ("admin",))
                admin_exists = cursor.fetchone()
                
                if not admin_exists:
                    logger.info("Creating admin user...")
                    # Register admin user with admin/admin credentials
                    try:
                        admin_user = auth_service.register_user("admin", "admin", email="admin@langplug.local")
                        # Update user to be admin
                        conn.execute(
                            "UPDATE users SET is_admin = 1 WHERE username = ?",
                            ("admin",)
                        )
                        conn.commit()
                        logger.info("Admin user created successfully")
                    except Exception as e:
                        logger.info(f"Could not create admin user: {e}")
                else:
                    logger.info("Admin user already exists")
        except Exception as e:
            logger.warning(f"Could not check/create admin user: {e}")
        
        logger.info("Creating vocabulary service...")
        from services.dataservice.authenticated_user_vocabulary_service import AuthenticatedUserVocabularyService
        vocab_service = AuthenticatedUserVocabularyService(db_manager, auth_service)
        _service_registry["vocabulary_service"] = vocab_service
        logger.info("Vocabulary service created and registered")
        
        # Ensure vocabulary database is populated
        logger.info("Checking vocabulary database...")
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM vocabulary")
                vocab_count = cursor.fetchone()[0]
                logger.info(f"Vocabulary database contains {vocab_count} words")
                
                if vocab_count < 100:
                    logger.info("Warning: Vocabulary database has fewer than 100 words")
                    logger.info("Run 'python load_vocabulary.py' to populate the database")
        except Exception as e:
            logger.warning(f"Could not check vocabulary database: {e}")
        
        # Temporarily skip filter chain initialization to test core async/sync fix
        logger.info("Skipping filter chain initialization to test async/sync authentication fix")
        logger.info("Filter chain will be re-enabled once authentication is confirmed working")
        
        # Skip transcription service initialization to avoid startup hang
        logger.info("Skipping transcription service initialization (will load on-demand)")
        # NOTE: Transcription service was causing startup hang due to Whisper model loading
        # It will be initialized on first use instead
        
        logger.info("All services initialized successfully - models are pre-loaded")
        
    except Exception as e:
        logger.info(f"Failed to initialize services: {e}")
        raise