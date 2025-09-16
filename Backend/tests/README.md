# Robust URL Testing Implementation

This directory contains a robust testing framework that eliminates hardcoded URLs and prevents URL divergence issues in your FastAPI test suite.

## 🎯 Problem Solved

Previously, tests used hardcoded URLs like `"/api/auth/me"` which would break when route prefixes changed. This implementation uses named routes and a URL builder pattern to make tests resilient to URL structure changes.

## 🛠️ How It Works

### 1. Named Routes
All FastAPI routes now have unique `name` parameters following the `resource_action` convention:

```python
# Before ❌
@router.get("/me", response_model=UserResponse)
async def get_current_user_info():
    pass

# After ✅
@router.get("/me", response_model=UserResponse, name="auth_get_current_user")
async def get_current_user_info():
    pass
```

### 2. URL Builder Pattern
Tests use the `url_builder.py` utility to generate URLs dynamically:

```python
# Before ❌ - Fragile hardcoded URL
response = client.get("/api/auth/me")

# After ✅ - Robust named route
url = url_builder.url_for("auth_get_current_user")
response = client.get(url)
```

## 📁 File Structure

```
tests/
├── README.md                          # This documentation
├── url_builder.py                     # Core URL builder utility
├── example_robust_tests.py           # Example patterns and best practices
├── convert_hardcoded_urls.py         # Tool to find hardcoded URLs
│
├── robust_auth_tests.py              # Authentication endpoint tests
├── robust_video_tests.py             # Video endpoint tests  
├── robust_vocabulary_tests.py        # Vocabulary endpoint tests
├── robust_processing_tests.py        # Processing endpoint tests
├── robust_performance_tests.py       # Performance tests
│
└── [existing test files...]          # Legacy tests (can be migrated)
```

## 🚀 Quick Start

### Using URL Builder in Tests

```python
import pytest
from fastapi.testclient import TestClient
from url_builder import get_url_builder
from main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture 
def url_builder(client):
    return get_url_builder(client.app)

def test_my_endpoint(client, url_builder):
    # Generate URL dynamically
    url = url_builder.url_for("my_route_name")
    response = client.get(url)
    assert response.status_code == 200
```

### With Path Parameters

```python
def test_video_streaming(client, url_builder):
    # Route with parameters
    url = url_builder.url_for("stream_video", series="TestSeries", episode="S01E01")
    response = client.get(url)
    # URL will be: /api/videos/TestSeries/S01E01
```

## 📋 Available Route Names

### Authentication Routes
- `auth_get_current_user` - GET /api/auth/me
- `auth_test_prefix` - GET /api/auth/test-prefix

### Video Routes  
- `get_videos` - GET /api/videos
- `stream_video` - GET /api/videos/{series}/{episode}
- `upload_video_to_series` - POST /api/videos/upload/{series}
- `upload_video_generic` - POST /api/videos/upload
- `get_video_status` - GET /api/videos/{video_id}/status
- `get_video_vocabulary` - GET /api/videos/{video_id}/vocabulary
- `get_subtitles` - GET /api/videos/subtitles/{subtitle_path}
- `upload_subtitle` - POST /api/videos/subtitle/upload
- `scan_videos` - POST /api/videos/scan
- `get_user_videos` - GET /api/videos/user

### Vocabulary Routes
- `get_vocabulary_stats` - GET /api/vocabulary/stats
- `get_blocking_words` - GET /api/vocabulary/blocking-words
- `mark_word_known` - POST /api/vocabulary/mark-known
- `preload_vocabulary` - POST /api/vocabulary/preload
- `get_library_stats` - GET /api/vocabulary/library/stats
- `get_vocabulary_level` - GET /api/vocabulary/library/{level}
- `bulk_mark_level` - POST /api/vocabulary/library/bulk-mark

### Processing Routes
- `process_chunk` - POST /api/processing/chunk
- `transcribe_video` - POST /api/processing/transcribe
- `filter_subtitles` - POST /api/processing/filter-subtitles
- `translate_subtitles` - POST /api/processing/translate-subtitles
- `prepare_episode` - POST /api/processing/prepare-episode
- `full_pipeline` - POST /api/processing/full-pipeline
- `get_task_progress` - GET /api/processing/progress/{task_id}

