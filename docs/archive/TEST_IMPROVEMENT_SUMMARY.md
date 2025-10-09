# Test Improvement Summary

**Quick reference for test quality improvements**

See [CODE_SIMPLIFICATION_ROADMAP.md](CODE_SIMPLIFICATION_ROADMAP.md) sections 7-11 for full details.

---

## 🚨 Current Problems

### Test Pyramid is Inverted

- **Current**: 39 unit vs 39 integration (1:1 ratio)
- **Target**: 100 unit vs 25 integration vs 15 E2E (4:1:0.6 ratio)
- **Problem**: Too many slow integration tests, not enough fast unit tests

### Tests Coupled to Implementation

- **719 mock usages** across 47 files
- **116 mock assertions** (testing HOW, not WHAT)
- Tests break on refactoring, not behavior changes

### Missing E2E Coverage

- **Backend**: 0 E2E tests
- **Frontend**: 1 E2E test
- Critical user flows not tested end-to-end

### Skipped Tests Hide Problems

- **42 skipped tests** with `@pytest.mark.skip` or `xfail`
- Per CLAUDE.md: Should fail loud, not skip silently

---

## 🎯 Goals

### Proper Test Pyramid

```
    /\
   /E2E\     10-15 tests (5-10%)  - Critical user flows
  /------\
 /  INT   \  20-30 tests (15-20%) - Multiple systems
/----------\
/   UNIT    \ 100+ tests (70-80%) - Single components
/____________\
```

### Test Quality Standards

- ✅ Tests verify **behavior**, not implementation
- ✅ Tests survive **refactoring** without changes
- ✅ Tests are **independent** (run in any order)
- ✅ Tests are **fast** (unit: <50ms, integration: <500ms)
- ✅ Zero **skipped tests** (all pass or deleted)
- ✅ Minimal **mocking** (only external systems)

---

## 🔴 Anti-Patterns to Eliminate

### 1. Testing Private Methods

```python
# ❌ BAD - Breaks on refactoring
def test_internal_cache_management():
    service = VocabService()
    service._update_cache("test")
    assert len(service._cache) == 1
```

```python
# ✅ GOOD - Tests public behavior
def test_word_lookup_returns_cached_result():
    service = VocabService()
    # First call loads from DB
    result1 = service.get_word("Haus", db)
    # Second call should be cached (verify by speed, not implementation)
    result2 = service.get_word("Haus", db)
    assert result1 == result2
```

### 2. Mock Call Counting

```python
# ❌ BAD - Tests implementation
mock_db.save.assert_called_once()
assert mock_service.process.call_count == 3
```

```python
# ✅ GOOD - Tests outcome
result = service.mark_word_known(user_id, "Haus", db)
assert result.success is True

# Verify through public API
word = service.get_word_status(user_id, "Haus", db)
assert word.is_known is True
```

### 3. Excessive Mocking

```python
# ❌ BAD - 5+ mocks = testing implementation
@patch('service.db')
@patch('service.cache')
@patch('service.logger')
@patch('service.event_bus')
@patch('service.validator')
def test_complex_operation(mock_val, mock_event, mock_log, mock_cache, mock_db):
    # Too many mocks = implementation coupled
    ...
```

```python
# ✅ GOOD - Test with real dependencies or minimal mocks
def test_complex_operation(test_db, test_cache):
    # Use real test DB and cache, only mock external APIs
    service = VocabService(test_db, test_cache)
    result = service.process_word("Haus")
    assert result.success is True
```

### 4. Integration Tests as Unit Tests

```python
# ❌ BAD - Labeled "unit" but uses database
# File: tests/unit/test_vocabulary_service.py
async def test_get_word(async_db):
    service = VocabularyService()
    result = await service.get_word("Haus", async_db)  # Uses real DB!
    assert result.word == "Haus"
```

```python
# ✅ GOOD - True unit test
# File: tests/unit/test_vocabulary_service.py
def test_word_validation():
    service = VocabularyService()
    # No DB, no external dependencies
    result = service.validate_word_format("Haus123")
    assert result.is_valid is False
    assert "numbers not allowed" in result.error
```

