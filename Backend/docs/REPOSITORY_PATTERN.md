# Repository Pattern Implementation Guide

## Overview

The Repository Pattern provides a centralized data access layer that abstracts database operations from business logic. This implementation follows the Dependency Inversion Principle: services depend on repository interfaces, not concrete implementations.

## Architecture

```
┌─────────────────┐
│   API Routes    │
└────────┬────────┘
         │ depends on
         ▼
┌─────────────────┐      ┌──────────────────────┐
│   Services      │─────▶│ Repository Interface │
└─────────────────┘      └──────────────────────┘
         │                        △
         │                        │ implements
         │                        │
         │               ┌────────┴──────────┐
         │               │ Concrete Repository│
         │               └────────┬───────────┘
         │                        │
         ▼                        ▼
┌─────────────────────────────────────┐
│       Database (SQLAlchemy)         │
└─────────────────────────────────────┘
```

## Benefits

1. **Testability**: Services can be tested with mock repositories
2. **Separation of Concerns**: Business logic isolated from data access
3. **Flexibility**: Easy to swap implementations (SQL → NoSQL, etc.)
4. **Type Safety**: Interface contracts enforced by type system
5. **Maintainability**: Database logic centralized in one place

## Directory Structure

```
Backend/
├── core/
│   ├── repository_dependencies.py  # DI functions
│   └── dependencies.py              # Re-exports
├── database/
│   └── repositories/
│       ├── interfaces.py            # Repository interfaces
│       ├── base_repository.py       # Base implementation
│       ├── user_repository.py       # Concrete implementations
│       ├── vocabulary_repository.py
│       └── ...
└── services/
    └── authservice/
        └── auth_service.py          # Service using repositories
```

## Using Repositories in Routes

### Before (Direct Database Access)

```python
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_async_session
from database.models import User

router = APIRouter()

@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    return user
```

### After (Repository Pattern)

```python
from fastapi import APIRouter, Depends
from database.repositories.interfaces import UserRepositoryInterface
from core.dependencies import get_user_repository

router = APIRouter()

@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    user_repo: UserRepositoryInterface = Depends(get_user_repository)
):
    user = await user_repo.get_by_id(user_id)
    return user
```

## Using Repositories in Services

### Constructor Injection Pattern

```python
from database.repositories.interfaces import UserRepositoryInterface

class AuthService:
    """Authentication service with repository dependency injection"""

    def __init__(self, user_repository: UserRepositoryInterface):
        self.user_repo = user_repository

    async def register_user(self, username: str, password: str):
        # Check if user exists
        existing = await self.user_repo.get_by_username(username)
        if existing:
            raise UserAlreadyExistsError()

        # Create new user
        user = await self.user_repo.create(
            username=username,
            hashed_password=hash_password(password)
        )
        return user
```

### Service Dependency Injection

```python
# core/service_dependencies.py
from database.repositories.interfaces import UserRepositoryInterface
from core.repository_dependencies import get_user_repository

def get_auth_service(
    user_repo: UserRepositoryInterface = Depends(get_user_repository)
) -> IAuthService:
    """Get authentication service with injected repository"""
    from services.authservice.auth_service import AuthService
    return AuthService(user_repo)
```

## Available Repository Interfaces

### UserRepositoryInterface

```python
# CRUD operations
user = await user_repo.get_by_id(user_id)
user = await user_repo.get_by_email(email)
user = await user_repo.get_by_username(username)
user = await user_repo.create(username=..., email=...)
user = await user_repo.update(user_id, email=new_email)
deleted = await user_repo.delete(user_id)

# User-specific operations
await user_repo.update_last_login(user_id)
```

### VocabularyRepositoryInterface

```python
# CRUD operations
word = await vocab_repo.get_by_id(word_id)
word = await vocab_repo.get_by_lemma(lemma, language="de")
words = await vocab_repo.get_by_difficulty_level(level="A1", language="de")
words = await vocab_repo.search_words(query="Haus", language="de")
```

### UserVocabularyProgressRepositoryInterface

```python
# Progress tracking
progress = await progress_repo.get_user_progress(user_id, language="de")
word_progress = await progress_repo.get_user_word_progress(user_id, vocab_id)
updated = await progress_repo.mark_word_known(user_id, vocab_id, is_known=True)
```

### ProcessingSessionRepositoryInterface

```python
# Session management
session = await session_repo.get_by_session_id(session_id)
session = await session_repo.update_status(session_id, status="completed")
sessions = await session_repo.get_user_sessions(user_id, status="active")
```

