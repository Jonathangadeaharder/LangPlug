# Implementation Coupling Elimination Guide

## Overview

This document outlines the systematic elimination of implementation coupling from unit tests to improve maintainability, refactorability, and test reliability.

## Problems with Implementation Coupling

### Identified Anti-Patterns

#### 1. Mock Call Assertion Testing

```python
# BAD: Testing implementation details
mock_session.add.assert_called_once()
mock_session.commit.assert_called_once()
assert mock_session.add.call_count == 3
mock_session.delete.assert_called_once_with(mock_progress)
```

**Problems**:

- Tests break when implementation changes (even if behavior stays same)
- Focuses on "how" instead of "what"
- Creates brittle tests that resist refactoring
- Makes code harder to improve without breaking tests

#### 2. Private Method Testing

```python
# BAD: Testing private implementation
result = await service._get_user_known_concepts(1, "de")
```

**Problems**:

- Couples tests to internal structure
- Private methods are implementation details that should change freely
- Prevents refactoring internal structure
- Tests don't reflect actual usage patterns

#### 3. Complex Mock Setup Chains

```python
# BAD: Hard-coding precise execution sequence
mock_session.execute.side_effect = [
    MagicMock(scalar=lambda: 100),  # A1 total
    MagicMock(scalar=lambda: 20),   # A1 known
    MagicMock(scalar=lambda: 150),  # A2 total
    # ... 10 more specific mock configurations
]
```

**Problems**:

- Tests become coupled to exact query sequence
- Harmless database query optimization breaks tests
- Difficult to understand what behavior is being tested
- Setup code is longer and more complex than the actual test

#### 4. Infrastructure Mock Introspection

```python
# BAD: Testing mock internal state
mock_result.scalars.return_value.all.return_value = [mock_data]
mock_session.execute.return_value = mock_result
```

**Problems**:

- Tests know too much about ORM/database layer structure
- Changes to database abstraction break unrelated tests
- Tests become database-implementation specific

## Solution: Behavior-Focused Testing

### Core Principles

#### 1. Test Observable Behavior, Not Implementation

```python
# GOOD: Testing what the service does
@pytest.mark.anyio
async def test_When_concept_marked_known_Then_user_progress_updated(self, service, repository):
    # Arrange
    user_id = "test-user"
    concept_id = str(uuid4())

    # Initially user doesn't know concept
    assert not repository.is_concept_known_by_user(user_id, concept_id)

    # Act
    result = await service.mark_concept_known(user_id, concept_id, True)

    # Assert - test the observable outcome
    assert result["success"] is True
    assert result["concept_id"] == concept_id
    assert result["known"] is True

    # Verify behavior change occurred
    assert repository.is_concept_known_by_user(user_id, concept_id)
```

#### 2. Use Test Doubles That Model Behavior

```python
# GOOD: Behavior-focused test double
class MockVocabularyRepository:
    def __init__(self):
        self.user_progress = {}  # user_id -> set of known concepts

    def mark_user_knows_concept(self, user_id: str, concept_id: str):
        if user_id not in self.user_progress:
            self.user_progress[user_id] = set()
        self.user_progress[user_id].add(concept_id)

    def is_concept_known_by_user(self, user_id: str, concept_id: str) -> bool:
        return user_id in self.user_progress and concept_id in self.user_progress[user_id]
```

#### 3. Test Public API Only

```python
# GOOD: Testing only public interface
async def test_When_vocabulary_stats_requested_Then_correct_totals_returned(self, service):
    # Only interact with public methods
    result = await service.get_vocabulary_stats("de", "es", user_id="test")

    # Assert on public contract
    assert result["target_language"] == "de"
    assert result["translation_language"] == "es"
    assert "total_words" in result
    assert "total_known" in result
```

#### 4. Focus on State Changes and Return Values

```python
# GOOD: Testing state changes and outputs
async def test_When_user_marks_multiple_concepts_Then_stats_reflect_progress(self, service, repository):
    user_id = "test-user"

    # Get initial stats
    initial_stats = await service.get_vocabulary_stats("de", "es", user_id=user_id)
    initial_known = initial_stats["total_known"]

    # Mark concept as known
    concept_id = str(uuid4())
    await service.mark_concept_known(user_id, concept_id, True)

    # Verify stats changed
    updated_stats = await service.get_vocabulary_stats("de", "es", user_id=user_id)
    assert updated_stats["total_known"] == initial_known + 1
```

## Refactoring Strategy

### Step 1: Identify Coupling Patterns

Search for these anti-patterns:

- `.assert_called_once()`
- `.call_count`
- `._private_method()`
- Complex `side_effect` chains
- Mock setup longer than actual test

