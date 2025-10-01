# Testing Quick Reference

**Last Updated**: 2025-09-29
**Test Status**: ✅ 96/96 passing (100%)

---

## Quick Test Execution

### Run All Architecture Tests

```bash
cd Backend
powershell.exe -Command ". api_venv/Scripts/activate; python -m pytest tests/unit/core/test_service_container_thread_safety.py tests/unit/dtos/test_vocabulary_dto_validation.py tests/unit/services/test_chunk_processing_resource_management.py -v"
```

### Run Individual Test Suites

```bash
# ServiceContainer (17 tests)
pytest tests/unit/core/test_service_container_thread_safety.py -v

# DTO Validation (59 tests)
pytest tests/unit/dtos/test_vocabulary_dto_validation.py -v

# Chunk Processing (20 tests)
pytest tests/unit/services/test_chunk_processing_resource_management.py -v
```

### With Coverage

```bash
pytest tests/unit/core/test_service_container_thread_safety.py \
       tests/unit/dtos/test_vocabulary_dto_validation.py \
       tests/unit/services/test_chunk_processing_resource_management.py \
       --cov=core --cov=api/dtos --cov=services/processing \
       --cov-report=term-missing --cov-report=html
```

### View Coverage Report

```bash
start Backend/htmlcov/index.html  # Windows
open Backend/htmlcov/index.html   # macOS
xdg-open Backend/htmlcov/index.html  # Linux
```

---

## Test Files Location

```
Backend/tests/unit/
├── core/
│   └── test_service_container_thread_safety.py    (17 tests)
├── dtos/
│   └── test_vocabulary_dto_validation.py          (59 tests)
└── services/
    └── test_chunk_processing_resource_management.py (20 tests)
```

---

## Coverage Summary

| Component           | File                                                 | Coverage | Tests  |
| ------------------- | ---------------------------------------------------- | -------- | ------ |
| ServiceContainer    | `core/service_container.py`                          | 81%      | 17     |
| Vocabulary DTOs     | `api/dtos/vocabulary_dto.py`                         | 97%      | 59     |
| Chunk Transcription | `services/processing/chunk_transcription_service.py` | 84%      | 20     |
| **Average**         | -                                                    | **87%**  | **96** |

---

## What's Tested

### Thread Safety ✅

- Concurrent singleton access (20 threads)
- Service creation race conditions
- High concurrency (100 threads)
- Double-check locking
- RLock reentrant behavior

### Security ✅

- SQL injection prevention
- XSS prevention
- Query sanitization
- Character whitelisting
- Length limits

### Resource Management ✅

- FFmpeg timeout (600s)
- Process killing
- Temporary file cleanup
- Original file protection
- Graceful error handling

### Input Validation ✅

- CEFR levels (A1-C2)
- Language codes (10 languages)
- Range constraints
- Optional fields
- Pagination limits

---

## Common Issues & Solutions

### Issue: Tests Fail in WSL

**Solution**: Use PowerShell wrapper

```bash
powershell.exe -Command ". api_venv/Scripts/activate; python -m pytest ..."
```

### Issue: Coverage Too Low

**Reason**: Measuring against entire codebase (26%)
**Solution**: These tests target specific components (87% in tested areas)

### Issue: Import Errors

**Solution**: Ensure virtual environment is activated

```bash
cd Backend
. api_venv/Scripts/activate  # Linux/macOS
api_venv\Scripts\activate    # Windows
```

### Issue: Async Test Warnings

**Expected**: Some RuntimeWarnings about unawaited coroutines in mock cleanup
**Impact**: None - tests still pass, warnings are from test infrastructure

---

## Test Quality Checklist

When writing new tests, ensure:

✅ **Observable Behavior**: Test outcomes, not implementation
✅ **Specific Assertions**: Assert exact values, not ranges
✅ **No Mock Counting**: Don't use `mock.assert_called_once()` as primary assertion
✅ **No Hard-coded Paths**: Use `Path()` and `tempfile`
✅ **No Array Indices**: Use semantic selectors
✅ **Proper Async**: Use `AsyncMock()` for async methods
✅ **Descriptive Names**: Use When-Then pattern

---

## Documentation Index

1. **TESTING_COMPLETION_SUMMARY.md** - High-level overview, all fixes
2. **TESTING_FINAL_REPORT.md** - Executive summary, production readiness
3. **TESTING_COVERAGE_REPORT.md** - Component coverage, quality metrics
4. **TESTING_IMPLEMENTATION_SUMMARY.md** - Detailed implementation notes
5. **TESTING_QUICK_REFERENCE.md** - This file (quick commands)

---

## Key Metrics

- **Total Tests**: 96
- **Pass Rate**: 100%
- **Execution Time**: ~2 seconds
- **Coverage (tested)**: 87%
- **Failures**: 0
- **Status**: ✅ Production Ready

---

## Next Steps

### To Add More Tests

1. Create test file in appropriate directory
2. Follow When-Then naming pattern
3. Use Arrange-Act-Assert structure
4. Run tests to verify
5. Update this reference

### To Run Pre-commit Tests

```bash
cd Backend
pytest tests/unit/core/test_service_container_thread_safety.py \
       tests/unit/dtos/test_vocabulary_dto_validation.py \
       tests/unit/services/test_chunk_processing_resource_management.py \
       -x  # Stop on first failure
```

### To Debug Failing Test

```bash
# Run single test with full output
pytest tests/unit/core/test_service_container_thread_safety.py::TestServiceContainerThreadSafety::test_When_concurrent_singleton_access_Then_same_instance_returned -vv -s

# With debugger
pytest tests/unit/core/test_service_container_thread_safety.py::TestServiceContainerThreadSafety::test_When_concurrent_singleton_access_Then_same_instance_returned --pdb
```

---

## Contact & Support

For questions about these tests:

1. Check documentation in `Backend/docs/TESTING_*.md`
2. Review test file comments
3. Check git history for implementation details

---

**Status**: ✅ All systems operational
**Last Verified**: 2025-09-29
**Next Review**: When adding new architecture features
