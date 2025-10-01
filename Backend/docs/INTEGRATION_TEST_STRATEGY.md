# Integration Test Strategy

**Date**: 2025-09-30
**Purpose**: Testing database-heavy services with real dependencies
**Target**: Services with <80% unit test coverage due to database operations

---

## Rationale

### Why Integration Tests?

**Problem with Unit Tests for DB-Heavy Code**:

- Requires extensive database session mocking (anti-pattern)
- Tests become implementation-coupled
- Brittle tests that break on refactoring
- Doesn't test actual database behavior
- Missing SQL-level bugs (queries, constraints, transactions)

**Benefits of Integration Tests**:

- Test actual database interactions
- Validate SQL queries and joins
- Test transaction boundaries
- Catch constraint violations
- Test real data serialization
- More confidence in production behavior

---

## Services Requiring Integration Tests

### High Priority (Database-Heavy)

1. **vocabulary_service.py** (58% coverage, 138 uncovered lines)
   - Methods: `get_vocabulary_by_level()`, `search_vocabulary()`, `add_vocabulary()`, `update_vocabulary()`
   - Why: Complex SQL queries with joins, filtering, pagination
   - Benefit: Validate query performance and correctness

2. **VocabularyRepository** (0% coverage, 125 uncovered lines)
   - All CRUD operations
   - Why: Core data access layer
   - Benefit: Validate database constraints and relationships

3. **UserRepository** (0% coverage, 67 uncovered lines)
   - User management operations
   - Why: Authentication and user data
   - Benefit: Test user creation, updates, queries

4. **filtering_handler.py** (51% coverage, 98 uncovered lines)
   - Methods: `_build_vocabulary_words()`, `extract_blocking_words()`
   - Why: Complex joins between vocabulary and user progress
   - Benefit: Test filtering logic with real data

### Medium Priority

5. **vocabulary_progress_service.py** (91% coverage, 9 uncovered lines)
   - Methods: `mark_level_known()`, `bulk_mark_words()`
   - Why: Bulk operations and transaction testing
   - Benefit: Validate batch operations

6. **vocabulary_lookup_service.py** (78% coverage, 20 uncovered lines)
   - Methods: Complex lemma lookups
   - Why: Case-insensitive search, wildcard queries
   - Benefit: Test search performance

---

## Integration Test Infrastructure

### Database Setup

```python
# tests/integration/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from database.models import Base

@pytest.fixture(scope="session")
async def test_db_engine():
    """Create test database engine"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()

@pytest.fixture
async def db_session(test_db_engine):
    """Create clean database session for each test"""
    async_session = sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()
```

### Test Data Fixtures

```python
@pytest.fixture
async def sample_vocabulary(db_session):
    """Create sample vocabulary words"""
    words = [
        VocabularyWord(
            lemma="house",
            word="house",
            language="en",
            difficulty_level="A1",
            part_of_speech="noun"
        ),
        VocabularyWord(
            lemma="Haus",
            word="Haus",
            language="de",
            difficulty_level="A1",
            part_of_speech="noun"
        )
    ]

    for word in words:
        db_session.add(word)

    await db_session.commit()
    return words

@pytest.fixture
async def sample_user(db_session):
    """Create sample user"""
    from database.models import User

    user = User(
        email="test@example.com",
        hashed_password="hashed",
        is_active=True
    )

    db_session.add(user)
    await db_session.commit()
    return user
```

---

## Test Structure and Patterns

### Integration Test Template

```python
"""
Integration tests for [Service Name]
Tests real database operations with actual database
"""

import pytest
from services.[module] import [ServiceClass]

class Test[ServiceName]Integration:
    """Integration tests for [ServiceName]"""

    @pytest.fixture
    def service(self):
        """Create service instance"""
        return [ServiceClass]()

    @pytest.mark.integration
    async def test_[operation]_success(
        self,
        service,
        db_session,
        sample_vocabulary,
        sample_user
    ):
        """Test [operation] with real database"""
        # Arrange
        # Use real fixtures

        # Act
        result = await service.[method](db_session, ...)

        # Assert
        # Verify database state
        assert result is not None

        # Query database to verify changes
        stmt = select(Model).where(...)
        db_result = await db_session.execute(stmt)
        db_object = db_result.scalar_one()

        assert db_object.field == expected_value
```

### Best Practices

1. **Use Real Database**
   - SQLite in-memory for speed
   - PostgreSQL for production-like testing
   - Clean state between tests

