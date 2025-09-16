"""
User Repository Implementation
Standardizes user data access patterns and removes direct database queries from services
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class User:
    """User domain model"""
    def __init__(self, id: Optional[int] = None, username: str = "", 
                 hashed_password: str = "", email: str = "", 
                 native_language: str = "en", target_language: str = "de",
                 created_at: Optional[datetime] = None):
        self.id = id
        self.username = username
        self.hashed_password = hashed_password
        self.email = email
        self.native_language = native_language
        self.target_language = target_language
        self.created_at = created_at or datetime.now()


class UserRepository(BaseRepository[User]):
    """Repository for User entity with standardized database access"""
    
    @property
    def table_name(self) -> str:
        return "users"
    
    def _row_to_model(self, row: Dict[str, Any]) -> User:
        """Convert database row to User model"""
        return User(
            id=row.get('id'),
            username=row.get('username', ''),
            hashed_password=row.get('hashed_password', ''),
            email=row.get('email', ''),
            native_language=row.get('native_language', 'en'),
            target_language=row.get('target_language', 'de'),
            created_at=datetime.fromisoformat(row['created_at']) if row.get('created_at') else datetime.now()
        )
    
    def _model_to_dict(self, user: User) -> Dict[str, Any]:
        """Convert User model to dictionary for database operations"""
        return {
            'id': user.id,
            'username': user.username,
            'hashed_password': user.hashed_password,
            'email': user.email,
            'native_language': user.native_language,
            'target_language': user.target_language,
            'created_at': user.created_at.isoformat() if user.created_at else datetime.now().isoformat()
        }
    
    def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_model(dict(row))
                return None
        except Exception as e:
            self.logger.error(f"Error finding user by username {username}: {e}")
            raise
    
    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_model(dict(row))
                return None
        except Exception as e:
            self.logger.error(f"Error finding user by email {email}: {e}")
            raise
    
    def create(self, user: User) -> int:
        """Create a new user and return the user ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (username, password_hash, salt, is_admin, is_active, created_at, updated_at, native_language, target_language)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user.username,
                    user.password_hash,
                    "",  # Empty salt for bcrypt
                    user.is_admin or False,
                    user.is_active or True,
                    user.created_at.isoformat() if user.created_at else datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    getattr(user, 'native_language', 'en'),
                    getattr(user, 'target_language', 'de')
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            self.logger.error(f"Error creating user {user.username}: {e}")
            raise

    def username_exists(self, username: str, exclude_id: Optional[int] = None) -> bool:
        """Check if username already exists (optionally excluding a specific user ID)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if exclude_id:
                    cursor.execute("SELECT COUNT(*) FROM users WHERE username = ? AND id != ?", (username, exclude_id))
                else:
                    cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
                
                return cursor.fetchone()[0] > 0
        except Exception as e:
            self.logger.error(f"Error checking username exists {username}: {e}")
            raise
    
    def email_exists(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """Check if email already exists (optionally excluding a specific user ID)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if exclude_id:
                    cursor.execute("SELECT COUNT(*) FROM users WHERE email = ? AND id != ?", (email, exclude_id))
                else:
                    cursor.execute("SELECT COUNT(*) FROM users WHERE email = ?", (email,))
                
                return cursor.fetchone()[0] > 0
        except Exception as e:
            self.logger.error(f"Error checking email exists {email}: {e}")
            raise
    
    def update_language_preference(self, user_id: int, native_language: str, target_language: str) -> bool:
        """Update user language preferences"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users 
                    SET native_language = ?, target_language = ?, updated_at = ?
                    WHERE id = ?
                """, (native_language, target_language, datetime.now().isoformat(), user_id))
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Error updating language preferences for user {user_id}: {e}")
            raise
    
    def update_password(self, user_id: int, password_hash: str) -> bool:
        """Update user password hash"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET password_hash = ? WHERE id = ?",
                    (password_hash, user_id)
                )
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Error updating password for user {user_id}: {e}")
            raise
    
    def deactivate_session(self, session_token: str) -> bool:
        """Deactivate a user session"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE user_sessions SET is_active = 0 WHERE session_token = ?
                """, (session_token,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Error deactivating session {session_token}: {e}")
            raise

    # Legacy create_from_data method removed - use FastAPI-Users for user creation
    
    def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users 
                    SET last_login = ?, updated_at = ? 
                    WHERE id = ?
                """, (datetime.now().isoformat(), datetime.now().isoformat(), user_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Error updating last login for user {user_id}: {e}")
            raise
    
    def update_password_hash(self, user_id: int, password_hash: str) -> bool:
        """Update user's password hash"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users 
                    SET password_hash = ?, salt = '', updated_at = ? 
                    WHERE id = ?
                """, (password_hash, datetime.now().isoformat(), user_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Error updating password for user {user_id}: {e}")
            raise


    def create_session(self, user_id: int, session_token: str, expires_at: str) -> bool:
        """Create a new user session"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                cursor.execute("""
                    INSERT INTO user_sessions (user_id, session_token, expires_at, created_at, last_used, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, session_token, expires_at, now, now, True))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Error creating session for user {user_id}: {e}")
            raise


    def get_active_session_with_user(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Get active session with user data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT us.session_token, us.expires_at, us.last_used, us.is_active,
                           u.id, u.username, u.is_admin, u.is_active as user_is_active,
                           u.created_at, u.last_login, u.native_language, u.target_language
                    FROM user_sessions us
                    JOIN users u ON us.user_id = u.id
                    WHERE us.session_token = ? AND us.is_active = 1
                """, (session_token,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"Error getting session {session_token}: {e}")
            raise


    def mark_session_inactive(self, session_token: str) -> bool:
        """Mark a session as inactive"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE user_sessions SET is_active = 0 WHERE session_token = ?
                """, (session_token,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Error marking session {session_token} inactive: {e}")
            raise


    def update_session_last_used(self, session_token: str) -> bool:
        """Update session last used timestamp"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                cursor.execute("""
                    UPDATE user_sessions SET last_used = ? WHERE session_token = ?
                """, (now, session_token))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Error updating session {session_token} last used: {e}")
            raise