---

## ✅ Good Patterns

### Unit Test Example

```python
def test_vocabulary_level_calculation():
    """Tests business logic, no external dependencies"""
    calculator = VocabularyLevelCalculator()

    # Test A1 level
    result = calculator.get_level(known_words=50)
    assert result == VocabularyLevel.A1

    # Test A2 level
    result = calculator.get_level(known_words=150)
    assert result == VocabularyLevel.A2
```

### Integration Test Example

```python
@pytest.mark.integration
async def test_vocabulary_persistence(async_db):
    """Tests multiple systems: service + database"""
    service = VocabularyService()

    # Create word
    await service.add_word("Haus", "de", async_db)

    # Verify persistence
    retrieved = await service.get_word("Haus", "de", async_db)
    assert retrieved.word == "Haus"

    # Verify query works
    all_words = await service.search_words("Hau", "de", async_db)
    assert len(all_words) >= 1
```

### E2E Test Example

```typescript
// tests/e2e/vocabulary-learning.spec.ts
test("user can mark word as known and see in progress", async ({ page }) => {
  // Login
  await page.goto("/login");
  await page.fill('[data-testid="email"]', "test@example.com");
  await page.fill('[data-testid="password"]', "password123");
  await page.click('[data-testid="login-button"]');

  // Navigate to vocabulary
  await page.goto("/vocabulary");

  // Mark word as known
  await page.click('[data-testid="word-Haus-mark-known"]');
  await expect(page.locator('[data-testid="word-Haus-status"]')).toHaveText(
    "Known",
  );

  // Check progress
  await page.goto("/progress");
  await expect(page.locator('[data-testid="known-words-count"]')).toContainText(
    "1",
  );
});
```

---

## 📊 Current State Analysis

### Backend Tests (123 files)

| Type        | Current  | Target    | Status                |
| ----------- | -------- | --------- | --------------------- |
| Unit        | 39 (32%) | 100 (70%) | ⚠️ Need 61 more       |
| Integration | 39 (32%) | 25 (18%)  | ⚠️ Convert 14 to unit |
| E2E         | 0 (0%)   | 15 (10%)  | ❌ Need to create     |
| Skipped     | 42       | 0         | ❌ Fix or delete      |

### Frontend Tests (22 files)

| Type      | Current | Target | Status         |
| --------- | ------- | ------ | -------------- |
| Component | 22      | 30     | ⚠️ Need 8 more |
| E2E       | 1       | 10     | ❌ Need 9 more |

### Test Quality Metrics

| Metric              | Current | Target | Status           |
| ------------------- | ------- | ------ | ---------------- |
| Mock usages         | 719     | <100   | ❌ 619 to remove |
| Mock assertions     | 116     | 0      | ❌ All to remove |
| Skipped tests       | 42      | 0      | ❌ Fix or delete |
| Tests with 5+ mocks | ~30     | 0      | ❌ Rewrite       |

---

## 🚀 Action Plan

### Phase 1: Fix Skipped Tests (2 hours)

**Priority**: Immediate - hiding real problems

1. List all skipped tests: `grep -r "@pytest.mark.skip\|xfail" tests/`
2. For each test:
   - Broken due to refactoring? → Fix
   - Flaky/timing? → Fix root cause or delete
   - Performance test? → Move to `tests/manual/`
   - Never worked? → Delete
3. Document any that remain with user approval

**Commands**:

```bash
# Find all skipped tests
grep -r "@pytest.mark.skip" Backend/tests --include="*.py"
grep -r "@pytest.mark.xfail" Backend/tests --include="*.py"
grep -r "pytest.skip(" Backend/tests --include="*.py"

# Run to see which fail
pytest Backend/tests -v --collect-only | grep skip
```

---

### Phase 2: Identify Mock-Heavy Tests (2 hours)

**Priority**: High - indicates implementation coupling

1. Find tests with excessive mocks:

