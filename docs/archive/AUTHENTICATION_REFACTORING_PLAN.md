# Authentication Architecture Refactoring Plan

**Goal**: Transform authentication layer into a production-ready, properly decoupled, best-practice implementation

**Current State**: Dual authentication systems, inconsistent hashing, global state, in-memory storage
**Target State**: Single JWT-based system, proper DI, Redis-backed features, scalable architecture

---

## Phase 1: Critical Infrastructure Fixes (1-2 days)

### 1.1 Eliminate Dual Authentication System ⚠️ CRITICAL

**Problem**: Two complete auth systems running simultaneously
- FastAPI-Users (JWT, modern)
- Custom AuthService (sessions, legacy)

**Decision**: **Keep FastAPI-Users, remove custom AuthService**

**Rationale**:
- FastAPI-Users is industry-standard, well-maintained
- JWT is stateless and scalable
- Community support and security updates
- Modern OAuth2/OIDC patterns

**Actions**:
```markdown
[ ] 1. Audit all imports of `services.authservice.auth_service`
[ ] 2. Identify dependencies on custom AuthService
[ ] 3. Migrate functionality to FastAPI-Users hooks
[ ] 4. Update all endpoints to use FastAPI-Users exclusively
[ ] 5. Delete `services/authservice/auth_service.py`
[ ] 6. Delete `services/authservice/models.py` (AuthSession, AuthUser)
[ ] 7. Update tests to use FastAPI-Users patterns
```

**Migration Path**:
```python
# OLD: Custom AuthService
from services.authservice.auth_service import AuthService
auth_service = AuthService(db)
session = await auth_service.login(username, password)

# NEW: FastAPI-Users
from core.auth import fastapi_users, auth_backend
# Login handled by fastapi_users.get_auth_router(auth_backend)
# Current user via: Depends(current_active_user)
```

---

### 1.2 Fix Password Hashing Inconsistency ⚠️ SECURITY

**Problem**: Two hashing algorithms in use
- `core/auth_security.py`: bcrypt (12 rounds)
- `services/authservice/password_validator.py`: argon2

**Decision**: **Use Argon2 everywhere**

**Rationale**:
- Argon2 won the Password Hashing Competition (2015)
- Memory-hard (resists GPU/ASIC attacks)
- Recommended by OWASP
- Better than bcrypt for modern threats

**Actions**:
```markdown
[ ] 1. Update core/auth_security.py to use argon2
[ ] 2. Update core/auth.py password hashing to use PasswordValidator
[ ] 3. Remove bcrypt CryptContext from auth_security.py
[ ] 4. Create migration script for existing bcrypt hashes
[ ] 5. Add password rehashing on next login (transparent upgrade)
[ ] 6. Validate all password operations use single source of truth
```

**Implementation**:
```python
# core/auth_security.py - REPLACE bcrypt context
from services.authservice.password_validator import PasswordValidator

class SecurityConfig:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash using Argon2 (delegates to PasswordValidator)"""
        return PasswordValidator.hash_password(password)

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        """Verify using Argon2 with fallback to bcrypt for migration"""
        # Try Argon2 first
        if PasswordValidator.verify_password(plain, hashed):
            return True
        # Fallback to bcrypt for legacy hashes
        if hashed.startswith('$2b$'):
            from passlib.context import CryptContext
            bcrypt_ctx = CryptContext(schemes=["bcrypt"])
            return bcrypt_ctx.verify(plain, hashed)
        return False
```

---

### 1.3 Replace Global Singletons with Dependency Injection ⚠️ CRITICAL

**Problem**: Global state prevents testing, violates DI principles
- `token_blacklist = TokenBlacklist()` (core/token_blacklist.py:140)
- `login_tracker = LoginAttemptTracker()` (core/auth_security.py:233)

**Actions**:
```markdown
[ ] 1. Convert TokenBlacklist to FastAPI dependency
[ ] 2. Convert LoginAttemptTracker to FastAPI dependency
[ ] 3. Add proper lifecycle management (startup/shutdown)
[ ] 4. Update all consumers to use Depends()
[ ] 5. Add dependency override support for testing
```

