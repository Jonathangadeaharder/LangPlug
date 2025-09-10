"""
Simple and clean authentication service for LangPlug
No complex dependencies, no fancy logging, just works
"""

import secrets
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from passlib.context import CryptContext

@dataclass
class AuthUser:
    """Represents an authenticated user"""
    id: int
    username: str
    is_admin: bool = False
    is_active: bool = True
    created_at: str = ""
    last_login: Optional[str] = None
    native_language: str = "en"
    target_language: str = "de"

@dataclass
class AuthSession:
    """Represents a user session"""
    session_token: str
    user: AuthUser
    expires_at: datetime
    created_at: datetime

class AuthenticationError(Exception):
    """Base exception for authentication errors"""
    pass

class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid"""
    pass

class UserAlreadyExistsError(AuthenticationError):
    """Raised when trying to register a user that already exists"""
    pass

class SessionExpiredError(AuthenticationError):
    """Raised when a session token has expired"""
    pass

class AuthService:
    """
    Simple authentication service with secure bcrypt password hashing
    """
    
    def __init__(self, db_manager, session_lifetime_hours: int = 24):
        self.db = db_manager
        self.session_lifetime_hours = session_lifetime_hours
        # In-memory session storage for fast access
        self.sessions: Dict[str, Dict[str, Any]] = {}
        # Initialize password context with bcrypt
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
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
        
        # Check if user exists
        existing_user = self._get_user_by_username(username)
        if existing_user:
            raise UserAlreadyExistsError(f"User '{username}' already exists")
        
        # Create user with hashed password (bcrypt includes salt internally)
        password_hash = self._hash_password(password)
        
        try:
            now = datetime.now().isoformat()
            user_id = self.db.execute_insert("""
                INSERT INTO users (username, password_hash, salt, is_admin, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (username, password_hash, "", False, True, now, now))  # Empty salt field for bcrypt
            
            return AuthUser(
                id=user_id,
                username=username,
                is_admin=False,
                is_active=True,
                created_at=now,
                native_language="en",
                target_language="de"
            )
            
        except Exception as e:
            raise AuthenticationError(f"Failed to register user: {e}")
    
    def login(self, username: str, password: str) -> AuthSession:
        """Login user and create session"""
        # Get user from database
        user_data = self._get_user_by_username(username)
        if not user_data:
            raise InvalidCredentialsError("Invalid username or password")
        
        # Check if user needs password migration (from SHA256 to bcrypt)
        needs_migration = user_data.get('needs_password_migration', False)
        
        if needs_migration and user_data.get('salt'):
            # Old SHA256 verification for legacy users
            old_hash = hashlib.sha256(f"{password}{user_data['salt']}".encode()).hexdigest()
            if user_data['password_hash'] != old_hash:
                raise InvalidCredentialsError("Invalid username or password")
            
            # Migrate to bcrypt on successful login
            new_hash = self._hash_password(password)
            now = datetime.now().isoformat()
            self.db.execute_update("""
                UPDATE users 
                SET password_hash = ?, salt = '', needs_password_migration = 0, updated_at = ?
                WHERE id = ?
            """, (new_hash, now, user_data['id']))
            
        else:
            # Verify password using bcrypt for new/migrated users
            if not self._verify_password(password, user_data['password_hash']):
                raise InvalidCredentialsError("Invalid username or password")
        
        # Create session
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=self.session_lifetime_hours)
        
        # Store session in memory
        self.sessions[session_token] = {
            'user_data': user_data,
            'expires_at': expires_at,
            'created_at': datetime.now()
        }
        
        # Update last login
        now = datetime.now().isoformat()
        self.db.execute_update("""
            UPDATE users SET last_login = ?, updated_at = ? WHERE id = ?
        """, (now, now, user_data['id']))
        
        # Create user object
        user = AuthUser(
            id=user_data['id'],
            username=user_data['username'],
            is_admin=bool(user_data.get('is_admin', False)),
            is_active=bool(user_data.get('is_active', True)),
            created_at=user_data.get('created_at', ''),
            last_login=now,
            native_language=user_data.get('native_language', 'en'),
            target_language=user_data.get('target_language', 'de')
        )
        
        return AuthSession(
            session_token=session_token,
            user=user,
            expires_at=expires_at,
            created_at=datetime.now()
        )
    
    def validate_session(self, session_token: str) -> AuthUser:
        """Validate session token and return user"""
        session_data = self.sessions.get(session_token)
        if not session_data:
            raise SessionExpiredError("Invalid or expired session")
        
        # Check expiry
        if datetime.now() > session_data['expires_at']:
            del self.sessions[session_token]
            raise SessionExpiredError("Session has expired")
        
        user_data = session_data['user_data']
        return AuthUser(
            id=user_data['id'],
            username=user_data['username'],
            is_admin=bool(user_data.get('is_admin', False)),
            is_active=bool(user_data.get('is_active', True)),
            created_at=user_data.get('created_at', ''),
            last_login=user_data.get('last_login'),
            native_language=user_data.get('native_language', 'en'),
            target_language=user_data.get('target_language', 'de')
        )
    
    def logout(self, session_token: str) -> bool:
        """Logout user by removing session"""
        if session_token in self.sessions:
            del self.sessions[session_token]
            return True
        return False
    
    def update_language_preferences(self, user_id: int, native_language: str, target_language: str) -> bool:
        """Update user's language preferences"""
        try:
            now = datetime.now().isoformat()
            self.db.execute_update("""
                UPDATE users 
                SET native_language = ?, target_language = ?, updated_at = ?
                WHERE id = ?
            """, (native_language, target_language, now, user_id))
            
            # Update any cached sessions
            for token, session_data in self.sessions.items():
                if session_data['user_data']['id'] == user_id:
                    session_data['user_data']['native_language'] = native_language
                    session_data['user_data']['target_language'] = target_language
            
            return True
        except Exception as e:
            raise AuthenticationError(f"Failed to update language preferences: {e}")
    
    def _get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user from database by username"""
        results = self.db.execute_query("""
            SELECT id, username, password_hash, salt, is_admin, is_active, created_at, updated_at, last_login,
                   native_language, target_language, 
                   COALESCE(needs_password_migration, 0) as needs_password_migration
            FROM users WHERE username = ?
        """, (username,))
        
        return dict(results[0]) if results else None