### Profile Routes
- `profile_get` - GET /api/profile
- `profile_update_languages` - PUT /api/profile/languages
- `profile_get_supported_languages` - GET /api/profile/languages
- `profile_get_settings` - GET /api/profile/settings
- `profile_update_settings` - PUT /api/profile/settings

### Progress Routes
- `progress_get_user` - GET /api/progress/user
- `progress_update_user` - POST /api/progress/update
- `progress_get_daily` - GET /api/progress/daily

### Game Routes
- `game_start_session` - POST /api/game/start
- `game_get_session` - GET /api/game/session/{session_id}
- `game_submit_answer` - POST /api/game/answer
- `game_get_user_sessions` - GET /api/game/sessions

### Debug Routes
- `debug_receive_frontend_logs` - POST /api/debug/frontend-logs
- `debug_health` - GET /api/debug/health
- `debug_test_minimal` - POST /api/debug/test-minimal
- `debug_test_with_data` - POST /api/debug/test-with-data

### Logs Routes
- `logs_receive_frontend` - POST /api/logs/frontend
- `logs_list_files` - GET /api/logs/list
- `logs_download_file` - GET /api/logs/download/{filename}

## 🔧 Tools

### Finding Hardcoded URLs
```bash
python tests/convert_hardcoded_urls.py
```
This tool scans test files and identifies hardcoded URLs that should be converted.

### Running Robust Tests
```bash
# Run all robust tests
python -m pytest tests/robust_*.py -v

# Run specific test category
python -m pytest tests/robust_auth_tests.py -v
python -m pytest tests/robust_video_tests.py -v
```

## 📈 Benefits

### URL Divergence Prevention
- Tests automatically adapt when route prefixes change
- No more broken tests due to URL structure changes
- Future-proof against API versioning

### Maintainability  
- Single source of truth for route names
- Type-safe URL generation
- Clear error messages for missing routes

### Test Reliability
- Eliminates hardcoded URL maintenance burden
- Consistent URL generation across all tests
- Better test coverage with parameter validation

## 🔄 Migration Guide

### Converting Existing Tests

1. **Add URL Builder Fixture**:
```python
@pytest.fixture 
def url_builder(client):
    from url_builder import get_url_builder
    return get_url_builder(client.app)
```

2. **Replace Hardcoded URLs**:
```python
# Before
response = client.get("/api/auth/me")

# After  
url = url_builder.url_for("auth_get_current_user")
response = client.get(url)
```

3. **Handle Path Parameters**:
```python
# Before
response = client.get(f"/api/videos/{series}/{episode}")

# After
url = url_builder.url_for("stream_video", series=series, episode=episode)
response = client.get(url)
```

### Common Patterns

**Authentication Tests**:
```python
def test_protected_endpoint(client, url_builder):
    url = url_builder.url_for("protected_route_name")
    response = client.get(url)
    assert response.status_code == 401  # No auth provided
```

**Parameter Validation**:
```python
def test_invalid_parameters(client, url_builder):
    url = url_builder.url_for("route_with_params", param="invalid_value")
    response = client.get(url)
    assert response.status_code in [400, 404, 422]
```

**Security Tests**:
```python
def test_sql_injection_protection(client, url_builder):
    malicious_input = "'; DROP TABLE users; --"
    url = url_builder.url_for("search_route")
    response = client.get(url, params={"q": malicious_input})
    assert response.status_code in [400, 422]  # Should be rejected
```

## 🏁 Next Steps

1. **Migrate Legacy Tests**: Convert existing test files to use the URL builder pattern
2. **Add New Routes**: When creating new routes, always add a `name` parameter
3. **Update CI/CD**: Ensure the robust tests run in your continuous integration pipeline
4. **Monitor**: Use the conversion tool periodically to catch any new hardcoded URLs

## 🆘 Troubleshooting

### Common Issues

**Route Not Found Error**:
```python
ValueError: Route 'my_route_name' not found in app routes
```
- Check if the route name exists in the route definition
- Verify the route is properly included in the app

**Missing Path Parameters**:
```python
url = url_builder.url_for("stream_video")  # Missing series, episode
```
- Provide all required path parameters
- Check the route definition for required parameters

**Import Errors**:
- Ensure `url_builder.py` is in the same directory or properly imported
- Check that the `main` module can be imported for the app instance

### Getting Help

- Check `example_robust_tests.py` for patterns and examples
- Run `convert_hardcoded_urls.py` to identify URLs needing conversion
- Look at existing `robust_*.py` files for implementation examples
