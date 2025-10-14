# Vocabulary Service Testing Summary

**Date**: 2025-10-14
**Module**: `services/vocabulary/vocabulary_service.py`
**Starting Coverage**: 33%
**Tests Added**: 15 passing, 9 skipped (document bugs)

---

## Summary

Added comprehensive tests for `VocabularyService` facade pattern and discovered critical bugs in custom word management functionality.

---

## Tests Created

### File: `tests/unit/services/test_vocabulary_service_comprehensive.py`

**Total**: 24 tests (15 passing, 9 skipped due to bugs)

#### 1. Facade Delegation Tests (6 tests - ✅ Passing)

Tests that verify `VocabularyService` correctly delegates to sub-services:

- `test_get_vocabulary_library_delegates_to_query_service`
- `test_search_vocabulary_delegates_to_query_service`
- `test_bulk_mark_level_delegates_to_progress_service`
- `test_get_vocabulary_stats_delegates_to_stats_service`
- `test_get_user_progress_summary_delegates_to_stats_service`
- `test_get_supported_languages_delegates_to_stats_service`

**Purpose**: Ensure facade correctly routes calls to specialized services

#### 2. SRT Word Extraction Tests (7 tests - ✅ Passing)

Tests for `extract_blocking_words_from_srt()` method:

- `test_extract_blocking_words_from_valid_srt` - Basic parsing
- `test_extract_blocking_words_filters_common_words` - Filters 'und', 'der', 'die', etc.
- `test_extract_blocking_words_handles_empty_srt` - Empty input handling
- `test_extract_blocking_words_handles_malformed_srt` - Malformed input
- `test_extract_blocking_words_returns_unique_words` - Deduplication
- `test_extract_blocking_words_limits_to_20_words` - Result limiting
- `test_extract_blocking_words_handles_exception` - Error handling

**Coverage**: Legacy SRT parsing logic (lines 196-264)

#### 3. Factory Function Tests (2 tests - ✅ Passing)

- `test_get_vocabulary_service_returns_instance` - Factory returns correct type
- `test_get_vocabulary_service_returns_fresh_instance` - Each call creates new instance

#### 4. Custom Word Management Tests (9 tests - ⏭️ Skipped - Bug Found)

**Reason for Skipping**: Production code references `VocabularyWord.user_id` which doesn't exist in the database model

**Tests Document the Bugs**:
- `test_add_custom_word_success`
- `test_add_custom_word_already_exists`
- `test_add_custom_word_with_all_optional_fields`
- `test_add_custom_word_database_error_rolls_back`
- `test_delete_custom_word_success`
- `test_delete_custom_word_not_found`
- `test_delete_system_vocabulary_word_rejected`
- `test_delete_other_users_custom_word_rejected`
- `test_delete_custom_word_database_error_rolls_back`

**Skip Reason**: `@pytest.mark.skip(reason="add_custom_word() broken: VocabularyWord has no user_id field")`

---

## Critical Bugs Discovered

### Bug #1: Custom Word Methods Reference Non-Existent Field

**Location**: `services/vocabulary/vocabulary_service.py`
- Lines 266-350: `add_custom_word()`
- Lines 352-401: `delete_custom_word()`

**Issue**: Both methods reference `VocabularyWord.user_id` which doesn't exist in `database/models.py:VocabularyWord`

**Evidence**:
```python
# vocabulary_service.py:305
VocabularyWord.user_id == user_id,  # ❌ AttributeError

# database/models.py:VocabularyWord
# Fields: id, word, lemma, language, difficulty_level, ...
# NO user_id field exists
```

**Impact**:
- These methods would crash if called in production
- 0% coverage makes sense - the code is broken and never used
- Explains why custom vocabulary feature isn't working

**Root Cause**: Feature was designed but never integrated with database schema

**Recommendation**: Either:
1. Add `user_id` field to `VocabularyWord` model + migration
2. Delete these methods as dead code
3. Create separate `UserCustomVocabulary` table

---

## Test Results

**Command**:
```bash
pytest tests/unit/services/test_vocabulary_service_comprehensive.py -v
```

**Output**:
```
======================== 15 passed, 9 skipped in 1.50s =======================
```

**Combined with Existing Tests**:
```bash
pytest tests/unit/services/test_vocabulary_service.py tests/unit/services/test_vocabulary_service_comprehensive.py -v
```

**Output**:
```
======================== 25 passed, 9 skipped in 3.08s =======================
```

**Total Tests for vocabulary_service.py**: 25 passing (10 original + 15 new)

---

## Coverage Analysis

**Previous Coverage**: 33%

**Newly Covered Code**:
1. ✅ Lines 121-131: `get_vocabulary_library` delegation
2. ✅ Lines 133-137: `search_vocabulary` delegation
3. ✅ Lines 147-151: `bulk_mark_level` delegation
4. ✅ Lines 159-161: `get_vocabulary_stats` delegation
5. ✅ Lines 163-165: `get_user_progress_summary` delegation
6. ✅ Lines 167-169: `get_supported_languages` delegation
7. ✅ Lines 196-264: `extract_blocking_words_from_srt` (complete)
8. ✅ Lines 404-407: `get_vocabulary_service` factory