**Implementation**:
```python
# core/dependencies.py (NEW FILE)
from fastapi import Depends, Request
from core.token_blacklist import TokenBlacklist
from core.auth_security import LoginAttemptTracker

def get_token_blacklist() -> TokenBlacklist:
    """Get token blacklist service (singleton per app lifecycle)"""
    if not hasattr(get_token_blacklist, "_instance"):
        get_token_blacklist._instance = TokenBlacklist()
    return get_token_blacklist._instance

def get_login_tracker() -> LoginAttemptTracker:
    """Get login attempt tracker (singleton per app lifecycle)"""
    if not hasattr(get_login_tracker, "_instance"):
        get_login_tracker._instance = LoginAttemptTracker()
    return get_login_tracker._instance

# Usage in endpoints
@router.post("/logout")
async def logout(
    token: str,
    blacklist: TokenBlacklist = Depends(get_token_blacklist)
):
    await blacklist.add_token(token)
```

---

## Phase 2: Storage & Scalability (2-3 days)

### 2.1 Replace In-Memory Storage with Redis ⚠️ PRODUCTION BLOCKER

**Problem**:
- In-memory sessions lost on restart
- Won't scale horizontally
- TokenBlacklist falls back to memory silently

**Actions**:
```markdown
[ ] 1. Make Redis required (not optional)
[ ] 2. Remove in-memory fallback from TokenBlacklist
[ ] 3. Fail fast if Redis unavailable at startup
[ ] 4. Implement Redis connection pooling
[ ] 5. Add health checks for Redis connectivity
[ ] 6. Add Redis reconnection logic with exponential backoff
[ ] 7. Update docker-compose with Redis service
```

**Implementation**:
```python
# core/redis_client.py (NEW FILE)
import redis.asyncio as redis
from core.config import settings

class RedisClient:
    """Redis client with connection pooling"""

    def __init__(self):
        self._pool = None
        self._client = None

    async def connect(self):
        """Connect to Redis on startup"""
        self._pool = redis.ConnectionPool(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            decode_responses=True,
            max_connections=50,
        )
        self._client = redis.Redis(connection_pool=self._pool)

        # Fail fast if Redis unavailable
        try:
            await self._client.ping()
        except Exception as e:
            raise RuntimeError(f"Redis connection failed: {e}") from e

    async def disconnect(self):
        """Disconnect from Redis on shutdown"""
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()

    def get_client(self) -> redis.Redis:
        """Get Redis client"""
        if not self._client:
            raise RuntimeError("Redis not connected")
        return self._client

# Singleton instance
redis_client = RedisClient()

# Dependency
def get_redis() -> redis.Redis:
    return redis_client.get_client()

# Startup/shutdown
@app.on_event("startup")
async def startup():
    await redis_client.connect()

@app.on_event("shutdown")
async def shutdown():
    await redis_client.disconnect()
```

**Update TokenBlacklist**:
```python
# core/token_blacklist.py - REFACTORED
class TokenBlacklist:
    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client
        # Remove _memory_blacklist and _memory_expiry

    async def add_token(self, token: str, expires_at: datetime) -> bool:
        """Add token to Redis blacklist"""
        ttl = int((expires_at - datetime.now(UTC)).total_seconds())
        if ttl <= 0:
            return False
        await self._redis.setex(f"blacklist:{token}", ttl, "1")
        return True

    async def is_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted in Redis"""
        return bool(await self._redis.exists(f"blacklist:{token}"))

# Dependency
def get_token_blacklist(redis: redis.Redis = Depends(get_redis)) -> TokenBlacklist:
    return TokenBlacklist(redis)
```

---

### 2.2 Implement Distributed Rate Limiting

**Problem**: In-memory rate limiter won't work across multiple instances

**Actions**:
```markdown
[ ] 1. Move rate limiting to Redis
[ ] 2. Use Redis sorted sets for sliding window
[ ] 3. Update RateLimitMiddleware to use Redis
[ ] 4. Add per-user and per-IP rate limits
[ ] 5. Implement different limits for different endpoints
```

