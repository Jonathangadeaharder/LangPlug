# LangPlug Backend - Code Style Guide

**Version**: 1.0
**Last Updated**: 2025-10-03

Comprehensive Python coding standards and best practices for LangPlug Backend development.

---

## Table of Contents

1. [Philosophy](#philosophy)
2. [Python Style Guidelines](#python-style-guidelines)
3. [Naming Conventions](#naming-conventions)
4. [File Organization](#file-organization)
5. [Import Ordering](#import-ordering)
6. [Type Hinting](#type-hinting)
7. [Docstrings](#docstrings)
8. [Error Handling](#error-handling)
9. [Async/Await Best Practices](#asyncawait-best-practices)
10. [Testing Patterns](#testing-patterns)
11. [Code Review Checklist](#code-review-checklist)

---

## Philosophy

### Core Principles

**Code is read more often than written**. Optimize for:
- **Readability**: Clear, self-documenting code
- **Maintainability**: Easy to modify and extend
- **Testability**: Designed for comprehensive testing
- **Performance**: Efficient without sacrificing clarity
- **Consistency**: Uniform style across the codebase

### Golden Rules

1. **Explicit is better than implicit** - No magic, no surprises
2. **Simple is better than complex** - Avoid clever code
3. **Flat is better than nested** - Reduce indentation levels
4. **Errors should never pass silently** - Fail fast and loud
5. **If implementation is hard to explain, it's a bad idea** - Rethink design

---

## Python Style Guidelines

### PEP 8 Compliance

LangPlug Backend follows **PEP 8** with project-specific additions. We use **Ruff** for automatic formatting and linting.

#### Line Length

```python
# Maximum line length: 88 characters (Ruff default)
# This is shorter than PEP 8's 79 to improve readability

# Good
def process_video_chunk(
    video_id: str, chunk_id: str, user_id: str
) -> ProcessedChunk:
    pass

# Bad - exceeds 88 characters
def process_video_chunk(video_id: str, chunk_id: str, user_id: str, options: dict) -> ProcessedChunk:
    pass
```

#### Indentation

```python
# Use 4 spaces (never tabs)

# Good
def example():
    if condition:
        do_something()
        return result

# Bad - mixing spaces and tabs
def example():
	if condition:
        do_something()
```

#### Blank Lines

```python
# Two blank lines before top-level functions/classes
# One blank line between methods


def first_function():
    pass


def second_function():
    pass


class MyClass:
    def first_method(self):
        pass

    def second_method(self):
        pass
```

#### Whitespace

```python
# Good - proper spacing
result = function(arg1, arg2)
my_list = [1, 2, 3]
my_dict = {"key": "value"}

if x == 4:
    print(x, y)

# Bad - inconsistent spacing
result=function( arg1,arg2 )
my_list=[1,2,3]
my_dict={"key":"value"}

if x==4 :
    print(x,y)
```

### Quotes

```python
# Use double quotes for strings (project standard)
message = "Hello, world!"
error = "File not found"

# Use single quotes for dict keys (when not using literals)
data = {"key": "value"}

# Triple double quotes for docstrings
def example():
    """This is a docstring."""
    pass
```

### Comments

```python
# Good - explains WHY, not WHAT
# Calculate CEFR level using word frequency distribution
level = calculate_cefr_level(word)

# Bad - explains obvious WHAT
# Set level to result of calculate_cefr_level function
level = calculate_cefr_level(word)

# Inline comments: two spaces before #
result = process_data(x)  # Process user input

# Block comments: separate paragraph with blank line
# This is a complex algorithm that requires explanation.
# It uses dynamic programming to optimize performance.
#
# First, we initialize the cache...
cache = {}
```

### Line Breaks

```python
# Break before binary operators (PEP 8 recommendation)
total = (
    first_value
    + second_value
    + third_value
)

# Function calls with many arguments
result = my_function(
    argument1,
    argument2,
    argument3,
    keyword1=value1,
    keyword2=value2,
)

# Chained method calls
result = (
    some_object
    .filter(condition1)
    .map(transformation)
    .filter(condition2)
)
```

---

## Naming Conventions

### General Rules

| Element | Convention | Example |
|---------|------------|---------|
| **Module** | snake_case | `vocabulary_service.py` |
| **Package** | snake_case | `authservice/` |
| **Class** | PascalCase | `VocabularyService` |
| **Function** | snake_case | `get_vocabulary_words()` |
| **Method** | snake_case | `process_chunk()` |
| **Variable** | snake_case | `user_id`, `word_count` |
| **Constant** | UPPER_SNAKE_CASE | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| **Private** | _leading_underscore | `_internal_helper()` |
| **Protected** | _leading_underscore | `_validate_input()` |

### Specific Guidelines

#### Classes

```python
# Good - noun, descriptive, PascalCase
class UserRepository:
    pass

class VocabularyProgressService:
    pass

class TranscriptionStrategy:
    pass

# Bad - verb, vague, wrong case
class ProcessData:  # Should be a function, not a class
    pass

class Thing:  # Too vague
    pass

class vocabulary_service:  # Wrong case
    pass
```

#### Functions and Methods

```python
# Good - verb phrase, describes action
def get_user_by_id(user_id: str) -> User:
    pass

def calculate_vocabulary_level(word: str) -> str:
    pass

async def process_video_chunk(chunk_id: str) -> ProcessedChunk:
    pass

# Bad - noun, ambiguous, too short
def user(id):  # Unclear if getting, creating, or updating
    pass

def proc(c):  # Unclear abbreviation
    pass
```

#### Variables

```python
# Good - descriptive, clear type/purpose
user_id = "123e4567"
vocabulary_words = ["hello", "world"]
is_authenticated = True
max_retry_attempts = 3

# Bad - single letter (except loops), ambiguous
u = "123e4567"
words = ["hello", "world"]  # Ambiguous - vocabulary words? dictionary words?
flag = True  # What flag?
max = 3  # Max what?

# Loop variables: single letter OK for simple loops
for i in range(10):
    print(i)

# But descriptive names better for complex loops
for user_index, user in enumerate(users):
    process_user(user)
```

#### Constants

```python
# Good - module-level constants at top of file
MAX_VIDEO_SIZE_MB = 500
DEFAULT_TRANSCRIPTION_MODEL = "whisper-medium"
ALLOWED_VIDEO_EXTENSIONS = [".mp4", ".avi", ".mkv"]
CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

# Bad - magic numbers/strings embedded in code
if video.size > 524288000:  # What is this number?
    raise ValueError("Video too large")

# Good - use named constant
if video.size > MAX_VIDEO_SIZE_MB * 1024 * 1024:
    raise ValueError(f"Video exceeds {MAX_VIDEO_SIZE_MB}MB limit")
```

#### Booleans

```python
# Good - use is_, has_, can_, should_ prefixes
is_authenticated = True
has_permission = False
can_process = True
should_retry = False

# Bad - ambiguous, no prefix
authenticated = True  # Is it authenticated? Should it be authenticated?
permission = False  # Has permission? Permission granted?
```

#### Private/Protected

```python
class VocabularyService:
    def __init__(self):
        self._repository = VocabularyRepository()  # Protected
        self.__cache = {}  # Private (name mangling)

    def get_word(self, word: str) -> Word:
        """Public API method"""
        return self._fetch_from_cache_or_db(word)

    def _fetch_from_cache_or_db(self, word: str) -> Word:
        """Protected helper (internal use, but subclasses can access)"""
        if word in self.__cache:
            return self.__cache[word]
        return self._repository.get_word(word)
```

---

## File Organization

### Project Structure

```
Backend/
├── api/                    # API layer
│   ├── routes/            # FastAPI route handlers
│   ├── models/            # Pydantic request/response models
│   └── dtos/              # Data Transfer Objects
├── core/                   # Core infrastructure
│   ├── config.py          # Configuration management
│   ├── dependencies.py    # Dependency injection
│   ├── auth.py            # Authentication
│   └── exceptions.py      # Custom exceptions
├── services/               # Business logic
│   ├── authservice/       # Authentication service
│   ├── vocabulary/        # Vocabulary management
│   ├── processing/        # Video processing
│   └── ...
├── database/               # Data layer
│   ├── models.py          # SQLAlchemy models
│   └── repositories/      # Data access
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── conftest.py        # Test fixtures
└── main.py                 # Application entry point
```

### File Structure

**Standard Python file layout**:

```python
"""Module-level docstring.

Brief description of module purpose and main components.
"""

# 1. Standard library imports
import os
import sys
from typing import Optional, List, Dict

# 2. Third-party imports
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

# 3. Local application imports
from api.models.vocabulary import VocabularyResponse
from core.dependencies import get_db
from services.vocabulary.vocabulary_service_new import VocabularyService

# 4. Module-level constants
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200

# 5. Module-level variables (if needed)
logger = logging.getLogger(__name__)

# 6. Classes and functions
class VocabularyManager:
    """Class implementation."""
    pass


def get_vocabulary_words() -> List[str]:
    """Function implementation."""
    pass


# 7. Entry point (if script)
if __name__ == "__main__":
    main()
```

### One Class Per File (Recommended)

```python
# Good - services/vocabulary/vocabulary_query_service.py
class VocabularyQueryService:
    """Single focused class per file"""
    pass

# Acceptable - services/vocabulary/vocabulary_service_new.py
# If classes are tightly related (facade pattern)
class VocabularyService:
    """Main facade"""
    pass

class VocabularyServiceConfig:
    """Configuration for main service"""
    pass

# Bad - multiple unrelated classes
class VocabularyService:
    pass

class UserService:  # Should be in separate file
    pass
```

---

## Import Ordering

### Standard Order

```python
"""Module docstring."""

# 1. Standard library imports (alphabetical)
import asyncio
import logging
import os
from pathlib import Path
from typing import List, Optional, Dict

# 2. Third-party imports (alphabetical by package)
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 3. Local imports (alphabetical, absolute imports preferred)
from api.models.vocabulary import VocabularyResponse
from core.dependencies import get_db, current_active_user
from database.models import User, VocabularyWord
from services.vocabulary.vocabulary_service_new import VocabularyService
```

### Import Style

```python
# Good - explicit imports
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException

# Acceptable - module import for many items
import sqlalchemy as sa

# Bad - wildcard imports (avoid)
from services.vocabulary import *  # What exactly is imported?

# Good - group related imports
from database.models import (
    User,
    VocabularyWord,
    VocabularyProgress,
    VocabularyLevel,
)
```

### Absolute vs Relative Imports

```python
# Preferred - absolute imports (clear and explicit)
from services.vocabulary.vocabulary_service_new import VocabularyService
from services.vocabulary.vocabulary_query_service import VocabularyQueryService

# Acceptable - relative imports within same package
# File: services/vocabulary/vocabulary_service_new.py
from .vocabulary_query_service import VocabularyQueryService
from .vocabulary_progress_service import VocabularyProgressService

# Bad - mixing styles inconsistently
from services.vocabulary.vocabulary_query_service import VocabularyQueryService
from .vocabulary_progress_service import VocabularyProgressService  # Inconsistent
```

---

## Type Hinting

### Basic Type Hints

```python
# Primitive types
def get_username(user_id: str) -> str:
    pass

def calculate_score(points: int, multiplier: float) -> float:
    pass

def is_valid(data: dict) -> bool:
    pass

# Collections (from typing module)
from typing import List, Dict, Set, Tuple, Optional

def get_words() -> List[str]:
    pass

def get_user_data() -> Dict[str, str]:
    pass

def get_unique_tags() -> Set[str]:
    pass

def get_coordinates() -> Tuple[float, float]:
    pass

# Optional (value or None)
def find_user(user_id: str) -> Optional[User]:
    """Returns User or None if not found"""
    pass
```

### Advanced Type Hints

```python
from typing import Union, Callable, TypeVar, Generic, Protocol

# Union types (multiple possible types)
def process_input(data: Union[str, int, float]) -> str:
    return str(data)

# Callable (function type)
def apply_transform(
    data: List[int],
    transform: Callable[[int], int]
) -> List[int]:
    return [transform(x) for x in data]

# TypeVar (generic types)
T = TypeVar('T')

def first_item(items: List[T]) -> Optional[T]:
    return items[0] if items else None

# Protocol (structural subtyping)
class Transcribable(Protocol):
    """Any object with a transcribe method"""
    def transcribe(self, audio_path: str) -> str: ...

def process_audio(service: Transcribable, path: str) -> str:
    return service.transcribe(path)
```

### Async Type Hints

```python
from typing import Awaitable, AsyncIterator

# Async function returns
async def get_user(user_id: str) -> User:
    pass

# Awaitable return type (for functions that may be sync or async)
def get_user_flexible(user_id: str) -> Awaitable[User]:
    pass

# Async generators
async def stream_results() -> AsyncIterator[dict]:
    for item in items:
        yield item
```

### Type Aliases

```python
# Create readable aliases for complex types
from typing import Dict, List, Tuple

UserID = str
VocabularyMap = Dict[str, List[str]]
Coordinates = Tuple[float, float]

def get_user_vocabulary(user_id: UserID) -> VocabularyMap:
    pass

def get_location() -> Coordinates:
    return (40.7128, -74.0060)
```

### When to Skip Type Hints

```python
# Skip for simple, obvious cases in local scope
def process():
    items = []  # Type obvious from literal
    count = 0

    for item in get_items():  # item type inferred
        items.append(item)
        count += 1

# Always use for public API
def get_vocabulary_words(user_id: str) -> List[VocabularyWord]:
    """Public API must have type hints"""
    pass
```

---

## Docstrings

### Format: Google Style

LangPlug uses **Google-style docstrings** for consistency and readability.

### Module Docstrings

```python
"""Vocabulary service for managing user vocabulary progress.

This module provides the main VocabularyService facade that coordinates
vocabulary queries, progress tracking, and statistics calculation.

Example:
    Basic usage::

        service = VocabularyService(user_id="123", db=session)
        words = await service.get_known_words()
        await service.mark_word_as_known("hello")

Attributes:
    DEFAULT_PAGE_SIZE (int): Default pagination size (50)
    MAX_PAGE_SIZE (int): Maximum pagination size (200)
"""
```

### Class Docstrings

```python
class VocabularyService:
    """Facade for vocabulary management operations.

    Coordinates vocabulary queries, progress tracking, and statistics
    through specialized sub-services. Provides a simplified API for
    common vocabulary operations.

    Attributes:
        user_id: UUID of the user
        db: Async database session
        query_service: Handles vocabulary queries
        progress_service: Manages progress tracking
        stats_service: Calculates vocabulary statistics

    Example:
        Create and use the service::

            service = VocabularyService(user_id="123", db=session)
            known_words = await service.get_known_words()
            await service.mark_word_as_known("hello")
    """
```

### Function/Method Docstrings

```python
async def get_vocabulary_words(
    user_id: str,
    status_filter: Optional[str] = None,
    level_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = None
) -> List[VocabularyWord]:
    """Retrieve vocabulary words for a user with optional filtering.

    Fetches vocabulary words from the database with support for status
    and level filtering, as well as pagination. Returns empty list if
    no words found.

    Args:
        user_id: UUID of the user whose vocabulary to retrieve
        status_filter: Optional status filter ("known", "learning", "new")
        level_filter: Optional CEFR level filter ("A1", "A2", "B1", "B2", "C1", "C2")
        skip: Number of records to skip for pagination (default: 0)
        limit: Maximum number of records to return (default: 50)
        db: Database session (injected via dependency)

    Returns:
        List of VocabularyWord objects matching the criteria. Returns
        empty list if no matches found.

    Raises:
        ValueError: If status_filter or level_filter has invalid value
        HTTPException: If database query fails (status 500)

    Example:
        Get all known B1-level words::

            words = await get_vocabulary_words(
                user_id="123e4567",
                status_filter="known",
                level_filter="B1",
                skip=0,
                limit=20,
                db=session
            )
    """
```

### Property Docstrings

```python
class User:
    @property
    def full_name(self) -> str:
        """Full name combining first and last name.

        Returns:
            Formatted full name as "FirstName LastName"
        """
        return f"{self.first_name} {self.last_name}"
```

### One-Line Docstrings

```python
def is_valid_email(email: str) -> bool:
    """Check if email address format is valid."""
    pass

def get_current_time() -> datetime:
    """Return current UTC timestamp."""
    pass
```

### What NOT to Document

```python
# Bad - docstring states the obvious
def get_user(user_id: str) -> User:
    """Get a user.

    Args:
        user_id: The user ID

    Returns:
        User
    """
    pass

# Good - docstring adds value
def get_user(user_id: str) -> User:
    """Retrieve user from database by ID.

    Args:
        user_id: UUID of the user to retrieve

    Returns:
        User object with all profile information

    Raises:
        UserNotFoundError: If user_id doesn't exist in database
    """
    pass
```

---

## Error Handling

### Exception Philosophy

1. **Fail fast and loud** - Don't silently swallow errors
2. **Use specific exceptions** - Avoid bare `except:` blocks
3. **Handle at appropriate level** - Don't catch too early
4. **Provide context** - Include helpful error messages

### Custom Exceptions

```python
# core/exceptions.py
class LangPlugException(Exception):
    """Base exception for all LangPlug errors"""
    pass

class ValidationError(LangPlugException):
    """Raised when input validation fails"""
    pass

class AuthenticationError(LangPlugException):
    """Raised when authentication fails"""
    pass

class ResourceNotFoundError(LangPlugException):
    """Raised when requested resource doesn't exist"""
    pass

# Usage
def get_user(user_id: str) -> User:
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise ResourceNotFoundError(f"User {user_id} not found")
    return user
```

### Exception Handling Patterns

```python
# Good - specific exception handling
try:
    user = await get_user(user_id)
    await process_user(user)
except ResourceNotFoundError as e:
    logger.warning(f"User not found: {e}")
    raise HTTPException(status_code=404, detail=str(e))
except ValidationError as e:
    logger.warning(f"Validation failed: {e}")
    raise HTTPException(status_code=422, detail=str(e))

# Bad - catching all exceptions silently
try:
    user = await get_user(user_id)
    await process_user(user)
except:  # What went wrong? Nobody knows!
    pass

# Bad - catching too broad
try:
    user = await get_user(user_id)
    await process_user(user)
except Exception as e:  # Catches all exceptions, including unexpected ones
    logger.error(f"Error: {e}")
    pass
```

### Re-raising with Context

```python
# Good - add context when re-raising
try:
    result = await transcribe_audio(audio_path)
except WhisperModelError as e:
    logger.error(f"Transcription failed for {audio_path}: {e}")
    raise TranscriptionError(
        f"Failed to transcribe audio: {e}"
    ) from e  # Preserve original exception chain

# Bad - losing original exception
try:
    result = await transcribe_audio(audio_path)
except WhisperModelError as e:
    raise TranscriptionError("Transcription failed")  # Lost original error!
```

### Cleanup with Finally

```python
# Good - ensure cleanup happens
file = None
try:
    file = open("data.txt", "r")
    data = file.read()
    process_data(data)
except IOError as e:
    logger.error(f"File error: {e}")
    raise
finally:
    if file:
        file.close()

# Better - use context manager (automatic cleanup)
try:
    with open("data.txt", "r") as file:
        data = file.read()
        process_data(data)
except IOError as e:
    logger.error(f"File error: {e}")
    raise
```

### FastAPI Error Handling

```python
from fastapi import HTTPException, status

# Good - specific HTTP exceptions with detail
@router.get("/users/{user_id}")
async def get_user(user_id: str):
    try:
        user = await user_service.get_user(user_id)
        return user
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )

# Good - custom exception handler (global)
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(ResourceNotFoundError)
async def resource_not_found_handler(
    request: Request,
    exc: ResourceNotFoundError
):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)}
    )
```

---

## Async/Await Best Practices

### When to Use Async

```python
# Use async for:
# - Database queries
# - HTTP requests
# - File I/O (with aiofiles)
# - Any operation that waits on external systems

# Good - async database query
async def get_user(user_id: str, db: AsyncSession) -> User:
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()

# Good - async HTTP request
async def fetch_translation(text: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.translation.com/translate",
            json={"text": text}
        )
        return response.json()["translation"]

# Don't use async for CPU-bound operations (use threading/multiprocessing)
# Bad - async for computation
async def calculate_fibonacci(n: int) -> int:
    # This blocks the event loop!
    if n <= 1:
        return n
    return await calculate_fibonacci(n-1) + await calculate_fibonacci(n-2)

# Good - use sync function
def calculate_fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
```

### Awaiting Patterns

```python
# Good - await one at a time
user = await get_user(user_id)
vocabulary = await get_vocabulary(user_id)

# Better - parallel execution with asyncio.gather
user, vocabulary = await asyncio.gather(
    get_user(user_id),
    get_vocabulary(user_id)
)

# Good - async list comprehension
results = [
    await process_item(item)
    for item in items
]

# Better - parallel processing
results = await asyncio.gather(
    *[process_item(item) for item in items]
)

# Good - async context manager
async with get_db_session() as db:
    user = await get_user(user_id, db)
```

### Mixing Sync and Async

```python
# Good - run sync code in async context
import asyncio

async def async_function():
    # Run CPU-bound sync function in thread pool
    result = await asyncio.to_thread(cpu_intensive_function, arg1, arg2)
    return result

def cpu_intensive_function(arg1, arg2):
    # Blocking computation
    return expensive_calculation(arg1, arg2)
```

### Error Handling in Async

```python
# Good - handle errors in async context
async def process_users(user_ids: List[str]):
    tasks = [process_user(uid) for uid in user_ids]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for user_id, result in zip(user_ids, results):
        if isinstance(result, Exception):
            logger.error(f"Failed to process {user_id}: {result}")
        else:
            logger.info(f"Processed {user_id} successfully")
```

### Async Generators

```python
# Good - async generator for streaming
async def stream_vocabulary_words(
    user_id: str,
    db: AsyncSession
) -> AsyncIterator[VocabularyWord]:
    """Stream vocabulary words one at a time"""
    offset = 0
    batch_size = 100

    while True:
        result = await db.execute(
            select(VocabularyWord)
            .where(VocabularyWord.user_id == user_id)
            .offset(offset)
            .limit(batch_size)
        )
        words = result.scalars().all()

        if not words:
            break

        for word in words:
            yield word

        offset += batch_size

# Usage
async for word in stream_vocabulary_words(user_id, db):
    await process_word(word)
```

---

## Testing Patterns

### Test Structure: Arrange-Act-Assert

```python
@pytest.mark.asyncio
async def test_get_vocabulary_words_returns_user_words(
    async_client: AsyncClient,
    auth_headers: dict
):
    """Test that GET /api/vocabulary/words returns authenticated user's words"""
    # Arrange - set up test data
    expected_words = ["hello", "world", "test"]

    # Act - perform the action
    response = await async_client.get(
        "/api/vocabulary/words",
        headers=auth_headers
    )

    # Assert - verify results
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    actual_words = [item["word"] for item in data]
    for word in expected_words:
        assert word in actual_words
```

### Test Naming

```python
# Good - descriptive test names following pattern:
# test_<method>_<scenario>_<expected_result>

def test_GET_vocabulary_words_returns_200_for_authenticated_user():
    pass

def test_POST_vocabulary_word_returns_401_for_unauthenticated_user():
    pass

def test_calculate_cefr_level_returns_A1_for_basic_word():
    pass

def test_transcribe_audio_raises_error_when_file_not_found():
    pass

# Bad - vague test names
def test_vocabulary():
    pass

def test_api():
    pass

def test_success():
    pass
```

### Fixtures

```python
# conftest.py - shared fixtures

@pytest.fixture
async def async_client():
    """Async HTTP client for API testing"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def sample_user():
    """Sample user data for testing"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "native_language": "en",
        "target_language": "es"
    }

@pytest.fixture
async def authenticated_user(async_client, sample_user):
    """Create and authenticate a test user"""
    # Register user
    await async_client.post("/api/auth/register", json=sample_user)

    # Login
    response = await async_client.post(
        "/api/auth/login",
        json={
            "username": sample_user["username"],
            "password": sample_user["password"]
        }
    )
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}
```

### Mocking

```python
from unittest.mock import AsyncMock, patch

# Good - mock external dependencies
@pytest.mark.asyncio
async def test_transcribe_audio_calls_whisper_model():
    """Test that transcription calls Whisper model"""
    # Arrange
    mock_model = AsyncMock(return_value="transcribed text")

    with patch("services.transcriptionservice.whisper_model", mock_model):
        service = WhisperTranscriptionService()

        # Act
        result = await service.transcribe("audio.mp3")

        # Assert
        assert result == "transcribed text"
        mock_model.assert_called_once_with("audio.mp3")

# Bad - testing implementation details
def test_internal_cache_structure():
    """Don't test internal implementation"""
    service = VocabularyService()
    # Testing private cache structure - brittle!
    assert isinstance(service._cache, dict)
```

### Parameterized Tests

```python
import pytest

@pytest.mark.parametrize(
    "word,expected_level",
    [
        ("hello", "A1"),
        ("world", "A1"),
        ("understand", "A2"),
        ("vocabulary", "B1"),
        ("sophisticated", "C1"),
    ]
)
def test_calculate_cefr_level_for_various_words(word, expected_level):
    """Test CEFR level calculation for different words"""
    result = calculate_cefr_level(word)
    assert result == expected_level
```

---

## Code Review Checklist

### Before Submitting Code

#### Functionality
- [ ] Code works as expected
- [ ] All tests pass (including new tests)
- [ ] Edge cases handled
- [ ] Error handling implemented
- [ ] No regressions introduced

#### Code Quality
- [ ] Follows PEP 8 and project style guide
- [ ] Functions < 20 lines (or well-justified if longer)
- [ ] Clear, descriptive names
- [ ] No commented-out code
- [ ] No magic numbers/strings (use constants)
- [ ] DRY principle followed (no duplication)

#### Documentation
- [ ] Public APIs have docstrings
- [ ] Complex logic explained with comments
- [ ] Type hints added for function signatures
- [ ] README updated if needed

#### Testing
- [ ] Unit tests added for new functionality
- [ ] Integration tests added if needed
- [ ] Test coverage maintained (80%+)
- [ ] Tests are deterministic and isolated

#### Security
- [ ] No hardcoded credentials or secrets
- [ ] Input validation implemented
- [ ] SQL injection protected (use parameterized queries)
- [ ] XSS protection (sanitize user input)
- [ ] Authentication/authorization checks present

#### Performance
- [ ] No unnecessary database queries (N+1 problem)
- [ ] Async operations used where appropriate
- [ ] Large datasets handled efficiently (pagination, streaming)
- [ ] Caching implemented where beneficial

### During Code Review

#### As Reviewer
- [ ] Understand the change (ask questions if unclear)
- [ ] Check for logic errors
- [ ] Verify test coverage
- [ ] Suggest improvements (not just find problems)
- [ ] Approve if LGTM (Looks Good To Me)

#### As Author
- [ ] Respond to all comments
- [ ] Explain design decisions
- [ ] Make requested changes or discuss alternatives
- [ ] Thank reviewers for feedback

---

## Common Patterns

### Repository Pattern

```python
class VocabularyRepository:
    """Data access layer for vocabulary"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_word(
        self,
        user_id: str,
        word: str
    ) -> Optional[VocabularyWord]:
        """Retrieve word from database"""
        result = await self.db.execute(
            select(VocabularyWord)
            .where(
                VocabularyWord.user_id == user_id,
                VocabularyWord.word == word
            )
        )
        return result.scalar_one_or_none()

    async def save_word(self, word: VocabularyWord) -> VocabularyWord:
        """Save word to database"""
        self.db.add(word)
        await self.db.commit()
        await self.db.refresh(word)
        return word
```

### Service Layer (Facade Pattern)

```python
class VocabularyService:
    """Business logic facade"""

    def __init__(self, user_id: str, db: AsyncSession):
        self.user_id = user_id
        self.repository = VocabularyRepository(db)
        self.progress_service = VocabularyProgressService(user_id, db)

    async def mark_word_as_known(self, word: str) -> VocabularyWord:
        """Mark word as known and update progress"""
        # Coordinate multiple operations
        vocab_word = await self.repository.get_word(self.user_id, word)
        if not vocab_word:
            vocab_word = VocabularyWord(
                user_id=self.user_id,
                word=word,
                status="known"
            )
        else:
            vocab_word.status = "known"

        await self.repository.save_word(vocab_word)
        await self.progress_service.update_progress(word, "known")
        return vocab_word
```

### Strategy Pattern (AI Models)

```python
class TranscriptionStrategy(Protocol):
    """Interface for transcription strategies"""
    def transcribe(self, audio_path: str) -> str: ...

class WhisperStrategy:
    """Whisper transcription implementation"""
    def transcribe(self, audio_path: str) -> str:
        # Whisper-specific logic
        pass

class ParakeetStrategy:
    """Parakeet transcription implementation"""
    def transcribe(self, audio_path: str) -> str:
        # Parakeet-specific logic
        pass

def get_transcription_service(model: str) -> TranscriptionStrategy:
    """Factory to select strategy"""
    if model == "whisper":
        return WhisperStrategy()
    elif model == "parakeet":
        return ParakeetStrategy()
    else:
        raise ValueError(f"Unknown model: {model}")
```

---

## Tools and Automation

### Ruff (Linting and Formatting)

```bash
# Check code
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

### Bandit (Security Scanning)

```bash
# Scan for security issues
bandit -r Backend/ -x Backend/tests/

# Generate report
bandit -r Backend/ -f html -o bandit-report.html
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Type Checking (MyPy - Optional)

```bash
# Type check codebase
mypy Backend/

# Ignore specific errors
mypy Backend/ --ignore-missing-imports
```

---

## Related Documentation

- **[TESTING_BEST_PRACTICES.md](../TESTING_BEST_PRACTICES.md)** - Testing guidelines
- **[ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)** - Architecture patterns
- **[DEVELOPER_SETUP.md](DEVELOPER_SETUP.md)** - Development environment
- **[API_INTEGRATION_GUIDE.md](API_INTEGRATION_GUIDE.md)** - API usage patterns

---

**Document Version**: 1.0
**Last Updated**: 2025-10-03
**Maintained By**: Development Team
