# Migration Guide - Using Refactored Services

**Date**: 2025-09-30
**Audience**: Developers working with refactored services

---

## Quick Start

### TL;DR

- **Existing code**: No changes needed (100% backward compatible)
- **New code**: Use focused services directly for better clarity
- **Migration**: Optional and gradual

---

## Table of Contents

1. [No Breaking Changes](#no-breaking-changes)
2. [Using New Services](#using-new-services)
3. [Service-by-Service Guide](#service-by-service-guide)
4. [Common Patterns](#common-patterns)
5. [Testing Guide](#testing-guide)
6. [FAQ](#faq)

---

## No Breaking Changes

### All Existing Code Works ✅

The refactoring maintains **100% backward compatibility** through facade patterns.

```python
# This code written before refactoring still works EXACTLY the same
from services.vocabulary_service import VocabularyService

service = VocabularyService()
result = await service.get_word_info("Haus", "de")
# Works perfectly - no changes needed
```

**You do NOT need to update existing code.**

---

## Using New Services

### Recommendation for New Code

When writing **new code**, prefer using the focused services directly:

```python
# OLD STYLE (still works, but not recommended for new code)
from services.vocabulary_service import VocabularyService
service = VocabularyService()
word_info = await service.get_word_info("Haus", "de")
stats = await service.get_vocabulary_stats(user_id)

# NEW STYLE (recommended for new code)
from services.vocabulary import VocabularyQueryService, VocabularyStatsService

query_service = VocabularyQueryService()
stats_service = VocabularyStatsService()

word_info = await query_service.get_word_info("Haus", "de")
stats = await stats_service.get_vocabulary_stats(user_id)
```

### Why Use Focused Services?

1. **Clearer Intent**: Immediately see what functionality you're using
2. **Smaller Imports**: Only load what you need
3. **Better Testability**: Mock only the specific service needed
4. **Performance**: Lighter memory footprint

---

## Service-by-Service Guide

### 1. Vocabulary Service

#### Old API (Facade - Still Works)

```python
from services.vocabulary_service import VocabularyService

service = VocabularyService()

# All methods still work exactly as before
word_info = await service.get_word_info("Haus", "de")
level_words = await service.get_vocabulary_level("A1", "de")
stats = await service.get_vocabulary_stats(user_id)
await service.mark_word_known(user_id, "Haus")
```

#### New API (Focused Services)

```python
from services.vocabulary import (
    VocabularyQueryService,    # For queries and lookups
    VocabularyProgressService,  # For progress tracking
    VocabularyStatsService      # For statistics
)

# Use specific service for specific task
query_service = VocabularyQueryService()
word_info = await query_service.get_word_info("Haus", "de")
level_words = await query_service.get_vocabulary_level("A1", "de")

progress_service = VocabularyProgressService()
await progress_service.mark_word_known(user_id, "Haus")

stats_service = VocabularyStatsService()
stats = await stats_service.get_vocabulary_stats(user_id)
```

#### When to Use Which?

| Use Case                 | Recommended Approach           |
| ------------------------ | ------------------------------ |
| Need multiple operations | Use facade (VocabularyService) |
| Only need queries        | Use VocabularyQueryService     |
| Only tracking progress   | Use VocabularyProgressService  |
| Only need statistics     | Use VocabularyStatsService     |
| Writing new feature      | Use focused services           |
| Maintaining old code     | Keep using facade              |

---

### 2. Direct Subtitle Processor

#### Old API (Facade - Still Works)

```python
from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor

processor = DirectSubtitleProcessor()
result = await processor.process_subtitles(subtitles, user_id, "A1", "de")
```

#### New API (Focused Services)

```python
from services.filterservice.subtitle_processing import (
    UserDataLoader,      # Load user data
    WordValidator,       # Validate words
    WordFilter,          # Filter words
    SubtitleProcessor,   # Process subtitles
    SRTFileHandler       # File I/O
)

# For custom processing pipelines
data_loader = UserDataLoader()
validator = WordValidator()
filter_service = WordFilter()

user_data = await data_loader.get_user_known_words(user_id, "de")

for subtitle in subtitles:
    for word in subtitle.words:
        if validator.is_valid_vocabulary_word(word, "de"):
            filtered = filter_service.filter_word(word, user_data, "A1", "de")
            # Process filtered word
```

#### When to Use Which?

| Use Case                     | Recommended Approach                 |
| ---------------------------- | ------------------------------------ |
| Standard subtitle processing | Use facade (DirectSubtitleProcessor) |
| Custom validation rules      | Use WordValidator directly           |
| Custom filtering logic       | Use WordFilter directly              |
| Custom file formats          | Use SRTFileHandler directly          |
| Extending word validation    | Subclass WordValidator               |

---

### 3. Chunk Processor

#### Old API (Facade - Still Works)

```python
from services.processing.chunk_processor import ChunkProcessingService

service = ChunkProcessingService(db_session)
await service.process_chunk(video_path, start_time, end_time, user_id, task_id, task_progress)
```

#### New API (Focused Services)

```python
from services.processing.chunk_services import (
    VocabularyFilterService,       # Filter vocabulary
    SubtitleGenerationService,     # Generate subtitles
    TranslationManagementService   # Manage translations
)

# For custom chunk processing
vocab_filter = VocabularyFilterService()
subtitle_gen = SubtitleGenerationService()
translation_mgr = TranslationManagementService()

# Custom processing pipeline
vocabulary = await vocab_filter.filter_vocabulary_from_srt(srt_path, user, prefs)
filtered_srt = await subtitle_gen.generate_filtered_subtitles(video_file, vocabulary, source_srt)
translations = await translation_mgr.apply_selective_translations(srt_path, known_words, "de", "A1", user_id)
```

#### When to Use Which?

| Use Case                     | Recommended Approach                |
| ---------------------------- | ----------------------------------- |
| Standard chunk processing    | Use facade (ChunkProcessingService) |
| Custom vocabulary filtering  | Use VocabularyFilterService         |
| Custom subtitle highlighting | Use SubtitleGenerationService       |
| Custom translation logic     | Use TranslationManagementService    |

---

### 4. Filtering Handler

#### Old API (Facade - Still Works)

```python
from services.filterservice.filtering_handler import FilteringHandler

handler = FilteringHandler()
result = await handler.filter_subtitles(subtitles, user_id, options)
```

#### New API (Focused Services)

```python
from services.filtering import (
    SubtitleFilter,        # Filter subtitles
    VocabularyExtractor,   # Extract vocabulary
    TranslationAnalyzer    # Analyze translations
)

# Use specific service for specific task
subtitle_filter = SubtitleFilter()
filtered_subs = await subtitle_filter.filter(subtitles, options)

vocab_extractor = VocabularyExtractor()
vocabulary = await vocab_extractor.extract(filtered_subs)

translation_analyzer = TranslationAnalyzer()
analysis = await translation_analyzer.analyze(vocabulary)
```

---

### 5. Logging Service

#### Old API (Facade - Still Works)

```python
from services.loggingservice.logging_service import LoggingService

logger = LoggingService()
logger.log("INFO", "Message", {"context": "data"})
```

#### New API (Focused Services)

```python
from services.logging import (
    LogFormatterService,    # Format logs
    LogHandlerService,      # Setup handlers
    LogManagerService,      # Manage logs
    LogConfigManagerService # Configure logging
)

# For custom logging setup
formatter = LogFormatterService()
handler_service = LogHandlerService()
log_manager = LogManagerService()

# Custom log configuration
formatted_message = formatter.format(message, level, context)
handler = handler_service.create_console_handler()
log_manager.add_handler(handler)
```

---

### 6. User Vocabulary Service

#### Old API (Facade - Still Works)

```python
from services.user_vocabulary_service import UserVocabularyService

service = UserVocabularyService(db_session)
known_words = await service.get_user_known_words(user_id, "de")
```

#### New API (Focused Services)

```python
from services.user_vocabulary import (
    UserVocabularyRepository,  # Data access
    UserProgressService,       # Progress tracking
    UserStatsService,          # Statistics
    UserQueryService           # Queries
)

# Use repository for data access
repository = UserVocabularyRepository(db_session)
known_words = await repository.get_user_known_words(user_id, "de")

# Use services for business logic
progress_service = UserProgressService(repository)
progress = await progress_service.calculate_progress(user_id)
```

---

## Common Patterns

### Pattern 1: Dependency Injection

**Old Style** (still works):

```python
# Service creates its own dependencies
service = VocabularyService()
result = await service.get_word_info("Haus", "de")
```

**New Style** (recommended):

```python
# Inject dependencies explicitly
query_service = VocabularyQueryService(db_session)
result = await query_service.get_word_info("Haus", "de")
```

**Benefits**:

- Easier to test (inject mocks)
- Clearer dependencies
- Better for unit tests

---

### Pattern 2: Service Composition

**Old Style**:

```python
# Use monolithic service for everything
service = VocabularyService()
word_info = await service.get_word_info("Haus", "de")
stats = await service.get_vocabulary_stats(user_id)
```

**New Style**:

```python
# Compose multiple focused services
query_service = VocabularyQueryService()
stats_service = VocabularyStatsService()

word_info = await query_service.get_word_info("Haus", "de")
stats = await stats_service.get_vocabulary_stats(user_id)
```

**Benefits**:

- Only load what you need
- Clearer separation of concerns
- Easier to mock in tests

---

### Pattern 3: Repository Pattern

**New Feature**: Separate data access from business logic

```python
# Data Access Layer (Repository)
from services.user_vocabulary import UserVocabularyRepository

repository = UserVocabularyRepository(db_session)
known_words = await repository.get_user_known_words(user_id, "de")

# Business Logic Layer (Service)
from services.user_vocabulary import UserProgressService

progress_service = UserProgressService(repository)
progress = await progress_service.calculate_progress(user_id)
```

**Benefits**:

- Testable without database
- Swap database implementations
- Clear separation of concerns

---

## Testing Guide

### Testing with Old API (Facade)

```python
@pytest.mark.asyncio
async def test_vocabulary_service_get_word():
    """Test using facade (old style)"""
    service = VocabularyService()

    # Mock the database
    with patch.object(service, 'db_session'):
        result = await service.get_word_info("Haus", "de")

    assert result["word"] == "Haus"
```

### Testing with New API (Focused Services)

```python
@pytest.mark.asyncio
async def test_vocabulary_query_service():
    """Test using focused service (new style)"""
    query_service = VocabularyQueryService()

    # Only mock what this service needs
    mock_db = AsyncMock()
    result = await query_service.get_word_info("Haus", "de", mock_db)

    assert result["word"] == "Haus"
```

### Testing Service Composition

```python
@pytest.mark.asyncio
async def test_user_progress_calculation():
    """Test service using repository pattern"""
    # Mock repository (data access layer)
    mock_repository = Mock()
    mock_repository.get_user_known_words = AsyncMock(return_value=["Haus", "Auto"])

    # Test service (business logic layer)
    progress_service = UserProgressService(mock_repository)
    progress = await progress_service.calculate_progress("user123")

    assert progress["words_known"] == 2
```

---

## FAQ

### Q: Do I need to update my existing code?

**A:** No. All existing code continues to work without any changes.

---

### Q: Should I migrate existing code to use new services?

**A:** Only if you're already modifying that code. There's no urgency to migrate working code.

**When to migrate**:

- ✅ Already editing the file
- ✅ Adding new features
- ✅ Improving test coverage
- ✅ Performance optimization needed

**When NOT to migrate**:

- ❌ Code works fine and untouched
- ❌ No plans to modify
- ❌ Just for the sake of migrating

---

### Q: What should I use for new features?

**A:** Use the focused services directly. They're clearer, more testable, and more performant.

```python
# Recommended for new code
from services.vocabulary import VocabularyQueryService
query_service = VocabularyQueryService()
```

---

### Q: Can I mix old and new APIs?

**A:** Yes, absolutely. They can coexist without issues.

```python
# Mix old and new - totally fine
from services.vocabulary_service import VocabularyService
from services.vocabulary import VocabularyStatsService

# Use old API for some operations
old_service = VocabularyService()
result1 = await old_service.get_word_info("Haus", "de")

# Use new API for others
stats_service = VocabularyStatsService()
stats = await stats_service.get_vocabulary_stats(user_id)
```

---

### Q: How do I know which service to use?

**A:** Follow this decision tree:

```
Do you need multiple operations from the same domain?
├─ Yes → Use facade (e.g., VocabularyService)
└─ No → Use focused service (e.g., VocabularyQueryService)

Are you writing new code?
├─ Yes → Use focused services
└─ No (maintaining old code) → Keep using facade

Do you need custom logic?
├─ Yes → Use focused services and compose them
└─ No → Use facade
```

---

### Q: What if I need functionality from multiple services?

**A:** You have two options:

**Option 1**: Use the facade

```python
service = VocabularyService()
result1 = await service.get_word_info("Haus", "de")
result2 = await service.get_vocabulary_stats(user_id)
```

**Option 2**: Compose multiple services

```python
query_service = VocabularyQueryService()
stats_service = VocabularyStatsService()

result1 = await query_service.get_word_info("Haus", "de")
result2 = await stats_service.get_vocabulary_stats(user_id)
```

Choose based on:

- Facade: Simpler, fewer imports, good for many operations
- Composition: More explicit, better for testing, good for new code

---

### Q: Are there performance differences?

**A:** Minimal differences:

**Facades**:

- One extra function call (negligible)
- Load entire facade class
- Still delegates to focused services

**Focused Services**:

- Direct calls (slightly faster)
- Load only what you need
- Smaller memory footprint

**Recommendation**: Choose based on code clarity, not performance. The differences are negligible in practice.

---

### Q: How do I inject dependencies?

**Old style** (implicit):

```python
service = VocabularyService()  # Creates dependencies internally
```

**New style** (explicit):

```python
query_service = VocabularyQueryService(db_session)  # Inject explicitly
```

**For testing**:

```python
# Easy to inject mocks
mock_db = Mock()
query_service = VocabularyQueryService(mock_db)
```

---

### Q: What about backward compatibility in the future?

**A:** Facades will be maintained for at least 1 year. If we decide to remove them:

1. Deprecation warnings will be added (6 months notice)
2. Migration guide will be provided
3. Automated migration tools may be created

**Current status**: No plans to remove facades. They're lightweight and useful.

---

## Migration Checklist

### For New Features ✅

- [ ] Use focused services (VocabularyQueryService, etc.)
- [ ] Inject dependencies explicitly
- [ ] Write tests against focused services
- [ ] Document which services you're using

### For Maintaining Existing Code ✅

- [ ] Keep using facades (no changes needed)
- [ ] Only migrate if already editing the file
- [ ] Test thoroughly after migration
- [ ] Update tests to match new API

### For Refactoring ✅

- [ ] Identify which focused services are needed
- [ ] Replace facade calls with focused service calls
- [ ] Update tests to mock focused services
- [ ] Verify backward compatibility not needed
- [ ] Test thoroughly

---

## Examples

### Example 1: Writing a New Feature

**Task**: Add feature to track user's vocabulary learning streak

**Recommended approach**:

```python
from services.vocabulary import VocabularyProgressService

class StreakTracker:
    def __init__(self):
        self.progress_service = VocabularyProgressService()

    async def calculate_streak(self, user_id: str) -> int:
        """Calculate user's learning streak"""
        # Use focused service directly
        progress = await self.progress_service.get_user_progress(user_id)

        # Calculate streak based on progress
        streak = self._calculate_streak_from_progress(progress)
        return streak
```

**Why this approach?**

- Clear dependency (VocabularyProgressService)
- Easy to test (mock progress_service)
- Only loads what's needed

---

### Example 2: Maintaining Existing Code

**Task**: Fix bug in existing vocabulary lookup

**Recommended approach**:

```python
# Existing code
from services.vocabulary_service import VocabularyService

async def lookup_word(word: str, language: str):
    service = VocabularyService()
    return await service.get_word_info(word, language)

# Fix the bug - keep using facade
async def lookup_word(word: str, language: str):
    service = VocabularyService()
    # Fixed: Add error handling
    try:
        return await service.get_word_info(word, language)
    except NotFoundError:
        return {"error": "Word not found"}
```

**Why this approach?**

- Minimal changes (less risk)
- Backward compatible
- Existing tests still work

---

### Example 3: Refactoring for Testability

**Before** (hard to test):

```python
async def process_user_vocabulary(user_id: str):
    service = VocabularyService()  # Hard to mock
    stats = await service.get_vocabulary_stats(user_id)
    progress = await service.get_user_progress(user_id)
    return {"stats": stats, "progress": progress}
```

**After** (easy to test):

```python
from services.vocabulary import VocabularyStatsService, VocabularyProgressService

async def process_user_vocabulary(
    user_id: str,
    stats_service: VocabularyStatsService,
    progress_service: VocabularyProgressService
):
    # Easy to inject mocks for testing
    stats = await stats_service.get_vocabulary_stats(user_id)
    progress = await progress_service.get_user_progress(user_id)
    return {"stats": stats, "progress": progress}
```

**Test**:

```python
async def test_process_user_vocabulary():
    # Easy to mock
    mock_stats = Mock()
    mock_progress = Mock()

    mock_stats.get_vocabulary_stats = AsyncMock(return_value={"score": 100})
    mock_progress.get_user_progress = AsyncMock(return_value={"streak": 5})

    result = await process_user_vocabulary("user123", mock_stats, mock_progress)

    assert result["stats"]["score"] == 100
    assert result["progress"]["streak"] == 5
```

---

## Conclusion

### Key Takeaways

1. **No Changes Required**: Existing code works perfectly
2. **New Code**: Use focused services for clarity and testability
3. **Migration**: Optional and gradual
4. **Testing**: Focused services are easier to test
5. **Performance**: Negligible differences in practice

### When in Doubt

- **Maintaining existing code?** → Keep using facades
- **Writing new features?** → Use focused services
- **Unsure?** → Ask the team or stick with facades

### Resources

- **Architecture Overview**: See ARCHITECTURE_AFTER_REFACTORING.md
- **Refactoring Summary**: See REFACTORING_COMPLETE.md
- **Test Cleanup**: See TEST_CLEANUP_NEEDED.md

---

**Questions?** Ask the team or refer to the architecture documentation.