```bash
# Find files with many mocks
grep -r "Mock\|patch" Backend/tests --include="*.py" -c | sort -t: -k2 -nr | head -20

# Find mock assertion patterns
grep -r "assert_called\|call_count" Backend/tests --include="*.py" | wc -l
```

2. Categorize:
   - **Delete**: Tests only verifying mock calls
   - **Rewrite**: Can test behavior instead
   - **Keep**: Essential mocks (external APIs)

---

### Phase 3: Convert Integration to Unit (8-10 hours)

**Priority**: High - improve test speed and clarity

1. Audit `tests/integration/` directory
2. For each test, ask:
   - Does it NEED a database? → Keep as integration
   - Could it test logic without DB? → Convert to unit
   - Does it test multiple systems? → Keep as integration

3. Move tests:

```bash
# Example: vocabulary tests that don't need DB
mv tests/integration/test_vocabulary_validation.py tests/unit/
```

---

### Phase 4: Create E2E Tests (20-25 hours)

**Priority**: Medium - fill coverage gap

**Backend E2E** (6-8 hours):

```bash
mkdir -p Backend/tests/e2e
```

Create tests:

- `test_full_auth_flow.py` - Register, login, refresh token
- `test_video_processing_pipeline.py` - Upload → process → view
- `test_vocabulary_learning_journey.py` - Browse → mark known → progress
- `test_game_session_complete.py` - Start → answer → score

**Frontend E2E** (10-12 hours):
Create Playwright tests:

- `auth-flow.spec.ts` - Full auth journey
- `vocabulary-library.spec.ts` - Browse and filter
- `video-upload.spec.ts` - Upload and processing
- `learning-progress.spec.ts` - Stats and charts

---

## 📏 Testing Standards

### When to Write Each Type

**Unit Test** - Write when:

- ✅ Testing pure functions or business logic
- ✅ No database or external dependencies
- ✅ Fast execution (<50ms)
- ✅ Tests single component in isolation

**Integration Test** - Write when:

- ✅ Testing multiple systems together (service + DB)
- ✅ Testing data persistence
- ✅ Testing transaction behavior
- ✅ Slower execution acceptable (<500ms)

**E2E Test** - Write when:

- ✅ Testing complete user journeys
- ✅ Testing UI interactions
- ✅ Testing frontend + backend together
- ✅ Critical business flows
- ✅ Slow execution acceptable (<5 seconds)

### Test Naming Convention

```python
# Unit tests - describe behavior
def test_vocabulary_level_increases_with_known_words():
    ...

# Integration tests - describe integration
@pytest.mark.integration
async def test_vocabulary_persists_to_database():
    ...

# E2E tests - describe user journey
test('user can complete registration and login', async ({ page }) => {
    ...
});
```

---

## 🎯 Success Criteria

After completing improvements:

- [ ] **Test Pyramid**: 70% unit, 20% integration, 10% E2E
- [ ] **Mock Usage**: <100 mocks total, only for external APIs
- [ ] **Mock Assertions**: Zero `call_count` or `assert_called` checks
- [ ] **Skipped Tests**: Zero skipped tests (all pass or deleted)
- [ ] **E2E Coverage**: 15 critical flows tested
- [ ] **Test Speed**: Unit tests <50ms, Integration <500ms, E2E <5s
- [ ] **Independence**: All tests pass in random order
- [ ] **Behavior Focus**: Tests verify outcomes, not implementation

---

## 📚 Resources

- [Martin Fowler - Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
- [Playwright Documentation](https://playwright.dev/docs/intro)
- [Pytest Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- Internal: [CODE_SIMPLIFICATION_ROADMAP.md](CODE_SIMPLIFICATION_ROADMAP.md) sections 7-11

---

**Quick Links**:

- Full Roadmap: [CODE_SIMPLIFICATION_ROADMAP.md](CODE_SIMPLIFICATION_ROADMAP.md)
- Cleanup Script: [scripts/cleanup_project.sh](scripts/cleanup_project.sh)
- Standards: [CLAUDE.md](CLAUDE.md)

**Total Test Improvement Effort**: 92-116 hours
**Immediate Impact**: Fix 42 skipped tests, establish E2E foundation
