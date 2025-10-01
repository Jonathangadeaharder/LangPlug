# Code Review & Refactoring Plan: vocabulary_service.py

**Date**: 2025-09-30
**Target**: services/vocabulary_service.py (1011 lines, 60% coverage, 131 uncovered lines)
**Goal**: Refactor complex methods to improve testability and maintainability
**Status**: ⏳ **Awaiting Execution Confirmation**

---

## Executive Summary

**Problem**: vocabulary_service.py has complex methods (50-80 lines) that are difficult to test, violating Single Responsibility Principle and making coverage improvement impractical.

**Root Cause Analysis**:

- `get_vocabulary_library()`: 85 lines, does 4 things (query building, counting, progress fetching, response formatting)
- `bulk_mark_level()`: 73 lines, handles bulk operations, existing progress, and transaction management
- Multiple duplicate methods with different signatures (3 versions of `bulk_mark_level`, 2 of `get_vocabulary_stats`)
- God class anti-pattern: 17 public methods in single service class

**Solution**: Extract helper methods, create specialized sub-services, eliminate duplicates, follow SOLID principles.

**Expected Impact**:

- Reduce method complexity: 50-80 lines → 10-20 lines per method
- Increase testability: Each extracted method easily unit-testable
- Improve coverage: 60% → 75%+ with same test count
- Better maintainability: Clear, focused responsibilities

---

## Critical Issues Identified

### 1. Complex Method: `get_vocabulary_library()` (Lines 219-303, 85 lines)

**Violations**:

- Single Responsibility: Does query building, pagination, progress joining, AND response formatting
- Too complex to test: Requires extensive mocking of db session, vocabulary data, user progress
- Deep nesting: 3 levels of conditionals
- Multiple concerns: Database querying, data transformation, business logic

**Refactoring Plan**:

```python
# BEFORE: 85 lines, 4 responsibilities
async def get_vocabulary_library(self, db, language, level, user_id, limit, offset):
    # Build query (10 lines)
    # Count total (5 lines)
    # Execute query (3 lines)
    # Fetch user progress (15 lines)
    # Format response (40 lines)
    return {...}

# AFTER: Extract 4 focused methods
def _build_vocabulary_query(self, language: str, level: Optional[str]) -> Select:
    """Build base vocabulary query with filters"""
    query = select(VocabularyWord).where(VocabularyWord.language == language)
    if level:
        query = query.where(VocabularyWord.difficulty_level == level)
    return query.order_by(
        VocabularyWord.difficulty_level,
        VocabularyWord.frequency_rank.nullslast(),
        VocabularyWord.lemma
    )

async def _get_user_progress_map(
    self, db: AsyncSession, user_id: int, vocab_ids: List[int]
) -> Dict[int, Dict[str, Any]]:
    """Fetch user progress for vocabulary IDs"""
    if not vocab_ids:
        return {}
    stmt = select(UserVocabularyProgress).where(
        and_(
            UserVocabularyProgress.user_id == user_id,
            UserVocabularyProgress.vocabulary_id.in_(vocab_ids)
        )
    )
    result = await db.execute(stmt)
    return {
        p.vocabulary_id: {
            "is_known": p.is_known,
            "confidence_level": p.confidence_level
        }
        for p in result.scalars()
    }

def _format_vocabulary_word(
    self, word: VocabularyWord, user_progress: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Format single vocabulary word with optional progress"""
    word_data = {
        "id": word.id,
        "word": word.word,
        "lemma": word.lemma,
        "difficulty_level": word.difficulty_level,
        "part_of_speech": word.part_of_speech,
        "gender": word.gender,
        "translation_en": word.translation_en,
        "pronunciation": word.pronunciation
    }
    if user_progress:
        word_data.update(user_progress)
    else:
        word_data["is_known"] = False
        word_data["confidence_level"] = 0
    return word_data

async def get_vocabulary_library(
    self, db, language, level=None, user_id=None, limit=100, offset=0
):
    """Get vocabulary library with optional filtering"""
    # Build and execute query (5 lines)
    query = self._build_vocabulary_query(language, level)
    total_count = await self._count_query_results(db, query)
    words = await self._execute_paginated_query(db, query, limit, offset)

    # Get user progress if needed (3 lines)
    progress_map = {}
    if user_id:
        progress_map = await self._get_user_progress_map(
            db, user_id, [w.id for w in words]
        )

    # Format response (5 lines)
    return {
        "words": [
            self._format_vocabulary_word(w, progress_map.get(w.id))
            for w in words
        ],
        "total_count": total_count,
        "limit": limit,
        "offset": offset,
        "language": language,
        "level": level
    }
```