2. **Test Transactions**
   - Verify commit/rollback behavior
   - Test concurrent operations
   - Validate constraint violations

3. **Test SQL Queries**
   - Validate joins and relationships
   - Test filtering and pagination
   - Verify query performance

4. **Minimal Mocking**
   - Only mock external APIs
   - Use real database and models
   - No mocking of internal services

---

## Implementation Plan

### Phase 1: Infrastructure (30 minutes)

- [x] Create `tests/integration/` directory structure
- [ ] Set up database fixtures in `conftest.py`
- [ ] Create sample data fixtures
- [ ] Add pytest markers for integration tests
- [ ] Update pytest.ini configuration

### Phase 2: Repository Tests (1 hour)

- [ ] `test_vocabulary_repository.py`
  - CRUD operations
  - Search and filtering
  - Constraint validation
- [ ] `test_user_repository.py`
  - User management
  - Authentication queries

### Phase 3: Service Tests (2 hours)

- [ ] `test_vocabulary_service_integration.py`
  - `get_vocabulary_by_level()`
  - `search_vocabulary()`
  - `add_vocabulary()`
- [ ] `test_vocabulary_progress_integration.py`
  - `mark_level_known()`
  - `bulk_mark_words()`
- [ ] `test_filtering_handler_integration.py`
  - `_build_vocabulary_words()`
  - `extract_blocking_words()`

### Phase 4: Documentation (30 minutes)

- [ ] Document test execution
- [ ] Update coverage reports
- [ ] Create integration test guidelines

**Total Estimated Time**: 4 hours

---

## Execution Strategy

### Running Integration Tests

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific integration test file
pytest tests/integration/test_vocabulary_service_integration.py -v

# Run with coverage
pytest tests/integration/ --cov=services --cov=database/repositories

# Run unit tests only (exclude integration)
pytest tests/unit/ -v

# Run all tests
pytest tests/ -v
```

### CI/CD Integration

```yaml
# .github/workflows/test.yml
- name: Run Unit Tests
  run: pytest tests/unit/ --cov=services --cov-report=xml

- name: Run Integration Tests
  run: pytest tests/integration/ --cov=services --cov=database --cov-report=xml
  env:
    DATABASE_URL: sqlite+aiosqlite:///:memory:

- name: Upload Coverage
  uses: codecov/codecov-action@v3
```

---

## Success Criteria

### Quantitative Goals

- [ ] 15+ integration tests created
- [ ] All integration tests passing
- [ ] Coverage increase of 5-10% (to 65-70%)
- [ ] Test execution < 5 seconds
- [ ] Zero test flakiness

### Qualitative Goals

- [ ] Real database operations tested
- [ ] Transaction boundaries validated
- [ ] SQL queries verified
- [ ] Constraint violations tested
- [ ] Clear test documentation

---

## Coverage Targets After Integration Tests

| Service              | Current    | Target     | Gain       | Tests Needed |
| -------------------- | ---------- | ---------- | ---------- | ------------ |
| vocabulary_service   | 58%        | 75%        | +17%       | ~10          |
| VocabularyRepository | 0%         | 80%        | +80%       | ~8           |
| UserRepository       | 0%         | 80%        | +80%       | ~6           |
| filtering_handler    | 51%        | 70%        | +19%       | ~8           |
| vocabulary_progress  | 91%        | 95%        | +4%        | ~3           |
| **Overall**          | **60.18%** | **68-70%** | **+8-10%** | **~35**      |

---

## Risks and Mitigations

### Risk 1: Slow Test Execution

- **Mitigation**: Use SQLite in-memory
- **Fallback**: Parallel test execution

### Risk 2: Test Flakiness

- **Mitigation**: Clean database state between tests
- **Fallback**: Transaction rollback in fixtures

### Risk 3: Complex Setup

- **Mitigation**: Reusable fixtures
- **Fallback**: Factory functions for test data

### Risk 4: CI/CD Integration

- **Mitigation**: Use same database in CI
- **Fallback**: Docker-based database for CI

---

## Next Steps

1. **Create infrastructure** (`tests/integration/conftest.py`)
2. **Implement repository tests** (highest value)
3. **Add service integration tests** (database operations)
4. **Measure coverage improvement**
5. **Document results**

**Priority**: Start with repository tests (highest ROI, clearest test cases)

---

**Document Status**: ✅ Complete
**Next Action**: Implement integration test infrastructure
**Expected Outcome**: 68-70% overall coverage with high-quality integration tests