**Implementation**:
```python
# core/rate_limiter.py (NEW FILE)
import time
from redis.asyncio import Redis

class RedisRateLimiter:
    """Redis-backed rate limiter with sliding window"""

    def __init__(self, redis: Redis):
        self._redis = redis

    async def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int]:
        """
        Check if request is allowed

        Returns: (is_allowed, remaining_requests)
        """
        now = time.time()
        window_start = now - window_seconds

        # Pipeline for atomic operations
        pipe = self._redis.pipeline()

        # Remove old requests
        pipe.zremrangebyscore(f"ratelimit:{key}", 0, window_start)

        # Count requests in window
        pipe.zcard(f"ratelimit:{key}")

        # Add current request
        pipe.zadd(f"ratelimit:{key}", {str(now): now})

        # Set expiry
        pipe.expire(f"ratelimit:{key}", window_seconds + 1)

        results = await pipe.execute()
        current_count = results[1]

        is_allowed = current_count < max_requests
        remaining = max(0, max_requests - current_count - (1 if is_allowed else 0))

        return is_allowed, remaining

# Usage in middleware
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis: Redis):
        super().__init__(app)
        self._limiter = RedisRateLimiter(redis)

    async def dispatch(self, request: Request, call_next):
        client_id = self._get_client_id(request)

        is_allowed, remaining = await self._limiter.is_allowed(
            key=client_id,
            max_requests=300,
            window_seconds=60
        )

        if not is_allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
```

---

## Phase 3: Architecture Cleanup (2 days)

### 3.1 Eliminate Circular Imports & Improve Module Structure

**Problem**: Complex import dependencies, circular imports

**Actions**:
```markdown
[ ] 1. Create clear module hierarchy
[ ] 2. Move shared types to core/types.py
[ ] 3. Use forward references where needed
[ ] 4. Split large files (auth.py, auth_security.py)
[ ] 5. Document import rules in architecture doc
```

**New Structure**:
```
core/
  auth/
    __init__.py          # Public API
    config.py            # Auth configuration
    dependencies.py      # FastAPI dependencies
    schemas.py           # Pydantic models
    users.py             # FastAPI-Users setup
    password.py          # Password validation
    tokens.py            # JWT operations (move from services)

  security/
    __init__.py
    headers.py           # Security headers middleware
    rate_limiter.py      # Rate limiting

  storage/
    __init__.py
    redis_client.py      # Redis connection
    token_blacklist.py   # Token revocation

services/
  authservice/          # DELETE (functionality moved to core/auth)
```

---

### 3.2 Consolidate Configuration

**Problem**: Auth config scattered across multiple files

**Actions**:
```markdown
[ ] 1. Create single source of truth for auth config
[ ] 2. Move all auth settings to core/config.py
[ ] 3. Validate config on startup
[ ] 4. Add config validation tests
[ ] 5. Document all settings with examples
```

**Implementation**:
```python
# core/config.py - ADD auth section
class Settings(BaseSettings):
    # Existing settings...

    # Authentication
    secret_key: str = Field(..., description="JWT secret key (REQUIRED)")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # Password Policy
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digits: bool = True
    password_require_special: bool = True

    # Rate Limiting
    rate_limit_requests_per_minute: int = 300
    rate_limit_burst_size: int = 60

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str | None = None
    redis_required: bool = True  # Fail if Redis unavailable

    # Security
    session_cookie_secure: bool = True
    session_cookie_httponly: bool = True
    session_cookie_samesite: str = "strict"

    @validator("secret_key")
    def validate_secret_key(cls, v):
        if v == "your-secret-key-here" or len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 chars and not default")
        return v

    @validator("redis_host")
    def validate_redis_required(cls, v, values):
        if values.get("redis_required") and not v:
            raise ValueError("Redis is required but redis_host not configured")
        return v

    class Config:
        env_prefix = "LANGPLUG_"
        env_file = ".env"
```

---

### 3.3 Remove Dead Code & Unused Features