**Benefits**:

- Each method < 20 lines
- Easily unit testable without database
- Clear separation of concerns
- Reusable helper methods

---

### 2. Duplicate Methods: Multiple `bulk_mark_level` Implementations

**Violations**:

- DRY: Three implementations (lines 352, 695, 885) doing the same thing
- Inconsistent interfaces: Different parameter names and types
- Maintenance nightmare: Bug fixes need to be applied 3 times
- Test duplication: Each version needs separate tests

**Current Implementations**:

```python
# Version 1 (lines 352-427): Original implementation
async def bulk_mark_level(self, db, user_id, language, level, is_known):
    # 73 lines of implementation
    pass

# Version 2 (lines 695-750): Wrapper with different interface
async def bulk_mark_level(self, user_id, level, target_language, known):
    async with self._get_session() as db:
        return await self.bulk_mark_level(db, user_id, target_language, level, known)

# Version 3 (lines 885-929): Another wrapper
async def bulk_mark_level_known(self, db_session, user_id, level, known):
    # Different implementation
    pass
```

**Refactoring Plan**:

- Keep ONE canonical implementation
- Delete duplicate versions
- Add interface adapters if needed for backward compatibility
- Document as deprecated if external callers exist

---

### 3. Duplicate Methods: Multiple `get_vocabulary_stats` Implementations

**Violations**:

- Two completely different implementations
- Line 490-540: Legacy version with session management
- Line 816-883: New version with external session
- Inconsistent return types and interfaces

**Refactoring Plan**:

- Consolidate to single implementation
- Use dependency injection for session
- Deprecate and remove legacy version
- Update all callers

---

### 4. God Class Anti-Pattern

**Violations**:

- 17 public methods in single class
- Mixed concerns: CRUD, search, statistics, bulk operations, legacy support
- 1011 lines (should be < 300)
- Single Responsibility Principle violated

**Refactoring Plan**:

```python
# NEW STRUCTURE: Split into focused services

# services/vocabulary/vocabulary_query_service.py (200 lines)
class VocabularyQueryService:
    """Handles vocabulary queries and search"""
    async def get_word_info(...)
    async def search_vocabulary(...)
    async def get_vocabulary_library(...)

    # Private helpers
    def _build_vocabulary_query(...)
    async def _execute_paginated_query(...)

# services/vocabulary/vocabulary_progress_service.py (150 lines)
class VocabularyProgressService:
    """Handles user vocabulary progress tracking"""
    async def mark_word_known(...)
    async def bulk_mark_level(...)
    async def get_user_vocabulary_stats(...)

# services/vocabulary/vocabulary_stats_service.py (100 lines)
class VocabularyStatsService:
    """Handles vocabulary statistics and analytics"""
    async def get_vocabulary_stats(...)
    async def get_user_progress_summary(...)
    async def get_supported_languages(...)

# services/vocabulary/vocabulary_service.py (100 lines)
class VocabularyService:
    """Facade for vocabulary operations"""
    def __init__(self):
        self.query_service = VocabularyQueryService()
        self.progress_service = VocabularyProgressService()
        self.stats_service = VocabularyStatsService()

    # Delegate to appropriate service
    async def get_word_info(self, ...):
        return await self.query_service.get_word_info(...)
```

