"""
Simple and clean authentication service for LangPlug
No complex dependencies, no fancy logging, just works
"""

import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
from passlib.context import CryptContext

from database.unified_database_manager import UnifiedDatabaseManager as DatabaseManager
from services.repository.user_repository import UserRepository, User
from .models import (
    AuthUser, AuthSession, AuthenticationError, 
    InvalidCredentialsError, UserAlreadyExistsError, SessionExpiredError
)

class AuthService:
    """
    Simple authentication service with secure bcrypt password hashing
    Uses database-based session storage for scalability and persistence
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.user_repository = UserRepository(db_manager)
        # Initialize password context with bcrypt
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        # Set default session lifetime
        self.session_lifetime_hours = 24
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return self.pwd_context.hash(password)
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against bcrypt hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def register_user(self, username: str, password: str) -> AuthUser:
        """Register a new user"""
        # Validate input
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        
        # Check if user exists using UserRepository
        existing_user = self.user_repository.find_by_username(username)
        if existing_user:
            raise UserAlreadyExistsError(f"User '{username}' already exists")
        
        # Create user with hashed password (bcrypt includes salt internally)
        password_hash = self._hash_password(password)
        
        try:
            # Use UserRepository to create user
            user_id = self.user_repository.create_from_data(
                username=username,
                password_hash=password_hash,
                is_active=True,
                native_language="en",
                target_language="de"
            )
            
            return AuthUser(
                id=user_id,
                username=username,
                is_admin=False,
                is_active=True,
                created_at=datetime.now().isoformat(),
                native_language="en",
                target_language="de"
            )
            
        except Exception as e:
            raise AuthenticationError(f"Failed to register user: {e}")
    
    def login(self, username: str, password: str) -> AuthSession:
        """Login user and create session"""
        # Get user from database using UserRepository
        user = self.user_repository.find_by_username(username)
        if not user:
            raise InvalidCredentialsError("Invalid username or password")
        
        # Convert User to dict for compatibility with existing code
        user_data = {
            'id': user.id,
            'username': user.username,
            'password_hash': user.password_hash,
            'salt': getattr(user, 'salt', ''),  # For legacy users
            'is_admin': user.is_admin,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat() if user.created_at else '',
            'updated_at': getattr(user, 'updated_at', datetime.now()).isoformat() if getattr(user, 'updated_at') else '',
            'last_login': getattr(user, 'last_login', None),
            'native_language': getattr(user, 'native_language', 'en'),
            'target_language': getattr(user, 'target_language', 'de')
        }
        
        # Check if user needs password migration (from SHA256 to bcrypt)
        # For legacy users with salt, assume they need migration
        needs_migration = bool(user_data.get('salt'))
        
        if needs_migration and user_data.get('salt'):
            # Old SHA256 verification for legacy users
            old_hash = hashlib.sha256(f"{password}{user_data['salt']}".encode()).hexdigest()
            if user_data['password_hash'] != old_hash:
                raise InvalidCredentialsError("Invalid username or password")
            
            # Migrate to bcrypt on successful login
            new_hash = self._hash_password(password)
            self.user_repository.update_password_hash(user.id, new_hash)
            
        else:
            # Verify password using bcrypt for new/migrated users
            if not self._verify_password(password, user_data['password_hash']):
                raise InvalidCredentialsError("Invalid username or password")
        
        # Create session token
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=self.session_lifetime_hours)
        
        # Store session in database
        try:
            expires_at_iso = expires_at.isoformat()
            self.user_repository.create_session(user_data['id'], session_token, expires_at_iso)
        except Exception as e:
            raise AuthenticationError(f"Failed to create session: {e}")
        
        # Update last login using UserRepository
        self.user_repository.update_last_login(user.id)
        
        # Create AuthUser object for session
        auth_user = AuthUser(
            id=user.id,
            username=user.username,
            is_admin=user.is_admin,
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else '',
            native_language=getattr(user, 'native_language', 'en'),
            target_language=getattr(user, 'target_language', 'de'),
            last_login=getattr(user, 'last_login', None)
        )
        
        return AuthSession(
            session_token=session_token,
            user=auth_user,
            expires_at=expires_at,
            created_at=datetime.now()
        )
    
    def validate_session(self, session_token: str) -> AuthUser:
        """Validate session token and return user"""
        # Get session from database using UserRepository
        try:
            session_data = self.user_repository.get_active_session_with_user(session_token)
            
            if not session_data:
                raise SessionExpiredError("Invalid or expired session")
            
            # Check if session is expired
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            if datetime.now() > expires_at:
                # Mark session as inactive using UserRepository
                self.user_repository.mark_session_inactive(session_token)
                raise SessionExpiredError("Session has expired")
            
            # Update last used timestamp using UserRepository
            self.user_repository.update_session_last_used(session_token)
            
            return AuthUser(
                id=session_data['id'],
                username=session_data['username'],
                is_admin=bool(session_data.get('is_admin', False)),
                is_active=bool(session_data.get('user_is_active', True)),
                created_at=session_data.get('created_at', ''),
                last_login=session_data.get('last_login'),
                native_language=session_data.get('native_language', 'en'),
                target_language=session_data.get('target_language', 'de')
            )
        except SessionExpiredError:
            raise
        except Exception as e:
            raise AuthenticationError(f"Failed to validate session: {e}")
    
    def logout(self, session_token: str) -> bool:
        """Logout user by deactivating session"""
        try:
            # Use UserRepository to deactivate session
            return self.user_repository.deactivate_session(session_token)
        except Exception as e:
            raise AuthenticationError(f"Failed to logout: {e}")
    
    def update_language_preferences(self, user_id: int, native_language: str, target_language: str) -> bool:
        """Update user's language preferences"""
        try:
            # Use UserRepository to update language preferences
            return self.user_repository.update_language_preference(user_id, native_language, target_language)
        except Exception as e:
            raise AuthenticationError(f"Failed to update language preferences: {e}")
    
    def _get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user from database by username using UserRepository"""
        user = self.user_repository.find_by_username(username)
        if user:
            # Convert User object to dict for compatibility
            return {
                'id': user.id,
                'username': user.username,
                'password_hash': user.password_hash,
                'salt': getattr(user, 'salt', ''),  # For legacy users
                'is_admin': user.is_admin,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else '',
                'updated_at': getattr(user, 'updated_at', None),
                'last_login': getattr(user, 'last_login', None),
                'native_language': getattr(user, 'native_language', 'en'),
                'target_language': getattr(user, 'target_language', 'de')
            }
        return None