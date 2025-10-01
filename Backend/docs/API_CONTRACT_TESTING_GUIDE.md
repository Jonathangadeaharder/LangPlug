# API Contract Testing Guide

## The Problem We Discovered (Multiple Times!)

**All tests passed. Production crashed. Again. And again.**

This happened **THREE TIMES** with progressively better tests:

### Round 1: Bug #6 - Field Name Mismatch

```
✅ Unit tests: All passing
✅ Integration tests: All passing
✅ Service tests: All passing
❌ User experience: React app crashed with "Cannot read properties of undefined (reading 'toLowerCase')"
```

**Backend returned:**

```python
{
    "word": "Hallo",
    "difficulty": "A1",  # ❌ Wrong field name
    "active": True
}
```

**Frontend expected:**

```typescript
interface VocabularyWord {
  word: string;
  difficulty_level: string; // ✅ Correct field name (required!)
  // ... other fields
}
```

**Result**: React component tried to access `word.difficulty_level` → got `undefined` → tried to call `.toLowerCase()` → CRASH

---

### Round 2: Bug #7 - Field Value is None

**After fixing Bug #6, we added field name validation tests. Tests passed again. Production crashed again.**

```
✅ Tests validate field names are correct
✅ Tests check field exists
❌ Tests don't check field VALUES
❌ User experience: 39 Pydantic serialization warnings, frontend still broken
```

**Backend returned:**

```python
{
    "concept_id": None,  # ❌ Field exists but value is None!
    "word": "glücklich",
    "difficulty_level": "C2"
}
```

**Pydantic warning:**

```
PydanticSerializationUnexpectedValue: Expected `VocabularyWord` - serialized value may not be as expected
[input_value={'concept_id': None, ...}]
```

**Why tests didn't catch it:**

```python
# What our tests checked
assert "concept_id" in word  # ✅ Field exists
assert isinstance(word["concept_id"], str)  # ✅ Type is correct (when not None)

# What our tests SHOULD have checked
assert word["concept_id"] is not None  # ❌ MISSING!
```

---

### Round 3: Bug #8 - Field Value Wrong Format

**After fixing field names AND checking for None, tests passed again. Production crashed AGAIN.**

```
✅ Tests validate field names correct
✅ Tests validate field values not None
❌ Tests don't validate field VALUE FORMAT
❌ User experience: 422 Unprocessable Content when marking words as known
```

**Backend returned:**

```python
{
    "concept_id": "glücklich-C2",  # ❌ Not a valid UUID!
    "word": "glücklich",
    "difficulty_level": "C2"
}
```

**API validation error:**

```python
# api/routes/vocabulary.py:25-33
@field_validator('concept_id')
@classmethod
def validate_concept_id(cls, v):
    try:
        uuid.UUID(v)  # ❌ FAILS - "glücklich-C2" is not valid UUID format
        return v
    except ValueError:
        raise ValueError('concept_id must be a valid UUID')
```

**Frontend error:**

```
POST /api/vocabulary/mark-known
Response: 422 Unprocessable Content
Body: {"detail": "Value error, concept_id must be a valid UUID"}
```

**Why tests didn't catch it:**

```python
# What our tests checked
assert word["concept_id"] is not None  # ✅ Not None
assert isinstance(word["concept_id"], str)  # ✅ Is string

# What our tests SHOULD have checked
try:
    uuid.UUID(word["concept_id"])  # ❌ MISSING! Would have caught invalid format
except ValueError:
    pytest.fail("concept_id is not valid UUID")
```

---

## The Pattern: Progressive Test Inadequacy

Each round, we added better tests. Each round, they still weren't good enough:

| Round | Bug                  | What Tests Checked                | What Tests Missed                     | Why Production Crashed                                           |
| ----- | -------------------- | --------------------------------- | ------------------------------------- | ---------------------------------------------------------------- |
| **1** | #6: Wrong field name | Services instantiate              | Field names match frontend            | React tried `word.difficulty_level.toLowerCase()` on `undefined` |
| **2** | #7: Value is None    | Field names correct, field exists | Field values are not None             | Pydantic serialization warnings, frontend got `None`             |
| **3** | #8: Invalid format   | Field not None, type is string    | Field format matches API expectations | API validation rejected non-UUID string                          |

### The Core Problem: Test Quality Layers

**Layer 1: Existence** (Caught by traditional tests)

```python
assert service is not None  # ✅ Service exists
assert "concept_id" in word  # ✅ Field exists
```

**Layer 2: Structure** (Caught by Round 1 tests)

```python
assert "difficulty_level" in word  # ✅ Correct field name
assert "difficulty" not in word  # ✅ Wrong field name absent
```

**Layer 3: Values** (Caught by Round 2 tests)

```python
assert word["concept_id"] is not None  # ✅ Has value
assert isinstance(word["concept_id"], str)  # ✅ Correct type
```

