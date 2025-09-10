"""
Unit tests for Authentication Service
Tests user authentication, session management, and security features
"""
import pytest
from unittest.mock import patch
from services.authservice.auth_service import AuthService, AuthUser, SessionExpiredError


class TestAuthService:
    """Test cases for AuthService"""

    @pytest.fixture
    def auth_service(self, temp_db):
        """Create authentication service with temp database"""
        return AuthService(temp_db)

    def test_initialization(self, auth_service):
        """Test service initialization"""
        assert auth_service is not None
        assert hasattr(auth_service, 'db_manager')

    def test_create_user_success(self, auth_service):
        """Test successful user creation"""
        username = "testuser"
        password = "securepassword123"
        email = "test@example.com"
        
        user = auth_service.create_user(username, email, password)
        
        assert isinstance(user, AuthUser)
        assert user.username == username
        assert user.email == email
        assert user.user_id is not None

    def test_create_user_duplicate_username(self, auth_service):
        """Test creating user with duplicate username fails"""
        username = "testuser"
        password = "securepassword123"
        email = "test@example.com"
        
        # Create first user
        auth_service.create_user(username, email, password)
        
        # Attempt to create second user with same username
        with pytest.raises(ValueError, match="already exists"):
            auth_service.create_user(username, "other@example.com", password)

    def test_authenticate_valid_credentials(self, auth_service):
        """Test authentication with valid credentials"""
        username = "testuser"
        password = "securepassword123"
        email = "test@example.com"
        
        # Create user
        auth_service.create_user(username, email, password)
        
        # Authenticate
        user = auth_service.authenticate(username, password)
        
        assert isinstance(user, AuthUser)
        assert user.username == username

    def test_authenticate_invalid_username(self, auth_service):
        """Test authentication with invalid username"""
        with pytest.raises(ValueError, match="Invalid credentials"):
            auth_service.authenticate("nonexistent", "password")

    def test_authenticate_invalid_password(self, auth_service):
        """Test authentication with invalid password"""
        username = "testuser"
        password = "securepassword123"
        email = "test@example.com"
        
        # Create user
        auth_service.create_user(username, email, password)
        
        # Try with wrong password
        with pytest.raises(ValueError, match="Invalid credentials"):
            auth_service.authenticate(username, "wrongpassword")

    def test_create_session(self, auth_service):
        """Test session creation"""
        username = "testuser"
        password = "securepassword123"
        email = "test@example.com"
        
        # Create and authenticate user
        user = auth_service.create_user(username, email, password)
        
        # Create session
        session_id, token = auth_service.create_session(user.user_id)
        
        assert session_id is not None
        assert token is not None
        assert len(token) > 20  # Should be a substantial token

    def test_verify_valid_token(self, auth_service):
        """Test verifying valid token"""
        username = "testuser"
        password = "securepassword123"
        email = "test@example.com"
        
        # Create user and session
        user = auth_service.create_user(username, email, password)
        session_id, token = auth_service.create_session(user.user_id)
        
        # Verify token
        token_data = auth_service.verify_token(token)
        
        assert token_data is not None
        assert "user_id" in token_data
        assert token_data["user_id"] == user.user_id

    def test_verify_invalid_token(self, auth_service):
        """Test verifying invalid token"""
        with pytest.raises(ValueError, match="Invalid or expired token"):
            auth_service.verify_token("invalid_token")

    def test_session_expiration(self, auth_service):
        """Test session expiration handling"""
        username = "testuser"
        password = "securepassword123"
        email = "test@example.com"
        
        # Create user and session
        user = auth_service.create_user(username, email, password)
        session_id, token = auth_service.create_session(user.user_id)
        
        # Mock expired session in database
        with patch.object(auth_service, '_is_session_expired', return_value=True):
            with pytest.raises(SessionExpiredError):
                auth_service.verify_token(token)

    def test_revoke_session(self, auth_service):
        """Test session revocation"""
        username = "testuser"
        password = "securepassword123"
        email = "test@example.com"
        
        # Create user and session
        user = auth_service.create_user(username, email, password)
        session_id, token = auth_service.create_session(user.user_id)
        
        # Verify token works initially
        token_data = auth_service.verify_token(token)
        assert token_data is not None
        
        # Revoke session
        auth_service.revoke_session(session_id)
        
        # Verify token no longer works
        with pytest.raises(ValueError, match="Invalid or expired token"):
            auth_service.verify_token(token)

    def test_password_security(self, auth_service):
        """Test password hashing and security"""
        username = "testuser"
        password = "securepassword123"
        email = "test@example.com"
        
        # Create user
        user = auth_service.create_user(username, email, password)
        
        # Verify password is not stored in plain text
        # This assumes we can access the database directly for verification
        with auth_service.db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT password_hash FROM users WHERE user_id = ?", 
                (user.user_id,)
            )
            stored_hash = cursor.fetchone()
            
            # Password should be hashed, not plain text
            assert stored_hash is not None
            assert stored_hash[0] != password
            assert len(stored_hash[0]) > 50  # Hash should be substantial

    def test_multiple_sessions_per_user(self, auth_service):
        """Test that users can have multiple active sessions"""
        username = "testuser"
        password = "securepassword123"
        email = "test@example.com"
        
        # Create user
        user = auth_service.create_user(username, email, password)
        
        # Create multiple sessions
        session1_id, token1 = auth_service.create_session(user.user_id)
        session2_id, token2 = auth_service.create_session(user.user_id)
        
        # Both tokens should be valid
        token1_data = auth_service.verify_token(token1)
        token2_data = auth_service.verify_token(token2)
        
        assert token1_data["user_id"] == user.user_id
        assert token2_data["user_id"] == user.user_id
        assert session1_id != session2_id

    def test_user_data_privacy(self, auth_service):
        """Test that sensitive user data is properly handled"""
        username = "testuser"
        password = "securepassword123"
        email = "test@example.com"
        
        # Create user
        user = auth_service.create_user(username, email, password)
        
        # Verify AuthUser object doesn't contain password
        user_dict = user.__dict__
        assert "password" not in user_dict
        assert "password_hash" not in user_dict

    def test_concurrent_authentication(self, auth_service):
        """Test concurrent authentication attempts"""
        import threading
        username = "testuser"
        password = "securepassword123"
        email = "test@example.com"
        
        # Create user
        auth_service.create_user(username, email, password)
        
        results = []
        
        def authenticate_user():
            try:
                user = auth_service.authenticate(username, password)
                results.append(("success", user.user_id))
            except Exception as e:
                results.append(("error", str(e)))
        
        # Run multiple authentication attempts concurrently
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=authenticate_user)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All should succeed
        successes = [r for r in results if r[0] == "success"]
        assert len(successes) == 5