---

## Detailed Refactoring Tasks

### Phase 1: Extract Helper Methods (Priority: High)

#### Task 1.1: Extract Query Building Methods

- [ ] **Extract `_build_vocabulary_query()`** from `get_vocabulary_library()`
  - Location: lines 230-241
  - New method: ~12 lines
  - Test: Verify query construction with/without level filter
  - Benefit: Reusable, testable without database

- [ ] **Extract `_build_search_query()`** from `search_vocabulary()`
  - Location: lines 315-335
  - New method: ~20 lines
  - Test: Verify LIKE clauses and ordering
  - Benefit: Search logic testable in isolation

- [ ] **Extract `_build_stats_query()`** from `get_vocabulary_stats()`
  - Location: lines 505-535 (multiple places)
  - New method: ~30 lines
  - Test: Verify aggregation and grouping
  - Benefit: Complex SQL isolated

#### Task 1.2: Extract Data Transformation Methods

- [ ] **Extract `_format_vocabulary_word()`**
  - Location: lines 276-294 in `get_vocabulary_library()`
  - New method: ~18 lines
  - Test: Verify formatting with/without user progress
  - Benefit: Pure function, trivially testable

- [ ] **Extract `_merge_user_progress()`**
  - Location: lines 258-272 in `get_vocabulary_library()`
  - New method: ~15 lines
  - Test: Verify progress dictionary creation
  - Benefit: Data transformation logic isolated

- [ ] **Extract `_format_stats_response()`**
  - Location: multiple places in stats methods
  - New method: ~20 lines
  - Test: Verify response structure
  - Benefit: Consistent formatting

#### Task 1.3: Extract Database Operation Methods

- [ ] **Extract `_get_user_progress_map()`**
  - Location: lines 258-272 in `get_vocabulary_library()`
  - New method: ~18 lines
  - Test: Mock db session, verify query and result processing
  - Benefit: Progress fetching reusable

- [ ] **Extract `_count_query_results()`**
  - Location: lines 244-246 (used in multiple places)
  - New method: ~8 lines
  - Test: Verify count query execution
  - Benefit: Pagination helper

- [ ] **Extract `_execute_paginated_query()`**
  - Location: inline in multiple methods
  - New method: ~10 lines
  - Test: Verify limit/offset application
  - Benefit: Consistent pagination

### Phase 2: Eliminate Duplicates (Priority: High)

#### Task 2.1: Consolidate `bulk_mark_level` Methods

- [ ] **Analyze three implementations**
  - Compare lines 352-427, 695-750, 885-929
  - Document differences in behavior
  - Identify canonical version

- [ ] **Create single implementation**
  - Keep most robust version (likely 352-427)
  - Add missing features from other versions
  - Ensure all test cases pass

- [ ] **Delete duplicate implementations**
  - Remove lines 695-750
  - Remove lines 885-929
  - Update all callers to use canonical version

- [ ] **Add deprecation warnings** (if external API)
  - Mark old signatures as deprecated
  - Provide migration guide
  - Schedule removal in next major version

#### Task 2.2: Consolidate `get_vocabulary_stats` Methods

- [ ] **Analyze two implementations**
  - Compare lines 490-540 and 816-883
  - Document differences
  - Choose implementation pattern

- [ ] **Create single implementation**
  - Use dependency injection for session
  - Consolidate query logic
  - Consistent return type

- [ ] **Delete legacy version**
  - Remove lines 752-814 (wrapper)
  - Remove lines 766-814 (\_get_vocabulary_stats_original)
  - Update all callers

### Phase 3: Split into Sub-Services (Priority: Medium)

#### Task 3.1: Create VocabularyQueryService