**Layer 4: Value Format** (Caught by Round 3 tests - WHAT WE NEEDED!)

```python
try:
    uuid.UUID(word["concept_id"])  # ✅ Valid UUID format
except ValueError:
    pytest.fail("Invalid UUID format")
```

**Layer 5: Complete User Flow** (What we should test next!)

```python
# Test the COMPLETE flow that users experience:
# 1. Process chunk → 2. Get vocabulary → 3. Mark word as known
vocabulary = await process_chunk(...)
response = await mark_word_known(vocabulary[0]["concept_id"])
assert response.status_code == 200  # Not 422!
```

---

## Why Traditional Tests Missed This

### ❌ What We Had

**Unit Tests**: Verified services instantiate

```python
def test_service_exists():
    service = VocabularyFilterService()
    assert service is not None  # ✅ Passes (but useless)
```

**Integration Tests**: Verified methods can be called

```python
def test_extract_vocabulary():
    result = service.extract_vocabulary_from_result(data)
    assert len(result) > 0  # ✅ Passes (but doesn't check structure)
```

**Problem**: None of these tests validated the **data structure** matched what the frontend expected.

---

## The Solution: API Contract Validation Tests

### ✅ What We Need

**Contract Validation Tests**: Verify response structure matches frontend types

```python
def test_vocabulary_matches_frontend_type():
    """Test that backend response matches frontend VocabularyWord interface"""
    service = VocabularyFilterService()
    vocabulary = service.extract_vocabulary_from_result(filter_result)

    for word in vocabulary:
        # Verify EXACT field names from TypeScript interface
        assert "word" in word
        assert "difficulty_level" in word  # Not "difficulty"!
        assert "concept_id" in word

        # Verify required fields are not null
        assert word["word"] is not None
        assert word["difficulty_level"] is not None
        assert word["concept_id"] is not None

        # Catch wrong field names
        assert "difficulty" not in word  # ⭐ This catches the bug!

        # Verify types
        assert isinstance(word["word"], str)
        assert isinstance(word["difficulty_level"], str)
```

This test would have **FAILED immediately** with the buggy code.

---

## API Contract Testing Principles

### 1. Test Against TypeScript Types

**Bad**: Test what you think the API should return

```python
def test_api_response():
    result = api.get_vocabulary()
    assert "word" in result  # Which fields? What types?
```

**Good**: Test against actual frontend TypeScript interface

```python
def test_api_matches_typescript():
    """
    Validate against frontend type:
    interface VocabularyWord {
        concept_id: string;
        word: string;
        difficulty_level: string;  // required!
        translation?: string | null;  // optional
    }
    """
    result = api.get_vocabulary()

    # Required fields (non-optional in TypeScript)
    assert "concept_id" in result
    assert result["concept_id"] is not None

    # Optional fields (can be null but must exist)
    assert "translation" in result
    # translation can be None, but key must exist
```

### 2. Test Field Names Exactly

**Bad**: Generic structure check

```python
assert len(result) > 0  # Doesn't validate field names
```

**Good**: Explicit field name validation

```python
# Test exact field names from TypeScript
required_fields = ["concept_id", "word", "difficulty_level"]
for field in required_fields:
    assert field in result, f"Missing required field: {field}"

# Test NO wrong field names
wrong_fields = ["difficulty", "level", "concept"]  # Common mistakes
for field in wrong_fields:
    assert field not in result, f"Wrong field name: {field}"
```

### 3. Test the Complete Data Pipeline

**Bad**: Test each layer independently

```python
def test_service():
    result = service.method()
    assert result  # Service works

def test_api():
    response = api.endpoint()
    assert response  # API works
```

**Good**: Test the full flow end-to-end

```python
def test_complete_pipeline():
    # Simulate full request/response cycle
    subtitles = process_subtitles(...)
    filter_result = filter_service.process(subtitles)
    vocabulary = extract_vocabulary(filter_result)

    # Validate final output matches frontend expectations
    assert_matches_typescript_interface(vocabulary)
```

### 4. Test What Users See

**Bad**: Test internal implementation

```python
def test_internal_method():
    internal_data = service._internal_method()
    assert internal_data["some_field"]  # Users never see this
```

**Good**: Test user-facing data

```python
def test_user_facing_api():
    # Test the EXACT data structure that reaches the frontend
    response = api.get_vocabulary()

    # Can a React component safely use this data?
    for word in response:
        # This is what React does:
        level = word["difficulty_level"]
        display = level.lower()  # Would crash if undefined!

    assert True  # If we get here, React won't crash
```

---

## How to Write API Contract Tests

### Step 1: Find the Frontend TypeScript Interface

```typescript
// Frontend: src/client/types.gen.ts
export type VocabularyWord = {
  concept_id: string;
  word: string;
  translation?: string | null;
  lemma?: string | null;
  difficulty_level: string; // Required!
  semantic_category?: string | null;
  domain?: string | null;
};
```

