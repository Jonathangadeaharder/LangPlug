"""
Refresh Token Rotation Service

Implements automatic token rotation with family tracking for enhanced security.
Detects token theft by monitoring for reuse of old tokens within a family.

Key Concepts:
    - Token Family: A series of refresh tokens issued from the same login session
    - Rotation: When a refresh token is used, a new one is issued and the old one is invalidated
    - Theft Detection: If an old (already-rotated) token is used, the entire family is revoked

Usage Example:
    ```python
    service = RefreshTokenService(db)

    # Create new token family on login
    token, family_id = await service.create_token_family(user_id=1)

    # Rotate token on refresh
    new_token = await service.rotate_token(old_token)

    # Revoke family on logout
    await service.revoke_family(family_id)
    ```

Security Features:
    - Token hashing (SHA256) - tokens never stored in plaintext
    - Automatic expiration cleanup
    - Token theft detection via reuse monitoring
    - Family-level revocation on security incidents

Thread Safety:
    Yes. All operations are async and use database transactions.

Performance Notes:
    - Token lookup: O(1) via hash index
    - Cleanup operations: Scheduled background job recommended
"""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.config.logging_config import get_logger
from core.database.transaction import transactional
from core.exceptions import AuthenticationError
from database.models import RefreshTokenFamily, User

UTC = UTC
logger = get_logger(__name__)