- [ ] **Create new file** `services/vocabulary/vocabulary_query_service.py`
- [ ] **Move query methods**:
  - `get_word_info()` (lines 30-83)
  - `search_vocabulary()` (lines 305-350)
  - `get_vocabulary_library()` (lines 219-303, refactored)
- [ ] **Move private helpers**:
  - `_build_vocabulary_query()`
  - `_build_search_query()`
  - `_execute_paginated_query()`
- [ ] **Update tests** to import from new location
- [ ] **Update imports** in all callers

#### Task 3.2: Create VocabularyProgressService

- [ ] **Create new file** `services/vocabulary/vocabulary_progress_service.py`
- [ ] **Move progress methods**:
  - `mark_word_known()` (lines 85-151)
  - `bulk_mark_level()` (consolidated version)
  - `get_user_vocabulary_stats()` (lines 153-217)
- [ ] **Move private helpers**:
  - `_get_user_progress_map()`
  - `_track_unknown_word()` (lines 428-463)
- [ ] **Update tests**
- [ ] **Update imports**

#### Task 3.3: Create VocabularyStatsService

- [ ] **Create new file** `services/vocabulary/vocabulary_stats_service.py`
- [ ] **Move stats methods**:
  - `get_vocabulary_stats()` (consolidated version)
  - `get_user_progress_summary()` (lines 931-981)
  - `get_supported_languages()` (lines 466-487)
- [ ] **Move private helpers**:
  - `_build_stats_query()`
  - `_format_stats_response()`
  - `_validate_language_code()` (lines 985-991)
  - `_calculate_difficulty_score()` (lines 993-1008)
- [ ] **Update tests**
- [ ] **Update imports**

#### Task 3.4: Create Facade Service

- [ ] **Refactor vocabulary_service.py** to be a facade
- [ ] **Inject sub-services** via constructor
- [ ] **Delegate all methods** to appropriate sub-service
- [ ] **Keep backward compatibility** for external callers
- [ ] **Update dependency injection** configuration

### Phase 4: Add Comprehensive Tests (Priority: High)

#### Task 4.1: Test Extracted Query Helpers

- [ ] **Test `_build_vocabulary_query()`**
  - With level filter
  - Without level filter
  - Verify ORDER BY clause
  - ~3 tests, 20 lines total

- [ ] **Test `_build_search_query()`**
  - Case insensitive matching
  - Word vs lemma priority
  - Limit application
  - ~4 tests, 30 lines total

#### Task 4.2: Test Extracted Data Transformation Helpers

- [ ] **Test `_format_vocabulary_word()`**
  - With user progress
  - Without user progress
  - All fields present
  - ~3 tests, 25 lines total

- [ ] **Test `_merge_user_progress()`**
  - Empty progress
  - Partial progress
  - Full progress
  - ~3 tests, 20 lines total

#### Task 4.3: Integration Tests for Refactored Methods

- [ ] **Test refactored `get_vocabulary_library()`**
  - With pagination
  - With user progress
  - With level filter
  - Edge cases (empty results, large offsets)
  - ~6 tests, 100 lines total

- [ ] **Test consolidated `bulk_mark_level()`**
  - All known
  - All unknown
  - Mixed existing progress
  - Transaction rollback on error
  - ~5 tests, 80 lines total

### Phase 5: Documentation & Cleanup (Priority: Medium)

#### Task 5.1: Update Documentation

- [ ] **Add docstrings** to all extracted methods
- [ ] **Document service responsibilities** in module docstrings
- [ ] **Create architecture diagram** showing service split
- [ ] **Update API documentation** if public interface changed

#### Task 5.2: Code Cleanup

- [ ] **Remove commented code** (if any)
- [ ] **Remove unused imports**
- [ ] **Standardize formatting** (black/autopep8)
- [ ] **Run linters** (pylint, mypy)

#### Task 5.3: Performance Validation