### Step 2: Create Backend Test That Validates This Exact Structure

```python
# Backend: tests/integration/test_api_contract_validation.py
def test_vocabulary_word_matches_typescript_interface():
    """
    Validate backend response matches:
    Frontend/src/client/types.gen.ts :: VocabularyWord
    """
    service = VocabularyFilterService()
    vocabulary = service.extract_vocabulary(...)

    word = vocabulary[0]

    # Required fields (no ? in TypeScript)
    assert word["concept_id"]  # string
    assert word["word"]  # string
    assert word["difficulty_level"]  # string (NOT optional!)

    # Optional fields (? in TypeScript)
    assert "translation" in word  # Must exist (can be None)
    assert "lemma" in word
    assert "semantic_category" in word
    assert "domain" in word

    # Type validation
    assert isinstance(word["concept_id"], str)
    assert isinstance(word["word"], str)
    assert isinstance(word["difficulty_level"], str)

    # Optional fields can be None
    assert word["translation"] is None or isinstance(word["translation"], str)
```

### Step 3: Test Against Common Mistakes

```python
def test_no_common_field_name_mistakes():
    """Test for common API contract mistakes"""
    vocabulary = get_vocabulary_response()

    for word in vocabulary:
        # Common mistakes
        assert "difficulty" not in word  # Should be difficulty_level
        assert "level" not in word  # Should be difficulty_level
        assert "concept" not in word  # Should be concept_id
        assert "id" not in word  # Should be concept_id (unless that's the actual field)

        # Ensure correct names exist
        assert "difficulty_level" in word
        assert "concept_id" in word
```

---

## Real Example: The Bug We Fixed

### Before (Buggy Code)

```python
# Backend: vocabulary_filter_service.py
def extract_vocabulary_from_result(self, filter_result):
    return [
        {
            "word": word.word,
            "difficulty": getattr(word, "difficulty_level", "unknown"),  # ❌ Wrong field name!
            "active": True,
        }
        for word in filter_result.get("blocking_words", [])
    ]
```

**Test that would have caught this:**

```python
def test_bug_6_difficulty_vs_difficulty_level():
    service = VocabularyFilterService()
    vocabulary = service.extract_vocabulary_from_result(filter_result)

    # This assertion FAILS with buggy code
    assert "difficulty_level" in vocabulary[0]  # ❌ FAIL - field is "difficulty"
    assert "difficulty" not in vocabulary[0]  # ❌ FAIL - wrong field exists!
```

### After (Fixed Code)

```python
# Backend: vocabulary_filter_service.py
def extract_vocabulary_from_result(self, filter_result):
    return [
        {
            # Match frontend TypeScript interface exactly
            "concept_id": getattr(word, "concept_id", f"word_{word.word}"),
            "word": word.word,
            "difficulty_level": getattr(word, "difficulty_level", "unknown"),  # ✅ Correct!
            "translation": getattr(word, "translation", None),
            "lemma": getattr(word, "lemma", None),
            "semantic_category": getattr(word, "part_of_speech", None),
            "domain": None,
            "active": True,
        }
        for word in filter_result.get("blocking_words", [])
    ]
```

**Test now passes:**

```python
def test_bug_6_difficulty_vs_difficulty_level():
    service = VocabularyFilterService()
    vocabulary = service.extract_vocabulary_from_result(filter_result)

    assert "difficulty_level" in vocabulary[0]  # ✅ PASS
    assert "difficulty" not in vocabulary[0]  # ✅ PASS
```

---

## Testing Checklist

When writing API contract tests:

- [ ] ✅ Test against actual TypeScript interface (copy it into test docstring)
- [ ] ✅ Validate ALL required fields are present and non-null
- [ ] ✅ Validate optional fields exist (can be null)
- [ ] ✅ Test field names exactly match TypeScript
- [ ] ✅ Test for common wrong field names
- [ ] ✅ Validate field types (string, number, etc.)
- [ ] ✅ Test the complete data pipeline from service to API
- [ ] ✅ Test what users actually see, not internal details
- [ ] ❌ Don't mock the response structure
- [ ] ❌ Don't just check that "something" is returned
- [ ] ❌ Don't test implementation details

---

## Summary

### The Problem

**Services worked. Methods existed. Data flowed. But the field was named wrong → React crashed.**

### The Solution

**API Contract Validation Tests** that:

1. Validate response structure matches frontend TypeScript types
2. Test exact field names (not just existence)
3. Exercise complete data pipeline
4. Test what users see, not internal implementation

### The Result

**6 tests that would have caught the bug immediately**

### Key Insight

> **"If your tests don't validate the API contract, they're not testing what matters to users."**

All the service tests in the world are useless if the data structure is wrong when it reaches the frontend.