**Actions**:
```markdown
[ ] 1. Remove unused SecurityConfig methods
[ ] 2. Delete unused imports
[ ] 3. Remove commented code
[ ] 4. Consolidate duplicate validation logic
[ ] 5. Remove legacy compatibility code
```

**Files to Clean**:
- `core/auth_security.py` - Massive cleanup needed
- `services/authservice/` - DELETE entire directory
- `api/routes/auth.py` - Simplify, remove custom logic
- `core/auth_dependencies.py` - Merge into core/auth/dependencies.py

---

## Phase 4: Security Enhancements (2-3 days)

### 4.1 Implement Refresh Token Rotation ⚠️ SECURITY

**Problem**: Stolen refresh tokens valid for 30 days

**Actions**:
```markdown
[ ] 1. Implement token rotation on refresh
[ ] 2. Store refresh token family in Redis
[ ] 3. Invalidate all tokens in family if reuse detected
[ ] 4. Add refresh token jti (JWT ID) tracking
[ ] 5. Implement refresh token revocation endpoint
```

**Implementation**:
```python
# core/auth/tokens.py - Enhanced TokenService
class TokenService:
    @classmethod
    def create_refresh_token(cls, user_id: int) -> dict:
        """Create refresh token with family tracking"""
        import uuid

        token_family = str(uuid.uuid4())
        token_id = str(uuid.uuid4())

        payload = {
            "sub": str(user_id),
            "exp": datetime.now(UTC) + timedelta(days=30),
            "iat": datetime.now(UTC),
            "type": "refresh",
            "jti": token_id,
            "family": token_family,
        }

        token = jwt.encode(payload, settings.secret_key, cls.ALGORITHM)

        return {
            "token": token,
            "token_id": token_id,
            "family": token_family
        }

    @classmethod
    async def refresh_access_token(
        cls,
        refresh_token: str,
        redis: Redis
    ) -> dict:
        """Refresh with rotation"""
        payload = cls.decode_token(refresh_token, "refresh")

        user_id = int(payload["sub"])
        token_id = payload["jti"]
        family = payload["family"]

        # Check if token was already used (reuse attack)
        is_used = await redis.get(f"refresh_used:{token_id}")
        if is_used:
            # Revoke entire token family
            await cls._revoke_token_family(family, redis)
            raise AuthenticationError("Token reuse detected - all tokens revoked")

        # Mark token as used
        await redis.setex(f"refresh_used:{token_id}", 60*60*24*30, "1")

        # Create new tokens
        new_access = cls.create_access_token(user_id)
        new_refresh = cls.create_refresh_token(user_id)

        # Store new refresh token in same family
        await redis.setex(
            f"refresh_family:{new_refresh['token_id']}",
            60*60*24*30,
            family
        )

        return {
            "access_token": new_access,
            "refresh_token": new_refresh["token"],
            "token_type": "bearer"
        }

    @classmethod
    async def _revoke_token_family(cls, family: str, redis: Redis):
        """Revoke all tokens in a family"""
        # Get all tokens in family
        keys = []
        async for key in redis.scan_iter(f"refresh_family:*"):
            if await redis.get(key) == family:
                keys.append(key)

        # Mark all as used (revoked)
        if keys:
            pipe = redis.pipeline()
            for key in keys:
                token_id = key.split(":")[-1]
                pipe.setex(f"refresh_used:{token_id}", 60*60*24*30, "1")
            await pipe.execute()
```

---

### 4.2 Add Comprehensive Audit Logging

**Actions**:
```markdown
[ ] 1. Log all authentication events
[ ] 2. Log password changes
[ ] 3. Log failed login attempts
[ ] 4. Log token refresh operations
[ ] 5. Store audit log in database
[ ] 6. Add audit log query endpoints (admin only)
```