- [ ] **Benchmark critical paths**
  - `get_vocabulary_library()` with 1000 words
  - `bulk_mark_level()` with 500 words
  - Ensure no performance regression

- [ ] **Profile queries**
  - Check for N+1 queries
  - Verify proper indexing
  - Optimize if needed

---

## Success Criteria

### Quantitative Goals

| Metric                | Before   | Target     | Status     |
| --------------------- | -------- | ---------- | ---------- |
| Total Lines           | 1011     | < 800      | ⏳ Pending |
| Largest Method        | 85 lines | < 30 lines | ⏳ Pending |
| Test Coverage         | 60%      | 75%+       | ⏳ Pending |
| Cyclomatic Complexity | High     | Low        | ⏳ Pending |
| Number of Classes     | 1        | 4          | ⏳ Pending |
| Avg Method Length     | 40 lines | < 20 lines | ⏳ Pending |

### Qualitative Goals

- [ ] All methods follow Single Responsibility Principle
- [ ] No duplicate implementations
- [ ] Each method easily unit-testable
- [ ] Clear separation of concerns
- [ ] Consistent coding style
- [ ] Comprehensive test coverage for new helpers

---

## Execution Strategy

### Step 1: Create Feature Branch

```bash
git checkout -b refactor/vocabulary-service-split
```

### Step 2: Phase-by-Phase Execution

1. **Phase 1**: Extract helpers (all passing tests)
2. **Phase 2**: Eliminate duplicates (all passing tests)
3. **Phase 3**: Split services (all passing tests)
4. **Phase 4**: Add tests (coverage target met)
5. **Phase 5**: Documentation and cleanup

### Step 3: Validation Between Phases

```bash
# After each phase
pytest tests/unit/services/test_vocabulary*.py -v
pytest tests/integration/test_vocabulary_service*.py -v
pytest --cov=services/vocabulary_service --cov-report=term-missing
```

### Step 4: Code Review & Merge

- Create pull request
- Self-review with checklist
- Run full test suite
- Merge to main

---

## Risk Mitigation

### Risk 1: Breaking Changes

- **Mitigation**: Keep original class as facade
- **Fallback**: Backward-compatible interface

### Risk 2: Test Failures

- **Mitigation**: Run tests after each small change
- **Fallback**: Git revert to last known good state

### Risk 3: Performance Regression

- **Mitigation**: Benchmark before/after
- **Fallback**: Optimize or revert

### Risk 4: Merge Conflicts

- **Mitigation**: Work in feature branch, small commits
- **Fallback**: Rebase frequently

---

## Timeline Estimate

| Phase                         | Duration     | Dependencies |
| ----------------------------- | ------------ | ------------ |
| Phase 1: Extract Helpers      | 3 hours      | None         |
| Phase 2: Eliminate Duplicates | 2 hours      | Phase 1      |
| Phase 3: Split Services       | 4 hours      | Phase 2      |
| Phase 4: Add Tests            | 3 hours      | Phase 3      |
| Phase 5: Documentation        | 1 hour       | Phase 4      |
| **Total**                     | **13 hours** | Sequential   |

---

## Notes for Customization

**You can modify this plan to**:

- Focus on specific phases only (e.g., just Phase 1-2)
- Adjust priority of tasks
- Add/remove specific methods to refactor
- Change target metrics
- Add additional quality checks

**Common Customizations**:

- "Just extract helpers, don't split services" → Skip Phase 3
- "Focus on test coverage only" → Execute Phase 4 only
- "Quick wins only" → Phase 2 (eliminate duplicates) only
- "Full refactoring" → Execute all phases

---

## ⚠️ IMPORTANT: Next Steps

1. **Review this plan** and customize tasks as needed
2. **Edit priorities** if focusing on specific improvements
3. **Reply "EXECUTE"** when ready to proceed with refactoring
4. I will then **systematically execute each task** and make all code improvements

**Status**: ⏳ **Awaiting Your Confirmation to Execute**