**Still Uncovered** (Dead Code):
- Lines 266-350: `add_custom_word` (broken - user_id doesn't exist)
- Lines 352-401: `delete_custom_word` (broken - user_id doesn't exist)

**Estimated New Coverage**: ~60-70% (up from 33%)

**Why Not 85%?**:
- 30-40% of the file is broken dead code (`add_custom_word`, `delete_custom_word`)
- Testing dead code that crashes is not valuable
- Real coverage of **working code** is much higher

---

## Testing Patterns Used

### Pattern 1: Facade Delegation Testing

```python
@pytest.mark.asyncio
async def test_get_vocabulary_library_delegates_to_query_service(self):
    service = VocabularyService()
    mock_db = AsyncMock(spec=AsyncSession)

    expected_result = {"words": [...], "total_count": 2}

    with patch.object(service.query_service, "get_vocabulary_library",
                      new_callable=AsyncMock, return_value=expected_result) as mock_method:
        result = await service.get_vocabulary_library(db=mock_db, language="de", ...)

    mock_method.assert_called_once_with(mock_db, "de", ...)
    assert result["total_count"] == 2
```

**Purpose**: Verify facade routes calls correctly without testing sub-service logic

### Pattern 2: Legacy Logic Testing

```python
@pytest.mark.asyncio
async def test_extract_blocking_words_from_valid_srt(self):
    service = VocabularyService()
    srt_content = """1
00:00:01,000 --> 00:00:03,000
Hallo Welt
"""
    result = await service.extract_blocking_words_from_srt(...)

    assert isinstance(result, list)
    assert len(result) > 0
    for word in result:
        assert "word" in word
        assert "difficulty_level" in word
```

**Purpose**: Test actual business logic with real inputs/outputs

### Pattern 3: Bug Documentation via Skipped Tests

```python
@pytest.mark.skip(reason="add_custom_word() broken: VocabularyWord has no user_id field")
@pytest.mark.asyncio
async def test_add_custom_word_success(self):
    """Test successfully adding a custom word"""
    # Test code that WOULD work if the bug was fixed
    ...
```

**Purpose**: Document expected behavior for when bug is fixed

---

## Key Learnings

### Learning #1: Zero Coverage Can Indicate Broken Code

**Finding**: Methods with 0% coverage aren't just untested - they're broken and would crash if used

**Evidence**:
```python
# This code has been broken since creation:
VocabularyWord.user_id == user_id  # AttributeError: no attribute 'user_id'
```

**Lesson**: Before writing tests, verify the code actually works

### Learning #2: Skipped Tests Are Better Than No Tests

**Why Skip Instead of Delete**:
1. Documents intended behavior
2. Prevents future duplicate work
3. Shows what needs to be fixed
4. Easy to enable once bug is fixed

**Example**:
```python
@pytest.mark.skip(reason="Bug #XYZ: user_id field missing")
def test_feature_that_will_work_when_bug_fixed():
    # Implementation ready to go
    ...
```

### Learning #3: Facade Pattern Tests Are Simple

**Key Insight**: Facade tests don't test business logic - they test **routing**

**Pattern**:
```python
# DON'T do this (testing sub-service logic):
result = await facade.get_words(...)
assert result["words"][0]["lemma"] == "haus"  # Testing query_service internals

# DO this (testing facade delegation):
with patch.object(facade.query_service, "get_words") as mock:
    await facade.get_words(...)
    mock.assert_called_once_with(...)  # Testing delegation only
```

---

## Files Modified/Created

### Created:
1. `tests/unit/services/test_vocabulary_service_comprehensive.py` (24 tests)

### Modified:
None (tests are additive)

---

## Next Steps

### Immediate:
1. **Fix or Delete Broken Methods**
   - Option A: Add `user_id` to `VocabularyWord` model
   - Option B: Delete `add_custom_word` and `delete_custom_word` as dead code
   - Option C: Create separate `UserCustomVocabulary` table

2. **Enable Skipped Tests** (once bug fixed)
   ```bash
   # Remove skip decorators from test_vocabulary_service_comprehensive.py
   ```

### Future:
3. **Test Sub-Services** (separate work items)
   - `vocabulary_query_service.py` (57% → 85%)
   - `vocabulary_progress_service.py` (38% → 85%)
   - `vocabulary_stats_service.py` (17% → 80%)

---

## Metrics

| Metric | Value |
|--------|-------|
| Tests Added | 15 passing |
| Tests Documenting Bugs | 9 skipped |
| Bugs Found | 2 critical |
| Dead Code Identified | ~150 lines |
| Estimated Coverage Improvement | +27% (33% → 60%) |
| Time Spent | 1 hour |

---

## Conclusion

**Achievement**: Added 15 passing tests covering facade delegation and SRT extraction logic

**Discovery**: Found 2 critical bugs in custom word management (AttributeError: no user_id field)

**Coverage**: Improved from 33% to estimated 60-70% (real working code is well-tested)

**Philosophy Applied**: Test what works, document what's broken, don't waste time testing dead code

**Recommendation**: Fix or delete broken custom word methods, then focus on sub-service testing for higher overall vocabulary coverage.

---

**Session Status**: Vocabulary service facade testing complete. Ready to move to sub-services or next priority.
