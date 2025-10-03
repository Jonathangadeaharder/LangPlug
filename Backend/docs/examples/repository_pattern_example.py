"""
Repository Pattern Usage Example

This file demonstrates how to use the repository pattern with dependency injection
in FastAPI routes and services. This is a reference implementation showing best practices.

Do NOT import this file in production code - it's for documentation only.
"""

from fastapi import APIRouter, Depends, HTTPException

from core.dependencies import (
    get_user_repository,
    get_user_vocabulary_progress_repository,
    get_vocabulary_repository,
)
from database.models import User
from database.repositories.interfaces import (
    UserRepositoryInterface,
    UserVocabularyProgressRepositoryInterface,
    VocabularyRepositoryInterface,
)

# Example router
router = APIRouter(prefix="/example", tags=["example"])


# ─────────────────────────────────────────────────────────────
# Example 1: Simple Repository Usage in Routes
# ─────────────────────────────────────────────────────────────


@router.get("/users/{user_id}")
async def get_user_example(user_id: int, user_repo: UserRepositoryInterface = Depends(get_user_repository)):
    """
    Example: Get user by ID using repository

    Benefits:
        - Clean, readable code
        - No SQL in route handler
        - Easy to test with mock repository
        - Type-safe with interface contract
    """
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "username": user.username, "email": user.email}


@router.get("/vocabulary/level/{level}")
async def get_vocabulary_by_level_example(
    level: str,
    limit: int = 100,
    vocab_repo: VocabularyRepositoryInterface = Depends(get_vocabulary_repository),
):
    """
    Example: Get vocabulary words by difficulty level

    Benefits:
        - Repository handles query complexity
        - Route stays focused on HTTP concerns
        - Easy to add caching in repository
    """
    words = await vocab_repo.get_by_difficulty_level(level=level, language="de", limit=limit)
    return {"level": level, "count": len(words), "words": [w.word for w in words]}


# ─────────────────────────────────────────────────────────────
# Example 2: Using Multiple Repositories
# ─────────────────────────────────────────────────────────────


@router.get("/users/{user_id}/progress")
async def get_user_progress_example(
    user_id: int,
    progress_repo: UserVocabularyProgressRepositoryInterface = Depends(get_user_vocabulary_progress_repository),
    vocab_repo: VocabularyRepositoryInterface = Depends(get_vocabulary_repository),
):
    """
    Example: Combine multiple repositories in single endpoint

    Benefits:
        - Each repository focused on single entity
        - Clear data access boundaries
        - Easy to optimize queries per repository
    """
    progress = await progress_repo.get_user_progress(user_id, language="de")

    # Enrich with vocabulary details
    enriched = []
    for p in progress:
        word = await vocab_repo.get_by_id(p.vocabulary_id)
        enriched.append({"word": word.word, "is_known": p.is_known, "review_count": p.review_count})

    return {"user_id": user_id, "total_words": len(enriched), "progress": enriched}


# ─────────────────────────────────────────────────────────────
# Example 3: Service with Repository Dependency Injection
# ─────────────────────────────────────────────────────────────


class ExampleService:
    """
    Example service using repository pattern

    This demonstrates how to structure services that depend on repositories.
    Services receive repository interfaces via constructor injection.
    """

    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        vocab_repo: VocabularyRepositoryInterface,
        progress_repo: UserVocabularyProgressRepositoryInterface,
    ):
        """
        Initialize service with repository dependencies

        Args:
            user_repo: User repository interface
            vocab_repo: Vocabulary repository interface
            progress_repo: Progress tracking repository interface
        """
        self.user_repo = user_repo
        self.vocab_repo = vocab_repo
        self.progress_repo = progress_repo

    async def calculate_user_level(self, user_id: int) -> str:
        """
        Calculate user's CEFR level based on vocabulary progress

        Returns:
            str: CEFR level (A1, A2, B1, B2, C1, C2)
        """
        # Get user progress
        progress = await self.progress_repo.get_user_progress(user_id, language="de")

        # Calculate known words per level
        level_stats = {"A1": 0, "A2": 0, "B1": 0, "B2": 0, "C1": 0, "C2": 0}

        for p in progress:
            if p.is_known:
                word = await self.vocab_repo.get_by_id(p.vocabulary_id)
                if word and word.difficulty_level in level_stats:
                    level_stats[word.difficulty_level] += 1

        # Determine level (70% mastery threshold)
        levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        for level in reversed(levels):  # Start from C2 downward
            total_words_stmt = await self.vocab_repo.get_by_difficulty_level(level, language="de", limit=10000)
            total_words = len(total_words_stmt)

            if total_words > 0:
                mastery = level_stats[level] / total_words
                if mastery >= 0.7:
                    return level

        return "A1"  # Default