**Implementation**:
```python
# database/models.py - ADD
class AuditLog(Base):
    """Security audit log"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    event_type = Column(String(50), nullable=False)  # login, logout, token_refresh, etc.
    success = Column(Boolean, nullable=False)
    ip_address = Column(String(45))  # IPv6 support
    user_agent = Column(String(500))
    details = Column(JSON)  # Additional context

    __table_args__ = (
        Index("idx_audit_timestamp", "timestamp"),
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_event", "event_type"),
    )

# core/auth/audit.py (NEW FILE)
class AuditLogger:
    """Centralized audit logging for auth events"""

    @staticmethod
    async def log_event(
        db: AsyncSession,
        event_type: str,
        success: bool,
        user_id: int | None = None,
        request: Request | None = None,
        details: dict | None = None
    ):
        """Log authentication event"""
        log_entry = AuditLog(
            user_id=user_id,
            event_type=event_type,
            success=success,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
            details=details or {}
        )
        db.add(log_entry)
        await db.flush()

    @staticmethod
    async def log_login_attempt(
        db: AsyncSession,
        username: str,
        success: bool,
        request: Request,
        failure_reason: str | None = None
    ):
        """Log login attempt"""
        await AuditLogger.log_event(
            db=db,
            event_type="login_attempt",
            success=success,
            request=request,
            details={
                "username": username,
                "failure_reason": failure_reason
            }
        )
```

---

### 4.3 Implement MFA Support (Foundation)

**Actions**:
```markdown
[ ] 1. Add mfa_enabled column to User model
[ ] 2. Add mfa_secret column (encrypted)
[ ] 3. Create MFA setup endpoint
[ ] 4. Create MFA verification endpoint
[ ] 5. Add backup codes generation
[ ] 6. Update login flow to check MFA
```

**Implementation**:
```python
# database/models.py - UPDATE User model
class User(Base):
    # Existing columns...

    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(200), nullable=True)  # Encrypted TOTP secret
    mfa_backup_codes = Column(JSON, nullable=True)  # Hashed backup codes

# api/routes/mfa.py (NEW FILE)
from pyotp import TOTP, random_base32

@router.post("/mfa/setup")
async def setup_mfa(
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Setup MFA for user"""
    if current_user.mfa_enabled:
        raise HTTPException(400, "MFA already enabled")

    # Generate secret
    secret = random_base32()

    # Generate QR code URL
    totp = TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="LangPlug"
    )

    # Generate backup codes
    backup_codes = [secrets.token_hex(4) for _ in range(10)]
    hashed_codes = [PasswordValidator.hash_password(code) for code in backup_codes]

    # Store (temporarily) until verified
    await db.execute(
        update(User)
        .where(User.id == current_user.id)
        .values(
            mfa_secret=secret,  # Should be encrypted in production
            mfa_backup_codes=hashed_codes
        )
    )
    await db.commit()

    return {
        "secret": secret,
        "qr_code_url": provisioning_uri,
        "backup_codes": backup_codes  # Show once only
    }

@router.post("/mfa/verify")
async def verify_mfa(
    code: str,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Verify MFA code and enable MFA"""
    if current_user.mfa_enabled:
        raise HTTPException(400, "MFA already enabled")

    if not current_user.mfa_secret:
        raise HTTPException(400, "MFA not set up")

    # Verify TOTP code
    totp = TOTP(current_user.mfa_secret)
    if not totp.verify(code, valid_window=1):
        raise HTTPException(401, "Invalid MFA code")

    # Enable MFA
    await db.execute(
        update(User)
        .where(User.id == current_user.id)
        .values(mfa_enabled=True)
    )
    await db.commit()

    return {"message": "MFA enabled successfully"}
```

---

## Phase 5: Testing & Documentation (2 days)

### 5.1 Comprehensive Test Suite

**Actions**:
```markdown
[ ] 1. Unit tests for all auth functions
[ ] 2. Integration tests for auth flows
[ ] 3. Security tests (token validation, etc.)
[ ] 4. Performance tests (rate limiting under load)
[ ] 5. Penetration testing scenarios
[ ] 6. Test Redis failure scenarios
[ ] 7. Test password migration (bcrypt to argon2)
```

