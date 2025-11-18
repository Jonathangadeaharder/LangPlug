"""
Enhanced security configuration for authentication
"""

import logging
import secrets
import string
from datetime import timedelta

from fastapi import Request
from jose import jwt

logger = logging.getLogger(__name__)


class SecurityConfig:
    """Enhanced security configuration"""

    # JWT Configuration
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Reduced from 24 hours
    JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7

    # Password Policy
    MIN_PASSWORD_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL = True

    # Rate Limiting
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15

    # Session Security
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "strict"

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a cryptographically secure random token"""
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    @staticmethod
    def _check_length(password: str) -> tuple[bool, str]:
        """Check password length requirement"""
        if len(password) < SecurityConfig.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {SecurityConfig.MIN_PASSWORD_LENGTH} characters long"
        return True, ""

    @staticmethod
    def _check_uppercase(password: str) -> tuple[bool, str]:
        """Check uppercase letter requirement"""
        if SecurityConfig.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        return True, ""

    @staticmethod
    def _check_lowercase(password: str) -> tuple[bool, str]:
        """Check lowercase letter requirement"""
        if SecurityConfig.REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        return True, ""

    @staticmethod
    def _check_digits(password: str) -> tuple[bool, str]:
        """Check digit requirement"""
        if SecurityConfig.REQUIRE_DIGITS and not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"
        return True, ""

    @staticmethod
    def _check_special_chars(password: str) -> tuple[bool, str]:
        """Check special character requirement"""
        if SecurityConfig.REQUIRE_SPECIAL and not any(c in string.punctuation for c in password):
            return False, "Password must contain at least one special character"
        return True, ""

    @staticmethod
    def _check_common_passwords(password: str) -> tuple[bool, str]:
        """Check against common passwords"""
        common_passwords = ["password", "123456", "password123", "admin", "letmein"]
        if password.lower() in common_passwords:
            return False, "Password is too common. Please choose a stronger password"
        return True, ""

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """
        Validate password meets security requirements (Refactored for lower complexity)

        Returns:
            tuple: (is_valid, error_message)
        """
        checks = [
            SecurityConfig._check_length,
            SecurityConfig._check_uppercase,
            SecurityConfig._check_lowercase,
            SecurityConfig._check_digits,
            SecurityConfig._check_special_chars,
            SecurityConfig._check_common_passwords,
        ]

        for check in checks:
            is_valid, error_msg = check(password)
            if not is_valid:
                return False, error_msg

        return True, ""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password using Argon2 (via fastapi-users pwdlib)

        Argon2 is more secure than bcrypt for modern threats.
        Note: In production, use fastapi-users UserManager for password operations.
        This method is provided for compatibility only.
        """
        from pwdlib import PasswordHash

        password_hash = PasswordHash.recommended()
        return password_hash.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify password using Argon2

        Only Argon2 hashes are supported. Legacy bcrypt hashes must be migrated.
        """
        from pwdlib import PasswordHash

        try:
            password_hash = PasswordHash.recommended()
            return password_hash.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    @staticmethod
    def create_access_token(data: dict, secret_key: str, expires_delta: timedelta | None = None) -> str:
        """
        Create a JWT access token with enhanced security
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=SecurityConfig.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update(
            {
                "exp": expire,
                "iat": datetime.utcnow(),
                "jti": SecurityConfig.generate_secure_token(16),  # JWT ID for revocation
            }
        )

        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=SecurityConfig.JWT_ALGORITHM)
        return encoded_jwt


class SecurityHeaders:
    """Security headers middleware"""

    @staticmethod
    def get_security_headers() -> dict:
        """Get recommended security headers"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }

    @staticmethod
    async def add_security_headers(request: Request, call_next):
        """Add security headers to all responses"""
        response = await call_next(request)
        headers = SecurityHeaders.get_security_headers()
        for header, value in headers.items():
            response.headers[header] = value
        return response


from datetime import datetime


class LoginAttemptTracker:
    """Track login attempts for rate limiting"""

    def __init__(self):
        self._attempts = {}  # {email: [(timestamp, success), ...]}
        self._locked_until = {}  # {email: datetime}

    def is_locked(self, email: str) -> bool:
        """Check if account is locked due to failed attempts"""
        if email in self._locked_until:
            if datetime.utcnow() < self._locked_until[email]:
                return True
            else:
                # Lockout expired
                del self._locked_until[email]
                self._attempts[email] = []
        return False

    def record_attempt(self, email: str, success: bool):
        """Record a login attempt"""
        if email not in self._attempts:
            self._attempts[email] = []

        self._attempts[email].append((datetime.utcnow(), success))

        # Keep only recent attempts (last 15 minutes)
        cutoff = datetime.utcnow() - timedelta(minutes=15)
        self._attempts[email] = [(t, s) for t, s in self._attempts[email] if t > cutoff]

        # Check if we should lock the account
        recent_failures = sum(1 for t, s in self._attempts[email] if not s)
        if recent_failures >= SecurityConfig.MAX_LOGIN_ATTEMPTS:
            self._locked_until[email] = datetime.utcnow() + timedelta(minutes=SecurityConfig.LOCKOUT_DURATION_MINUTES)
            logger.warning(f"Account {email} locked due to {recent_failures} failed login attempts")

    def get_remaining_attempts(self, email: str) -> int:
        """Get number of remaining attempts before lockout"""
        if email not in self._attempts:
            return SecurityConfig.MAX_LOGIN_ATTEMPTS

        recent_failures = sum(1 for t, s in self._attempts[email] if not s)
        return max(0, SecurityConfig.MAX_LOGIN_ATTEMPTS - recent_failures)
