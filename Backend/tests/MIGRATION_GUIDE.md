# Migration Guide: Converting Tests to Robust URL Pattern

This guide helps you convert existing tests from hardcoded URLs to the robust URL builder pattern.

## Quick Start

### 1. Install the URL Builder Fixture

Add this fixture to your test file or use the shared `conftest_robust.py`:

```python
import pytest
from tests.utils.url_builder import get_url_builder

@pytest.fixture
def url_builder(client):
    """URL builder fixture for robust URL generation"""
    return get_url_builder(client.app)
```

### 2. Convert Hardcoded URLs

**Before (Fragile):**
```python
def test_get_user_profile(client):
    response = client.get("/api/user/profile")
    assert response.status_code == 200
```

**After (Robust):**
```python
def test_get_user_profile(client, url_builder):
    url = url_builder.url_for("profile_get")
    response = client.get(url)
    assert response.status_code == 200
```

## Step-by-Step Migration Process

### Step 1: Identify Hardcoded URLs

Use the conversion utility to scan your test files:

```bash
cd Backend/tests
python utils/convert_hardcoded_urls.py
```

This will generate a report showing:
- All hardcoded URLs found
- Suggested route names to use
- Example conversions

### Step 2: Ensure Routes Have Names

Check that all your FastAPI routes have unique `name` parameters:

```python
# ✅ Good - Named route
@router.get("/profile", name="profile_get")
async def get_profile():
    pass

# ❌ Bad - Unnamed route
@router.get("/profile")
async def get_profile():
    pass
```

### Step 3: Update Test Imports

Add the URL builder import to your test file:

```python
from tests.utils.url_builder import get_url_builder
```

### Step 4: Add URL Builder Fixture

```python
@pytest.fixture
def url_builder(client):
    return get_url_builder(client.app)
```

### Step 5: Convert URL Usage

Replace hardcoded URLs with URL builder calls:

| Pattern | Before | After |
|---------|--------|-------|
| Simple GET | `client.get("/api/auth/me")` | `client.get(url_builder.url_for("auth_get_current_user"))` |
| With Path Params | `client.get("/api/videos/123")` | `client.get(url_builder.url_for("video_get", video_id=123))` |
| With Query Params | `client.get("/api/search?q=test")` | `client.get(url_builder.url_for("search") + "?q=test")` |

## Common Route Name Patterns

Our codebase uses these naming conventions:

| Route Type | Pattern | Example |
|------------|---------|---------|
| Auth | `auth_<action>` | `auth_get_current_user`, `auth_test_prefix` |
| User Profile | `profile_<action>` | `profile_get`, `profile_update_languages` |
| Videos | `video_<action>` | `stream_video`, `upload_video` |
| Game | `game_<action>` | `game_start_session`, `game_submit_answer` |
| Progress | `progress_<action>` | `progress_get_user`, `progress_update_user` |
| Vocabulary | `vocab_<action>` | `vocab_get_stats`, `vocab_block_word` |
| Debug | `debug_<action>` | `debug_health`, `debug_test_minimal` |
| Logs | `logs_<action>` | `logs_receive_frontend`, `logs_list_files` |

## Migration Examples

### Example 1: Auth Tests

**Before:**
```python
def test_current_user_endpoint(client, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
```

**After:**
```python
def test_current_user_endpoint(client, url_builder, auth_headers):
    url = url_builder.url_for("auth_get_current_user")
    response = client.get(url, headers=auth_headers)
    assert response.status_code == 200
```

### Example 2: Video Streaming Tests

**Before:**
```python
def test_stream_video(client):
    response = client.get("/api/videos/stream/test-video-123")
    assert response.status_code == 200
```

**After:**
```python
def test_stream_video(client, url_builder):
    url = url_builder.url_for("stream_video", video_id="test-video-123")
    response = client.get(url)
    assert response.status_code == 200
```

### Example 3: POST Requests with Data

**Before:**
```python
def test_update_progress(client, auth_headers):
    data = {"words_learned": 25, "session_time": 300}
    response = client.post("/api/progress/user", json=data, headers=auth_headers)
    assert response.status_code == 200
```

**After:**
```python
def test_update_progress(client, url_builder, auth_headers):
    url = url_builder.url_for("progress_update_user")
    data = {"words_learned": 25, "session_time": 300}
    response = client.post(url, json=data, headers=auth_headers)
    assert response.status_code == 200
```

## Benefits After Migration

### ✅ Resilient to Route Changes
- Route prefix changes don't break tests
- URL structure modifications are automatically handled
- Path parameter validation is built-in

### ✅ Better Error Messages
- Clear exceptions when route names don't exist
- Type checking for path parameters
- Immediate feedback during development

### ✅ Maintainable Test Suite
- Single source of truth for URLs
- Easy to refactor route structures
- Self-documenting test code

## Common Migration Issues

### Issue 1: Route Name Not Found
```
RouteNotFoundError: Route 'unknown_route' not found
```
**Solution:** Check that the route has a `name` parameter in its decorator.

### Issue 2: Missing Path Parameters
```
MissingParameterError: Route 'video_get' requires parameter 'video_id'
```
**Solution:** Provide all required path parameters:
```python
url = url_builder.url_for("video_get", video_id=123)
```

### Issue 3: Import Errors
```
ModuleNotFoundError: No module named 'tests.utils'
```
**Solution:** Ensure proper Python path setup:
```python
import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
```

## Testing Your Migration

### Run Specific Test Categories
```bash
# Test only robust tests
pytest -m robust

# Test auth functionality
pytest -m auth

# Test performance
pytest -m performance
```

### Verify URL Generation
```python
def test_url_builder_functionality(url_builder):
    """Test that URL builder generates expected URLs"""
    # Test simple route
    url = url_builder.url_for("auth_get_current_user")
    assert url == "/api/auth/me"
    
    # Test route with parameters
    url = url_builder.url_for("stream_video", video_id="test-123")
    assert url == "/api/videos/stream/test-123"
```

## Integration with CI/CD

Add these commands to your CI pipeline:

```yaml
# Run migration scan to catch new hardcoded URLs
- name: Check for hardcoded URLs
  run: python tests/utils/convert_hardcoded_urls.py

# Run robust tests specifically
- name: Run robust tests
  run: pytest tests/robust/ -v

# Run all tests with robust markers
- name: Run all robust-compatible tests
  run: pytest -m robust
```

## File Organization After Migration

```
tests/
├── robust/                 # New robust test files
│   ├── __init__.py
│   ├── robust_auth_tests.py
│   ├── robust_video_tests.py
│   ├── robust_vocabulary_tests.py
│   ├── robust_processing_tests.py
│   └── robust_performance_tests.py
├── utils/                  # Testing utilities
│   ├── __init__.py
│   ├── url_builder.py     # Core URL builder
│   └── convert_hardcoded_urls.py  # Migration tool
├── conftest_robust.py     # Robust test configuration
├── MIGRATION_GUIDE.md     # This guide
└── README.md              # Full documentation
```

## Next Steps

1. **Audit Existing Tests:** Run the conversion utility to identify all hardcoded URLs
2. **Migrate High-Priority Tests:** Start with core authentication and API tests
3. **Add Route Names:** Ensure all new routes include unique names
4. **Update CI/CD:** Integrate robust test markers into your pipeline
5. **Train Team:** Share this guide with other developers

## Need Help?

- Check `tests/README.md` for comprehensive documentation
- Look at `tests/robust/` for working examples
- Run `python tests/utils/convert_hardcoded_urls.py` for automated suggestions
- Review `tests/example_robust_tests.py` for patterns and best practices