**Test Structure**:
```python
# tests/unit/auth/test_password.py
def test_password_validation_min_length():
    is_valid, msg = PasswordValidator.validate("Short1!")
    assert not is_valid
    assert "12 characters" in msg

def test_password_hashing_argon2():
    password = "SecurePass123!"
    hashed = PasswordValidator.hash_password(password)
    assert hashed.startswith("$argon2")
    assert PasswordValidator.verify_password(password, hashed)

# tests/integration/auth/test_login_flow.py
async def test_complete_login_flow(client, db):
    # Register
    response = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "SecurePass123!"
    })
    assert response.status_code == 201

    # Login
    response = await client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "SecurePass123!"
    })
    assert response.status_code == 200
    tokens = response.json()

    # Access protected resource
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert response.status_code == 200

# tests/security/test_token_security.py
async def test_token_type_substitution_prevented():
    """Ensure refresh token cannot be used as access token"""
    tokens = TokenService.create_token_pair(user_id=1)

    with pytest.raises(AuthenticationError, match="Invalid token type"):
        TokenService.verify_access_token(tokens["refresh_token"])

async def test_refresh_token_reuse_detected(redis):
    """Ensure token reuse is detected and family revoked"""
    tokens = await TokenService.create_token_pair(user_id=1)

    # Use refresh token once
    new_tokens = await TokenService.refresh_access_token(
        tokens["refresh_token"],
        redis
    )

    # Try to reuse same refresh token
    with pytest.raises(AuthenticationError, match="Token reuse detected"):
        await TokenService.refresh_access_token(
            tokens["refresh_token"],
            redis
        )
```

---

### 5.2 Documentation

**Actions**:
```markdown
[ ] 1. Architecture decision records (ADRs)
[ ] 2. API authentication guide
[ ] 3. Security best practices doc
[ ] 4. Deployment guide (Redis setup)
[ ] 5. Migration guide from old auth
[ ] 6. Troubleshooting guide
```

**Documentation Structure**:
```markdown
docs/authentication/
  README.md                    # Overview
  architecture.md              # Architecture decisions
  api-guide.md                 # How to use auth APIs
  security.md                  # Security features
  deployment.md                # Production deployment
  migration.md                 # Migrating from old auth
  troubleshooting.md           # Common issues

  adrs/
    001-fastapi-users.md       # Why FastAPI-Users
    002-argon2-hashing.md      # Why Argon2
    003-redis-required.md      # Why Redis is required
    004-refresh-rotation.md    # Token rotation design
```

---

## Phase 6: Deployment & Monitoring (1 day)

### 6.1 Production Deployment Checklist

```markdown
[ ] 1. Redis deployed and configured
[ ] 2. SECRET_KEY properly set (32+ chars, secure)
[ ] 3. HTTPS enforced
[ ] 4. Secure cookie settings enabled
[ ] 5. Rate limiting configured
[ ] 6. Monitoring alerts configured
[ ] 7. Backup strategy for Redis
[ ] 8. Log aggregation configured
[ ] 9. Health checks configured
[ ] 10. Load testing performed
```

---

### 6.2 Monitoring & Alerting

**Actions**:
```markdown
[ ] 1. Metrics for auth operations
[ ] 2. Alerts for failed login spikes
[ ] 3. Alerts for Redis connectivity
[ ] 4. Dashboard for auth statistics
[ ] 5. Audit log query interface
```

**Implementation**:
```python
# core/metrics.py (NEW FILE)
from prometheus_client import Counter, Histogram

auth_requests_total = Counter(
    "auth_requests_total",
    "Total authentication requests",
    ["endpoint", "status"]
)

auth_duration_seconds = Histogram(
    "auth_duration_seconds",
    "Authentication operation duration",
    ["operation"]
)

failed_login_attempts = Counter(
    "failed_login_attempts_total",
    "Failed login attempts",
    ["reason"]
)

# Usage
@router.post("/login")
async def login(...):
    with auth_duration_seconds.labels("login").time():
        try:
            # ... login logic
            auth_requests_total.labels("login", "success").inc()
        except Exception:
            failed_login_attempts.labels("invalid_credentials").inc()
            raise
```

---

## Success Criteria

### Functional Requirements
- ✅ Single authentication system (FastAPI-Users)
- ✅ Consistent password hashing (Argon2)
- ✅ No global singletons (proper DI)
- ✅ Redis-backed storage (scalable)
- ✅ Refresh token rotation
- ✅ Comprehensive audit logging
- ✅ MFA support foundation