## Creating a New Repository

### 1. Define Interface in `interfaces.py`

```python
from abc import ABC, abstractmethod

class GameSessionRepositoryInterface(BaseRepositoryInterface[Any, str]):
    """Game session repository operations"""

    @abstractmethod
    async def get_by_session_id(self, db: Session, session_id: str) -> Any | None:
        """Get game session by session ID"""
        pass

    @abstractmethod
    async def get_user_sessions(self, db: Session, user_id: str) -> list[Any]:
        """Get all sessions for a user"""
        pass
```

### 2. Create Concrete Implementation

```python
# database/repositories/game_session_repository.py
from sqlalchemy import select
from database.models import GameSession
from .base_repository import BaseRepository
from .interfaces import GameSessionRepositoryInterface

class GameSessionRepository(BaseRepository[GameSession], GameSessionRepositoryInterface):
    """Game session repository implementation"""

    def __init__(self, session: AsyncSession):
        super().__init__(GameSession, session)

    async def get_by_session_id(self, session_id: str) -> GameSession | None:
        stmt = select(GameSession).where(GameSession.session_id == session_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_sessions(self, user_id: str) -> list[GameSession]:
        stmt = select(GameSession).where(GameSession.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
```

### 3. Add Dependency Injection Function

```python
# core/repository_dependencies.py
def get_game_session_repository(
    db: Annotated[AsyncSession, Depends(get_async_session)]
) -> GameSessionRepositoryInterface:
    """Get game session repository instance"""
    return GameSessionRepository(db)
```

### 4. Export from `dependencies.py`

```python
# core/dependencies.py
try:
    from .repository_dependencies import (
        # ... existing imports
        get_game_session_repository,
    )
except ImportError:
    pass

__all__ = [
    # ... existing exports
    "get_game_session_repository",
]
```

## Testing with Mock Repositories

```python
import pytest
from unittest.mock import AsyncMock
from database.repositories.interfaces import UserRepositoryInterface

class MockUserRepository(UserRepositoryInterface):
    """Mock repository for testing"""

    def __init__(self):
        self.users = {}
        self.next_id = 1

    async def get_by_id(self, user_id: int):
        return self.users.get(user_id)

    async def get_by_username(self, username: str):
        return next((u for u in self.users.values() if u.username == username), None)

    async def create(self, **kwargs):
        user_id = self.next_id
        self.next_id += 1
        user = User(id=user_id, **kwargs)
        self.users[user_id] = user
        return user

@pytest.mark.asyncio
async def test_auth_service_registration():
    # Arrange
    mock_repo = MockUserRepository()
    auth_service = AuthService(mock_repo)

    # Act
    user = await auth_service.register_user("testuser", "SecurePass123!")

    # Assert
    assert user.username == "testuser"
    assert len(mock_repo.users) == 1
```

## Migration Checklist

When migrating a service to use repositories:

- [ ] Identify all database operations in the service
- [ ] Check if repository interface exists, create if needed
- [ ] Ensure concrete repository implements all required methods
- [ ] Add repository dependency injection function
- [ ] Update service constructor to accept repository interface
- [ ] Update service instantiation to inject repository
- [ ] Replace direct database queries with repository calls
- [ ] Update tests to use mock repositories
- [ ] Verify all routes still work correctly

## Anti-Patterns to Avoid

### ❌ Service Creating Repository Directly

```python
class MyService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)  # Bad: tight coupling
```

### ✅ Repository Injected via Interface

```python
class MyService:
    def __init__(self, user_repo: UserRepositoryInterface):
        self.repo = user_repo  # Good: depends on abstraction
```

### ❌ Mixing Database Access Methods

```python
class MyService:
    def __init__(self, db: AsyncSession, user_repo: UserRepositoryInterface):
        self.db = db
        self.repo = user_repo

    async def get_user(self, user_id):
        # Bad: mixing direct DB access with repository
        stmt = select(User).where(User.id == user_id)
        return await self.db.execute(stmt)
```

### ✅ Consistent Repository Usage

```python
class MyService:
    def __init__(self, user_repo: UserRepositoryInterface):
        self.repo = user_repo

    async def get_user(self, user_id):
        # Good: all data access through repository
        return await self.repo.get_by_id(user_id)
```

## See Also

- [Dependency Injection Guide](./DEPENDENCY_INJECTION.md)
- [Testing Guide](./TESTING_GUIDE.md)
- [Architecture Overview](./ARCHITECTURE_OVERVIEW.md)