# Service dependency injection
def get_example_service(
    user_repo: UserRepositoryInterface = Depends(get_user_repository),
    vocab_repo: VocabularyRepositoryInterface = Depends(get_vocabulary_repository),
    progress_repo: UserVocabularyProgressRepositoryInterface = Depends(get_user_vocabulary_progress_repository),
) -> ExampleService:
    """
    Get example service with injected repositories

    This shows how to create a service dependency function that
    receives repository dependencies and constructs the service.
    """
    return ExampleService(user_repo, vocab_repo, progress_repo)


@router.get("/users/{user_id}/level")
async def get_user_level_example(user_id: int, service: ExampleService = Depends(get_example_service)):
    """
    Example: Using service with repository dependencies

    Benefits:
        - Business logic in service, not route
        - Service is testable with mock repositories
        - Route is thin and focused
    """
    level = await service.calculate_user_level(user_id)
    return {"user_id": user_id, "level": level}


# ─────────────────────────────────────────────────────────────
# Example 4: Testing with Mock Repositories
# ─────────────────────────────────────────────────────────────


class MockUserRepository(UserRepositoryInterface):
    """
    Mock user repository for testing

    This demonstrates how to create mock repositories for unit tests.
    The mock implements the same interface but stores data in memory.
    """

    def __init__(self):
        self.users = {}
        self.next_id = 1

    async def get_by_id(self, user_id: int):
        return self.users.get(user_id)

    async def get_by_email(self, email: str):
        return next((u for u in self.users.values() if u.email == email), None)

    async def get_by_username(self, username: str):
        return next((u for u in self.users.values() if u.username == username), None)

    async def create(self, **kwargs):
        user_id = self.next_id
        self.next_id += 1
        user = User(id=user_id, **kwargs)
        self.users[user_id] = user
        return user

    async def update(self, user_id: int, **kwargs):
        if user_id in self.users:
            for key, value in kwargs.items():
                setattr(self.users[user_id], key, value)
            return self.users[user_id]
        return None

    async def delete(self, user_id: int):
        return self.users.pop(user_id, None) is not None

    async def exists(self, user_id: int):
        return user_id in self.users

    async def update_last_login(self, user_id: int):
        # Mock implementation
        pass


# Example test (pseudocode)
async def test_example_service():
    """
    Example test using mock repository

    This shows how easy it is to test services when they depend on
    repository interfaces instead of concrete database implementations.
    """
    # Arrange
    mock_user_repo = MockUserRepository()
    mock_vocab_repo = None  # Create mock
    mock_progress_repo = None  # Create mock

    service = ExampleService(mock_user_repo, mock_vocab_repo, mock_progress_repo)

    # Create test user
    await mock_user_repo.create(username="testuser", email="test@example.com")

    # Act
    # level = await service.calculate_user_level(1)

    # Assert
    # assert level == "A1"


# ─────────────────────────────────────────────────────────────
# Key Takeaways
# ─────────────────────────────────────────────────────────────

# 1. ALWAYS depend on repository interfaces, not concrete implementations
# 2. Inject repositories via FastAPI Depends() in routes
# 3. Inject repositories via constructor in services
# 4. Create mock repositories for testing
# 5. Keep routes thin - business logic belongs in services
# 6. Each repository handles one entity type
# 7. Repository methods should have clear, single purposes
# 8. Use type hints for all repository parameters and returns
