"""Simplified dependency injection for FastAPI using native Depends system"""
from typing import Optional, Annotated
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import get_async_session as get_db_session, engine
from .auth import get_user_manager, current_active_user
from .logging_config import get_logger
from database.models import User
from services.dataservice.authenticated_user_vocabulary_service import AuthenticatedUserVocabularyService
from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor
from services.transcriptionservice.factory import get_transcription_service as _get_transcription_service
from services.transcriptionservice.interface import ITranscriptionService

security = HTTPBearer()
logger = get_logger(__name__)


# Database session dependency is now handled by core.database.get_db_session

# Authentication is now handled by FastAPI-Users
# Use current_active_user from core.auth for authentication


def get_vocabulary_service(
    db: Annotated[AsyncSession, Depends(get_db_session)]
) -> AuthenticatedUserVocabularyService:
    """Get vocabulary service instance"""
    return AuthenticatedUserVocabularyService(db)


def get_subtitle_processor(
    db: Annotated[AsyncSession, Depends(get_db_session)]
) -> DirectSubtitleProcessor:
    """Get subtitle processor instance"""
    return DirectSubtitleProcessor()


@lru_cache()
def get_transcription_service() -> Optional[ITranscriptionService]:
    """Get transcription service instance (singleton)"""
    try:
        return _get_transcription_service()
    except Exception as e:
        logger.error(f"Failed to create transcription service: {e}")
        return None


# Backward compatibility function for tests
def get_user_filter_chain(user, session_token):
    """Get user filter chain for backward compatibility with tests"""
    # This is a legacy function kept for test compatibility
    # In production, we use DirectSubtitleProcessor directly
    from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor
    from .database import get_async_session
    
    class LegacyFilterChainWrapper:
        def __init__(self):
            self.processor = None
            
        async def process_file(self, srt_path: str, user_id: int):
            """Process SRT file using DirectSubtitleProcessor"""
            if not self.processor:
                # Create a new session for this operation
                async with get_async_session() as session:
                    self.processor = DirectSubtitleProcessor()
                    return await self.processor.process_file(srt_path, user_id)
            else:
                return await self.processor.process_file(srt_path, user_id)
    
    return LegacyFilterChainWrapper()


# Authentication is now handled by FastAPI-Users current_active_user
# Import and use current_active_user from core.auth

async def get_current_user_ws(
    token: str,
    db: Annotated[AsyncSession, Depends(get_db_session)]
) -> User:
    """Validate session token for WebSocket connections"""
    from .auth import jwt_authentication
    
    try:
        user = await jwt_authentication.authenticate(token, db)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication"
            )
        return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication"
        )


# Optional user dependency (for endpoints that work with or without auth)
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Annotated[AsyncSession, Depends(get_db_session)] = None
) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    if not credentials:
        return None
    
    try:
        from .auth import jwt_authentication
        token = credentials.credentials
        user = await jwt_authentication.authenticate(token, db)
        return user
    except Exception:
        return None


def get_user_subtitle_processor(
    current_user: Annotated[User, Depends(current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)]
) -> DirectSubtitleProcessor:
    """Get subtitle processor for authenticated user"""
    return DirectSubtitleProcessor()


# Backward compatibility functions for tests
def get_auth_service():
    """Get auth service for backward compatibility with tests"""
    from .auth import fastapi_users, get_user_manager
    return fastapi_users


def get_database_manager():
    """Get database manager for backward compatibility with tests"""
    return engine


# Global task progress registry for background tasks
_task_progress_registry: dict = {}


@lru_cache()
def get_task_progress_registry() -> dict:
    """Get task progress registry for background tasks"""
    return _task_progress_registry


async def init_services():
    """Initialize all services on startup"""
    logger.info("Initializing services...")
    
    # Initialize database tables
    from .database import init_db
    await init_db()
    
    # Initialize transcription service
    get_transcription_service()
    
    # Initialize task progress registry
    get_task_progress_registry()
    
    logger.info("All services initialized successfully")


async def cleanup_services():
    """Cleanup services on shutdown"""
    logger.info("Cleaning up services...")
    
    # Close database engine
    from .database import engine
    await engine.dispose()
    
    # Clear LRU cache for singleton services
    get_transcription_service.cache_clear()
    get_task_progress_registry.cache_clear()
    
    logger.info("Service cleanup complete")


# Export commonly used dependencies for convenience
__all__ = [
    'get_vocabulary_service',
    'get_subtitle_processor',
    'get_transcription_service',
    'get_user_subtitle_processor',
    'get_task_progress_registry',
    'get_current_user_ws',
    'get_optional_user',
    'current_active_user',
    'security',
    'init_services',
    'cleanup_services',
    'get_auth_service',
    'get_database_manager',
    'get_user_filter_chain'
]