class RefreshTokenService:
    """
    Service for managing refresh token families with automatic rotation.

    Implements OAuth2 refresh token rotation pattern for enhanced security.
    Each refresh operation generates a new token and invalidates the old one,
    while tracking the family to detect theft attempts.

    Attributes:
        db (AsyncSession): Database session for persistence
        token_lifetime_days (int): Refresh token lifetime (default: 30 days)
    """

    def __init__(self, db: AsyncSession, token_lifetime_days: int = 30):
        self.db = db
        self.token_lifetime_days = token_lifetime_days

    @staticmethod
    def _hash_token(token: str) -> str:
        """
        Hash token using SHA256 for secure storage.

        Args:
            token: Raw refresh token string

        Returns:
            Hexadecimal SHA256 hash of token

        Note:
            Tokens are never stored in plaintext for security.
            Hash is deterministic for lookup but irreversible.
        """
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def _generate_token() -> str:
        """
        Generate cryptographically secure refresh token.

        Returns:
            URL-safe base64 encoded token (43 characters)

        Note:
            Uses secrets module for cryptographic randomness.
            Token has 256 bits of entropy.
        """
        return secrets.token_urlsafe(32)

    @transactional
    async def create_token_family(self, user_id: int) -> tuple[str, str]:
        """
        Create new refresh token family for user login.

        Creates the initial token in a new family. This should be called
        on successful user authentication (login).

        Args:
            user_id: ID of authenticated user

        Returns:
            Tuple of (refresh_token, family_id)

        Raises:
            AuthenticationError: If user not found or database error

        Example:
            ```python
            token, family_id = await service.create_token_family(user_id=1)
            # Store token in httpOnly cookie
            # Store family_id for future revocation (optional)
            ```

        Note:
            Token is returned in plaintext (to send to client) but stored as hash.
            Family ID is stored for tracking and potential manual revocation.
        """
        # Verify user exists
        user = await self.db.get(User, user_id)
        if not user:
            raise AuthenticationError(f"User {user_id} not found")

        # Generate new token and family
        token = self._generate_token()
        token_hash = self._hash_token(token)
        family_id = str(uuid.uuid4())
        expires_at = datetime.now(UTC) + timedelta(days=self.token_lifetime_days)

        # Create family record
        family = RefreshTokenFamily(
            user_id=user_id,
            family_id=family_id,
            token_hash=token_hash,
            generation=0,
            expires_at=expires_at,
            is_revoked=False,
        )

        self.db.add(family)
        await self.db.flush()

        logger.info("Created refresh token family", family_id=family_id, user_id=user_id)
        return token, family_id

    @transactional
    async def rotate_token(self, old_token: str) -> tuple[str, str]:
        """
        Rotate refresh token to new generation within same family.

        Validates old token, creates new token in same family, and invalidates old token.
        If old token was already used (reuse detected), revokes entire family and raises error.

        Args:
            old_token: Current refresh token to rotate

        Returns:
            Tuple of (new_token, new_access_token_user_id)

        Raises:
            AuthenticationError: If token invalid, expired, revoked, or reused

        Example:
            ```python
            try:
                new_token, user_id = await service.rotate_token(old_token)
                # Issue new access token for user_id
                # Send new_token in httpOnly cookie
            except AuthenticationError as e:
                # Token invalid or family compromised
                # Require re-login
            ```

        Security:
            If token reuse is detected (old token used twice), this indicates potential
            token theft. The entire family is immediately revoked and error is raised.
        """
        token_hash = self._hash_token(old_token)

        # Find token family
        stmt = select(RefreshTokenFamily).where(RefreshTokenFamily.token_hash == token_hash)
        result = await self.db.execute(stmt)
        family = result.scalar_one_or_none()

        if not family:
            raise AuthenticationError("Invalid refresh token")

        # Check if token is expired
        if datetime.now(UTC) > family.expires_at:
            raise AuthenticationError("Refresh token expired")

        # Check if family is revoked
        if family.is_revoked:
            raise AuthenticationError(f"Refresh token family revoked: {family.revoked_reason or 'security_incident'}")

        # Check for token reuse (indicates theft)
        if family.last_used_at is not None:
            logger.warning(
                "Token reuse detected, revoking family", family_id=family.family_id, generation=family.generation
            )

            # Revoke entire family
            await self._revoke_family_internal(family.family_id, reason="token_reuse_detected")

            raise AuthenticationError("Token reuse detected. All tokens in this family have been revoked for security.")

        # Mark old token as used
        family.last_used_at = datetime.now(UTC)

        # Generate new token in same family
        new_token = self._generate_token()
        new_token_hash = self._hash_token(new_token)
        new_generation = family.generation + 1
        expires_at = datetime.now(UTC) + timedelta(days=self.token_lifetime_days)

        # Create new family record
        new_family = RefreshTokenFamily(
            user_id=family.user_id,
            family_id=family.family_id,
            token_hash=new_token_hash,
            generation=new_generation,
            expires_at=expires_at,
            is_revoked=False,
        )

        self.db.add(new_family)
        await self.db.flush()

        logger.info(
            "Rotated token family", family_id=family.family_id, old_gen=family.generation, new_gen=new_generation
        )

        return new_token, family.user_id

    async def verify_token(self, token: str) -> int | None:
        """
        Verify refresh token and return user ID without rotation.

        Validates token exists, is not expired, and family not revoked.
        Does NOT rotate the token - use rotate_token() for that.

        Args:
            token: Refresh token to verify

        Returns:
            User ID if valid, None if invalid

        Note:
            This is for verification only. For actual refresh operations,
            use rotate_token() which also rotates the token.
        """
        token_hash = self._hash_token(token)

        stmt = select(RefreshTokenFamily).where(RefreshTokenFamily.token_hash == token_hash)
        result = await self.db.execute(stmt)
        family = result.scalar_one_or_none()

        if not family:
            return None

        # Check expiration and revocation
        if datetime.now(UTC) > family.expires_at or family.is_revoked:
            return None

        return family.user_id

    async def _revoke_family_internal(self, family_id: str, reason: str):
        """
        Internal method to revoke entire token family.

        Marks all tokens in family as revoked. Used for theft detection
        and manual revocation.

        Args:
            family_id: UUID of token family to revoke
            reason: Reason for revocation (e.g., "token_reuse_detected")

        Note:
            This method does NOT commit the transaction. Call from within
            a transactional context.
        """
        stmt = (
            update(RefreshTokenFamily)
            .where(RefreshTokenFamily.family_id == family_id)
            .values(
                is_revoked=True,
                revoked_at=datetime.now(UTC),
                revoked_reason=reason,
            )
        )
        await self.db.execute(stmt)

    @transactional
    async def revoke_family(self, family_id: str, reason: str = "manual_revocation"):
        """
        Manually revoke token family (e.g., on logout).

        Revokes all tokens in the specified family. This should be called
        when user explicitly logs out or security incident detected.

        Args:
            family_id: UUID of token family to revoke
            reason: Reason for revocation (default: "manual_revocation")

        Raises:
            AuthenticationError: If family not found

        Example:
            ```python
            # On logout
            await service.revoke_family(family_id, reason="user_logout")

            # On security incident
            await service.revoke_family(family_id, reason="password_changed")
            ```
        """
        # Verify family exists
        stmt = select(RefreshTokenFamily).where(RefreshTokenFamily.family_id == family_id)
        result = await self.db.execute(stmt)
        family = result.scalar_one_or_none()

        if not family:
            raise AuthenticationError(f"Token family {family_id} not found")

        await self._revoke_family_internal(family_id, reason)
        await self.db.flush()

        logger.info("Revoked token family", family_id=family_id, reason=reason)

    @transactional
    async def revoke_all_user_tokens(self, user_id: int, reason: str = "revoke_all_sessions"):
        """
        Revoke all refresh token families for a user.

        Logs user out of all devices/sessions. Use for security incidents
        like password changes, account compromise, etc.

        Args:
            user_id: User ID whose tokens to revoke
            reason: Reason for revocation (default: "revoke_all_sessions")

        Example:
            ```python
            # On password change
            await service.revoke_all_user_tokens(
                user_id=1,
                reason="password_changed"
            )
            ```
        """
        stmt = (
            update(RefreshTokenFamily)
            .where(RefreshTokenFamily.user_id == user_id)
            .where(not RefreshTokenFamily.is_revoked)
            .values(
                is_revoked=True,
                revoked_at=datetime.now(UTC),
                revoked_reason=reason,
            )
        )
        result = await self.db.execute(stmt)
        count = result.rowcount
        await self.db.flush()

        logger.info("Revoked token families", count=count, user_id=user_id, reason=reason)

    @transactional
    async def cleanup_expired_tokens(self):
        """
        Remove expired refresh token records from database.

        Should be run periodically as background job to prevent
        database bloat. Removes tokens expired for more than 7 days.

        Example:
            ```python
            # In background scheduler
            async def cleanup_job():
                async with get_db_session() as db:
                    service = RefreshTokenService(db)
                    await service.cleanup_expired_tokens()
            ```

        Note:
            Only removes tokens expired for grace period (7 days) to allow
            for investigation of security incidents.
        """
        grace_period = datetime.now(UTC) - timedelta(days=7)

        stmt = select(RefreshTokenFamily).where(RefreshTokenFamily.expires_at < grace_period)
        result = await self.db.execute(stmt)
        expired_families = result.scalars().all()

        for family in expired_families:
            await self.db.delete(family)

        count = len(expired_families)
        await self.db.flush()

        logger.info("Cleaned up expired refresh tokens", count=count)