### Non-Functional Requirements
- ✅ 100% test coverage for auth code
- ✅ Load tested to 1000 req/s
- ✅ < 200ms auth endpoint latency (p95)
- ✅ Zero-downtime deployment support
- ✅ Horizontal scaling support
- ✅ Security audit passed

### Code Quality
- ✅ No circular imports
- ✅ Proper dependency injection
- ✅ Clean module boundaries
- ✅ Comprehensive documentation
- ✅ All linting/type checking passes

---

## Timeline Summary

| Phase | Duration | Priority | Blocker |
|-------|----------|----------|---------|
| Phase 1: Critical Fixes | 1-2 days | P0 | Production |
| Phase 2: Storage & Scalability | 2-3 days | P0 | Production |
| Phase 3: Architecture Cleanup | 2 days | P1 | Quality |
| Phase 4: Security Enhancements | 2-3 days | P1 | Security |
| Phase 5: Testing & Docs | 2 days | P1 | Quality |
| Phase 6: Deployment | 1 day | P0 | Production |

**Total**: 10-13 days

---

## Risk Mitigation

### Risk: Breaking existing authentication
**Mitigation**:
- Feature flag for new auth
- Parallel run old + new
- Gradual rollout by user %
- Quick rollback plan

### Risk: Redis dependency
**Mitigation**:
- Redis cluster for HA
- Redis persistence enabled
- Health checks with auto-restart
- Clear error messages if Redis down

### Risk: Password migration fails
**Mitigation**:
- Transparent upgrade on login
- Fallback to bcrypt verification
- Migration monitoring dashboard
- Manual migration script for bulk

### Risk: Token rotation breaks mobile apps
**Mitigation**:
- Feature flag for rotation
- Clear error messages
- Mobile SDK update first
- Backward compatibility period

---

## Post-Refactoring Maintenance

### Weekly
- Review failed auth metrics
- Check Redis performance
- Review audit logs for anomalies

### Monthly
- Security dependency updates
- Performance review
- Capacity planning

### Quarterly
- Security audit
- Penetration testing
- Architecture review

---

## Questions for Stakeholders

1. **Timeline**: Is 2-week timeline acceptable?
2. **Downtime**: Can we have 5-minute maintenance window?
3. **Redis**: Can we deploy Redis cluster?
4. **MFA**: Required now or can wait?
5. **OAuth**: Need Google/GitHub login?
6. **Monitoring**: Have Prometheus/Grafana?
7. **Testing**: Manual QA available?

---

## Final Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                   │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐    ┌──────────────┐   ┌────────────┐ │
│  │ Auth Routes  │───▶│ FastAPI-     │──▶│ Token      │ │
│  │              │    │ Users        │   │ Service    │ │
│  └──────────────┘    └──────────────┘   └────────────┘ │
│         │                    │                  │        │
│         │                    │                  │        │
│         ▼                    ▼                  ▼        │
│  ┌──────────────┐    ┌──────────────┐   ┌────────────┐ │
│  │ Password     │    │ User         │   │ Token      │ │
│  │ Validator    │    │ Manager      │   │ Blacklist  │ │
│  │ (Argon2)     │    │              │   │            │ │
│  └──────────────┘    └──────────────┘   └────────────┘ │
│         │                    │                  │        │
└─────────┼────────────────────┼──────────────────┼────────┘
          │                    │                  │
          ▼                    ▼                  ▼
   ┌──────────────┐    ┌──────────────┐   ┌────────────┐
   │  PostgreSQL  │    │  PostgreSQL  │   │   Redis    │
   │  (Users)     │    │  (Audit Log) │   │  (Tokens)  │
   └──────────────┘    └──────────────┘   └────────────┘
```

**Key Principles**:
- Single source of truth (FastAPI-Users)
- Stateless JWT authentication
- Redis for distributed state
- Proper dependency injection
- Comprehensive audit trail
- Production-ready scalability

---

**Ready to begin Phase 1?**
