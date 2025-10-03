"""
Authentication domain services
"""

from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from core.config import settings
from core.exceptions import AuthenticationError, ValidationError
from database.models import User
from database.repositories.interfaces import UserRepositoryInterface

from .models import TokenResponse, UserCreate, UserLogin, UserResponse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthenticationService:
    """Service for user authentication operations"""

    def __init__(self, user_repository: UserRepositoryInterface):
        self.user_repository = user_repository

    async def register_user(self, db: Session, user_data: UserCreate) -> UserResponse:
        """Register a new user"""
        existing_user = await self.user_repository.get_by_email(db, user_data.email)
        if existing_user:
            raise ValidationError("Email already registered")

        existing_username = await self.user_repository.get_by_username(db, user_data.username)
        if existing_username:
            raise ValidationError("Username already taken")

        hashed_password = self._hash_password(user_data.password)

        user = await self.user_repository.create(
            db,
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False,
        )

        return UserResponse.from_orm(user)

    async def login_user(self, db: Session, login_data: UserLogin) -> TokenResponse:
        """Authenticate user and return token"""
        user = await self.user_repository.get_by_username(db, login_data.username)
        if not user:
            raise AuthenticationError("Invalid credentials")

        if not self._verify_password(login_data.password, user.hashed_password):
            raise AuthenticationError("Invalid credentials")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        await self.user_repository.update_last_login(db, user.id)

        access_token = self._create_access_token({"sub": str(user.id)})

        return TokenResponse(
            access_token=access_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserResponse.from_orm(user),
        )

    async def get_current_user(self, db: Session, token: str) -> User:
        """Get current user from token"""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise AuthenticationError("Invalid token")
        except JWTError as e:
            raise AuthenticationError("Invalid token") from e

        user = await self.user_repository.get_by_id(db, int(user_id))
        if user is None:
            raise AuthenticationError("User not found")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        return user

    async def update_password(self, db: Session, user_id: int, current_password: str, new_password: str) -> bool:
        """Update user password"""
        user = await self.user_repository.get_by_id(db, user_id)
        if not user:
            raise AuthenticationError("User not found")

        if not self._verify_password(current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect")

        hashed_password = self._hash_password(new_password)
        return await self.user_repository.update_password(db, user_id, hashed_password)

    def _hash_password(self, password: str) -> str:
        """Hash password"""
        return pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def _create_access_token(self, data: dict) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
