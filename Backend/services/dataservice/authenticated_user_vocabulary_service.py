"""
Authenticated User Vocabulary Data Service
Wraps the SQLite vocabulary service with authentication requirements
"""

from typing import Set, Dict, Any, List
import logging

try:
    from .user_vocabulary_service import SQLiteUserVocabularyService
    from ..filterservice.interface import IUserVocabularyService
    from ...database.models import User
    from ...core.auth import jwt_authentication
    from ...core.database import get_async_session
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
except ImportError:
    # Fallback for when running as script
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    from services.dataservice.user_vocabulary_service import SQLiteUserVocabularyService
    from services.filterservice.interface import IUserVocabularyService
    from database.models import User
    from core.database import get_async_session
    # JWT authentication is now handled through fastapi-users dependency injection
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select

class InsufficientPermissionsError(Exception):
    """Raised when user lacks required permissions"""
    pass


class AuthenticationRequiredError(Exception):
    """Raised when authentication is required but not provided"""
    pass


class AuthenticatedUserVocabularyService(IUserVocabularyService):
    """
    Authentication-wrapped vocabulary service
    Ensures all operations are performed by authenticated users
    """
    
    def __init__(self, db_session: AsyncSession):
        self.vocab_service = SQLiteUserVocabularyService()
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)
    
    def _validate_user_access(self, requesting_user: User, target_user_id: str) -> None:
        """
        Validate that the requesting user can access data for target_user_id
        
        Args:
            requesting_user: The authenticated user making the request
            target_user_id: The user ID whose data is being accessed
            
        Raises:
            InsufficientPermissionsError: If user cannot access the data
        """
        # Users can always access their own data
        if str(requesting_user.id) == target_user_id or requesting_user.username == target_user_id:
            return
        
        # Admins can access any user's data
        if requesting_user.is_admin:
            return
        
        # Otherwise, access is denied
        raise InsufficientPermissionsError(
            f"User '{requesting_user.username}' cannot access data for user '{target_user_id}'"
        )
    
    async def _authenticate_user(self, session_token: str) -> User:
        """
        Authenticate user using JWT token
        
        Args:
            session_token: JWT token
            
        Returns:
            Authenticated user
            
        Raises:
            AuthenticationRequiredError: If authentication fails
        """
        try:
            user = await jwt_authentication.authenticate(session_token, self.db_session)
            if not user:
                raise AuthenticationRequiredError("Invalid or expired session token")
            return user
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            raise AuthenticationRequiredError("Authentication failed")
    
    async def is_word_known(self, requesting_user: User, user_id: str, word: str, language: str = "en") -> bool:
        """
        Check if user knows a specific word (requires authentication)
        
        Args:
            requesting_user: Authenticated user making the request
            user_id: User ID to check data for
            word: Word to check
            language: Language code
            
        Returns:
            True if word is known by user
            
        Raises:
            InsufficientPermissionsError: If user cannot access this data
        """
        self._validate_user_access(requesting_user, user_id)
        
        return await self.vocab_service.is_word_known(user_id, word, language)
    
    async def get_known_words(self, requesting_user: User, user_id: str, language: str = "en") -> Set[str]:
        """
        Get all words known by user (requires authentication)
        
        Args:
            requesting_user: Authenticated user making the request
            user_id: User ID to get data for
            language: Language code
            
        Returns:
            Set of known words
            
        Raises:
            InsufficientPermissionsError: If user cannot access this data
        """
        self._validate_user_access(requesting_user, user_id)
        
        return await self.vocab_service.get_known_words(user_id, language)
    
    async def mark_word_learned(self, requesting_user: User, user_id: str, word: str, language: str = "en") -> bool:
        """
        Mark word as learned by user (requires authentication)
        
        Args:
            requesting_user: Authenticated user making the request
            user_id: User ID to update data for
            word: Word to mark as learned
            language: Language code
            
        Returns:
            True if word was marked as learned
            
        Raises:
            InsufficientPermissionsError: If user cannot modify this data
        """
        self._validate_user_access(requesting_user, user_id)
        
        result = await self.vocab_service.mark_word_learned(user_id, word, language)
        if result:
            self.logger.info(f"User '{requesting_user.username}' marked word '{word}' as learned for user '{user_id}'")
        
        return result
    
    async def get_learning_level(self, requesting_user: User, user_id: str) -> str:
        """
        Get user's current learning level (requires authentication)
        
        Args:
            requesting_user: Authenticated user making the request
            user_id: User ID to get level for
            
        Returns:
            Learning level (A1, A2, B1, B2, C1, C2)
            
        Raises:
            InsufficientPermissionsError: If user cannot access this data
        """
        self._validate_user_access(requesting_user, user_id)
        
        return await self.vocab_service.get_learning_level(user_id)
    
    async def set_learning_level(self, requesting_user: User, user_id: str, level: str) -> bool:
        """
        Set user's learning level (requires authentication)
        
        Args:
            requesting_user: Authenticated user making the request
            user_id: User ID to set level for
            level: Learning level to set
            
        Returns:
            True if level was set successfully
            
        Raises:
            InsufficientPermissionsError: If user cannot modify this data
        """
        self._validate_user_access(requesting_user, user_id)
        
        result = await self.vocab_service.set_learning_level(user_id, level)
        if result:
            self.logger.info(f"User '{requesting_user.username}' set learning level to '{level}' for user '{user_id}'")
        
        return result
    
    async def add_known_words(self, requesting_user: User, user_id: str, words: List[str], language: str = "en") -> bool:
        """
        Add multiple words to user's known vocabulary (requires authentication)
        
        Args:
            requesting_user: Authenticated user making the request
            user_id: User ID to add words for
            words: List of words to add
            language: Language code
            
        Returns:
            True if words were added successfully
            
        Raises:
            InsufficientPermissionsError: If user cannot modify this data
        """
        self._validate_user_access(requesting_user, user_id)
        
        result = await self.vocab_service.add_known_words(user_id, words, language)
        if result:
            self.logger.info(f"User '{requesting_user.username}' added {len(words)} words for user '{user_id}'")
        
        return result
    
    async def get_learning_statistics(self, requesting_user: User, user_id: str, language: str = "en") -> Dict[str, Any]:
        """
        Get learning statistics for user (requires authentication)
        
        Args:
            requesting_user: Authenticated user making the request
            user_id: User ID to get statistics for
            language: Language code
            
        Returns:
            Dictionary with learning statistics
            
        Raises:
            InsufficientPermissionsError: If user cannot access this data
        """
        self._validate_user_access(requesting_user, user_id)
        
        return await self.vocab_service.get_learning_statistics(user_id, language)
    
    async def get_word_learning_history(self, requesting_user: User, user_id: str, word: str, language: str = "en") -> List[Dict[str, Any]]:
        """
        Get learning history for a specific word (requires authentication)
        
        Args:
            requesting_user: Authenticated user making the request
            user_id: User ID to get history for
            word: Word to get history for
            language: Language code
            
        Returns:
            List of learning history entries
            
        Raises:
            InsufficientPermissionsError: If user cannot access this data
        """
        self._validate_user_access(requesting_user, user_id)
        
        return await self.vocab_service.get_word_learning_history(user_id, word, language)
    
    async def get_words_by_confidence(self, requesting_user: User, user_id: str, confidence_level: int, language: str = "en") -> List[Dict[str, Any]]:
        """
        Get words at a specific confidence level (requires authentication)
        
        Args:
            requesting_user: Authenticated user making the request
            user_id: User ID to get words for
            confidence_level: Confidence level to filter by
            language: Language code
            
        Returns:
            List of words at the specified confidence level
            
        Raises:
            InsufficientPermissionsError: If user cannot access this data
        """
        self._validate_user_access(requesting_user, user_id)
        
        return await self.vocab_service.get_words_by_confidence(user_id, confidence_level, language)
    
    async def remove_word(self, requesting_user: User, user_id: str, word: str, language: str = "en") -> bool:
        """
        Remove a word from user's learning progress (requires authentication)
        
        Args:
            requesting_user: Authenticated user making the request
            user_id: User ID to remove word for
            word: Word to remove
            language: Language code
            
        Returns:
            True if word was removed successfully
            
        Raises:
            InsufficientPermissionsError: If user cannot modify this data
        """
        self._validate_user_access(requesting_user, user_id)
        
        result = await self.vocab_service.remove_word(user_id, word, language)
        if result:
            self.logger.info(f"User '{requesting_user.username}' removed word '{word}' for user '{user_id}'")
        
        return result
    
    # Admin-only methods
    async def admin_get_all_user_stats(self, requesting_user: User, language: str = "en") -> Dict[str, Dict[str, Any]]:
        """
        Admin method to get statistics for all users
        
        Args:
            requesting_user: Authenticated admin user making the request
            language: Language code
            
        Returns:
            Dictionary mapping user_id to their statistics
            
        Raises:
            InsufficientPermissionsError: If user is not admin
        """
        if not requesting_user.is_admin:
            raise InsufficientPermissionsError("Admin privileges required")
        
        # Get all users from database
        stmt = select(User)
        result = await self.db_session.execute(stmt)
        all_users = result.scalars().all()
        
        # Collect statistics for each user
        all_stats = {}
        for user in all_users:
            user_id = str(user.id)
            try:
                stats = await self.vocab_service.get_learning_statistics(user_id, language)
                stats['username'] = user.username
                stats['user_id'] = user_id
                all_stats[user_id] = stats
            except Exception as e:
                self.logger.warning(f"Failed to get stats for user {user_id}: {e}")
                all_stats[user_id] = {
                    'username': user.username,
                    'user_id': user_id,
                    'error': str(e),
                    'total_known': 0,
                    'total_learned': 0
                }
        
        return all_stats
    
    async def admin_reset_user_progress(self, requesting_user: User, target_user_id: str) -> bool:
        """
        Admin method to reset a user's learning progress
        
        Args:
            requesting_user: Authenticated admin user making the request
            target_user_id: User ID whose progress to reset
            
        Returns:
            True if progress was reset successfully
            
        Raises:
            InsufficientPermissionsError: If user is not admin
        """
        if not requesting_user.is_admin:
            raise InsufficientPermissionsError("Admin privileges required")
        
        try:
            # Remove all learning progress for the user using async session
            async with self.vocab_service.get_session() as session:
                from sqlalchemy import text
                result = await session.execute(
                    text("DELETE FROM user_learning_progress WHERE user_id = :user_id"),
                    {"user_id": target_user_id}
                )
                await session.commit()
                rows_affected = result.rowcount
            
            self.logger.info(f"Admin '{requesting_user.username}' reset progress for user '{target_user_id}' ({rows_affected} records removed)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reset progress for user '{target_user_id}': {e}")
            return False