### Step 2: Create Behavior-Focused Test Doubles

Instead of mocking infrastructure:

```python
# Replace this pattern:
mock_session = AsyncMock()
mock_session.execute.side_effect = [...]

# With this pattern:
class MockRepository:
    def __init__(self):
        self.data = {}

    def store_item(self, key, value):
        self.data[key] = value

    def retrieve_item(self, key):
        return self.data.get(key)
```

### Step 3: Test State Changes and Outputs

```python
# Replace assertion testing:
mock_session.add.assert_called_once()

# With behavior verification:
# Before action
initial_count = len(repository.get_all_items())

# Action
await service.add_item(new_item)

# After action - verify behavior
final_count = len(repository.get_all_items())
assert final_count == initial_count + 1
```

### Step 4: Use Data Builders for Complex Setup

```python
# Replace complex mock chains with data builders
user = UserBuilder().with_username("testuser").as_admin().build()
concepts = TestDataSets.create_german_vocabulary_set()
```

### Step 5: Test Edge Cases Through Public Interface

```python
# Test error conditions through public methods
async def test_When_invalid_concept_id_provided_Then_appropriate_error_returned(self, service):
    result = await service.mark_concept_known("user", "invalid-uuid", True)
    assert result["success"] is False
    assert "error" in result
```

## Benefits of Behavior-Focused Testing

### Maintainability

- **Refactoring Freedom**: Internal implementation can change without breaking tests
- **Clear Intent**: Tests document what the code should do, not how it does it
- **Reduced Brittleness**: Tests survive harmless implementation changes

### Reliability

- **Deterministic**: Tests focus on predictable state changes
- **No Race Conditions**: No timing dependencies on mock call order
- **Clear Failure Modes**: When tests fail, it's clear what behavior broke

### Design Quality

- **Better APIs**: Writing behavior-focused tests often reveals API design issues
- **Looser Coupling**: Reduces coupling between components
- **Easier Testing**: Well-designed public interfaces are easier to test

## Migration Checklist

### For Each Coupled Test:

- [ ] Identify what behavior the test is trying to verify
- [ ] Remove all `.assert_called_*` and `.call_count` assertions
- [ ] Replace mock setup with behavior-focused test doubles
- [ ] Test only through public API methods
- [ ] Verify actual state changes or return values
- [ ] Ensure test survives reasonable refactoring scenarios

### Quality Gates:

- [ ] No tests call private methods (methods starting with `_`)
- [ ] No tests assert on mock call counts or call arguments
- [ ] All test setup focuses on input data, not mock configuration
- [ ] All assertions focus on outputs and observable state changes
- [ ] Tests pass even if internal implementation details change

## Common Refactoring Patterns

### Pattern 1: Database Call Testing

```python
# Before: Implementation coupling
mock_session.execute.assert_called_once()
mock_session.commit.assert_called_once()

# After: Behavior verification
user_exists = await service.user_exists(user_id)
assert user_exists is True
```

### Pattern 2: Complex Mock Chains

```python
# Before: Complex mock setup
mock_session.execute.side_effect = [
    MagicMock(scalar=lambda: 100),
    MagicMock(scalar=lambda: 20),
    # ... many more
]

# After: Simple data setup
repository.add_concepts_for_level("A1", count=100)
repository.mark_user_knows_concepts(user_id, count=20)
```

### Pattern 3: Private Method Testing

```python
# Before: Testing private methods
result = await service._get_user_known_concepts(user_id)

# After: Testing through public interface
stats = await service.get_vocabulary_stats("de", "en", user_id=user_id)
assert stats["total_known"] > 0
```

## Exception Cases

### When Mock Assertions Are Appropriate

1. **Integration Points**: Testing that external services are called correctly
2. **Side Effects**: When the primary value is in the side effect, not the return
3. **Infrastructure**: Testing that infrastructure components are used correctly

### Examples of Appropriate Mock Testing

```python
# Testing external service integration
email_service = Mock()
await user_service.register_user(user_data)
email_service.send_welcome_email.assert_called_once_with(user_data["email"])

# Testing logging/monitoring
logger = Mock()
await service.process_critical_operation()
logger.error.assert_called_once()  # Ensuring errors are logged
```

The key is that these are testing the **interaction contract** with external systems, not internal implementation details.

## Results

### Before Refactoring

- Tests break when internal database queries are optimized
- 40+ lines of mock setup for simple behavior tests
- Tests fail when private methods are renamed or refactored
- Difficult to understand what behavior is being tested

### After Refactoring

- Tests survive major internal refactoring
- 10-15 lines of clear, intent-revealing test code
- Tests document expected behavior clearly
- Easy to add new test cases for edge conditions
