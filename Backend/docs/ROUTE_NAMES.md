# FastAPI Route Names Reference

**Created**: 2025-10-05
**Purpose**: Complete mapping of FastAPI route names to their endpoint paths
**Status**: Phase 1 of Path Standardization (Task 9)

---

## Overview

This document maps all FastAPI route names to their full endpoint paths. Use these route names with the `url_builder` fixture in tests instead of hardcoding paths.

**Usage in Tests**:

```python
# Instead of:
response = await client.post("/api/auth/login", data=login_data)

# Use:
url = url_builder.url_for("auth_login")
response = await client.post(url, data=login_data)
```

---

## Route Naming Convention

**Pattern**: `{feature}_{action}` or `{feature}_{resource}_{action}`

**Examples**:

- `auth_login` - Authentication login
- `auth_get_current_user` - Get current user info
- `get_videos` - List all videos
- `game_start_session` - Start game session

**Special Cases**:

- FastAPI-Users routes (login, register, logout) have framework-assigned names
- Some routes use resource-first naming (e.g., `get_videos` instead of `videos_list`)

---

## Authentication Routes

**Prefix**: `/api/auth`

### FastAPI-Users Routes (Framework-Assigned Names)

- `auth:{auth_backend.name}.login` → POST /api/auth/login
- `auth:{auth_backend.name}.logout` → POST /api/auth/logout
- `register:register` → POST /api/auth/register

**Note**: The actual backend name is dynamically assigned. In tests, use the exact names shown above.

### Custom Auth Routes

- `auth_get_current_user` → GET /api/auth/me
- `auth_refresh_token` → POST /api/auth/token/refresh

---

## Video Routes

**Prefix**: `/api/videos`

### Named Routes

- `get_videos` → GET /api/videos
- `get_subtitles` → GET /api/videos/subtitles/{subtitle_path:path}
- `stream_video` → GET /api/videos/{series}/{episode}
- `upload_subtitle` → POST /api/videos/subtitle/upload
- `scan_videos` → POST /api/videos/scan
- `get_user_videos` → GET /api/videos/user
- `get_video_vocabulary` → GET /api/videos/{video_id}/vocabulary
- `get_video_status` → GET /api/videos/{video_id}/status
- `upload_video_generic` → POST /api/videos/upload
- `upload_video_to_series` → POST /api/videos/upload/{series}

---

## Vocabulary Routes

**Prefix**: `/api/vocabulary`

### Named Routes

- `get_word_info` → GET /api/vocabulary/word-info/{word}
- `mark_word_known` → POST /api/vocabulary/mark-known
- `mark_word_known_by_lemma` → POST /api/vocabulary/mark-known-lemma
- `get_vocabulary_stats` → GET /api/vocabulary/stats
- `get_vocabulary_library` → GET /api/vocabulary/library
- `get_vocabulary_level` → GET /api/vocabulary/library/{level}
- `search_vocabulary` → POST /api/vocabulary/search
- `bulk_mark_level` → POST /api/vocabulary/library/bulk-mark
- `get_supported_languages` → GET /api/vocabulary/languages
- `get_test_data` → GET /api/vocabulary/test-data
- `get_blocking_words` → GET /api/vocabulary/blocking-words

---

## Game Routes

**Prefix**: `/api/game`

### Named Routes

- `game_start_session` → POST /api/game/start
- `game_get_session` → GET /api/game/session/{session_id}
- `game_submit_answer` → POST /api/game/answer
- `game_get_user_sessions` → GET /api/game/sessions

---

## Processing Routes

**Prefix**: `/api/process`

**Note**: Processing routes are organized into sub-modules (transcription, filtering, episode processing, pipeline) that are all included under the `/api/process` prefix.

### Episode Processing Routes

- `process_chunk` → POST /api/process/chunk

### Pipeline Routes

- `full_pipeline` → POST /api/process/full-pipeline
- `get_task_progress` → GET /api/process/progress/{task_id}

### Filtering Routes

- `filter_subtitles` → POST /api/process/filter-subtitles
- `apply_selective_translations` → POST /api/process/apply-selective-translations

### Transcription Routes

- `transcribe_video` → POST /api/process/transcribe

---

## User Profile Routes

**Prefix**: `/api/profile`

### Named Routes

- `profile_get` → GET /api/profile
- `profile_update_languages` → PUT /api/profile/languages
- `profile_get_supported_languages` → GET /api/profile/languages
- `profile_get_settings` → GET /api/profile/settings
- `profile_update_settings` → PUT /api/profile/settings

---

## Progress Routes

**Prefix**: `/api/progress`

### Named Routes

- `progress_get_user` → GET /api/progress/user
- `progress_update_user` → POST /api/progress/update
- `progress_get_daily` → GET /api/progress/daily

---

## SRT Utilities Routes

**Prefix**: `/api/srt`

### Routes WITHOUT Names (Need Names Added)

- **[UNNAMED]** → POST /api/srt/parse
- **[UNNAMED]** → POST /api/srt/parse-file
- **[UNNAMED]** → POST /api/srt/convert-to-srt
- **[UNNAMED]** → GET /api/srt/validate

**Recommended Names**:

- `srt_parse_content` → POST /api/srt/parse
- `srt_parse_file` → POST /api/srt/parse-file
- `srt_convert_to_srt` → POST /api/srt/convert-to-srt
- `srt_validate` → GET /api/srt/validate

---

## WebSocket Routes

**Prefix**: `/api/ws`

### Routes WITHOUT Names (Need Names Added)

- **[UNNAMED]** → WS /api/ws/connect
- **[UNNAMED]** → WS /api/ws/status

**Recommended Names**:

- `ws_connect` → WS /api/ws/connect
- `ws_status` → WS /api/ws/status

---

## Debug Routes (Debug Mode Only)

**Prefix**: `/api/debug`

### Routes WITHOUT Names (Need Names Added)

- **[UNNAMED]** → POST /api/debug/frontend-logs
- **[UNNAMED]** → GET /api/debug/health

**Recommended Names**:

- `debug_frontend_logs` → POST /api/debug/frontend-logs
- `debug_health` → GET /api/debug/health

**Note**: These routes are only available when `settings.debug = True`

---

## Test Routes (Debug Mode Only)

**Prefix**: `/api/test`

### Routes WITHOUT Names (Need Names Added)

- **[UNNAMED]** → DELETE /api/test/cleanup

**Recommended Names**:

- `test_cleanup` → DELETE /api/test/cleanup

**Note**: These routes are only available when `settings.debug = True`

---

## Health Check Routes

### Root Routes (No prefix)

- **[UNNAMED]** → GET /health
- **[UNNAMED]** → GET /test

**Recommended Names**:

- `health_check` → GET /health
- `test_endpoint` → GET /test

**Note**: These are defined directly in `core/app.py`, not in route modules

---

## Using Route Names in Tests

### Basic Usage

```python
# Get URL from route name
url = url_builder.url_for("get_videos")
response = await client.get(url, headers=auth_headers)
```

### With Path Parameters

```python
# Route with path parameters
url = url_builder.url_for("get_video_status", video_id="S01E01.mp4")
response = await client.get(url, headers=auth_headers)

# Multiple path parameters
url = url_builder.url_for("stream_video", series="Learn German", episode="S01E01.mp4")
response = await client.get(url, headers=auth_headers)
```

### With Query Parameters

```python
# Query parameters are NOT part of url_for
url = url_builder.url_for("get_vocabulary_library")
# Add query params separately
response = await client.get(f"{url}?level=A1&limit=50", headers=auth_headers)
```

### FastAPI-Users Routes

```python
# Login (special case - uses framework name)
login_url = url_builder.url_for("auth:jwt.login")
response = await client.post(login_url, data={"username": email, "password": password})

# Register
register_url = url_builder.url_for("register:register")
response = await client.post(register_url, json=user_data)
```

---

## Routes Needing Names

The following routes currently lack `name` parameters and should be updated:

### High Priority (Frequently Tested)

1. SRT Utilities routes (4 routes)
2. WebSocket routes (2 routes)

### Medium Priority (Debug/Test Routes)

3. Debug routes (2 routes)
4. Test routes (1 route)
5. Health check routes (2 routes)

---

## Verification

To verify all route names are valid, run this test:

```python
def test_all_route_names_valid(app, url_builder):
    """Ensure all documented route names are valid."""
    route_names = [
        # Auth
        "auth_get_current_user",
        "auth_refresh_token",

        # Videos
        "get_videos",
        "get_subtitles",
        "stream_video",
        "upload_subtitle",
        "scan_videos",
        "get_user_videos",
        "get_video_vocabulary",
        "get_video_status",
        "upload_video_generic",
        "upload_video_to_series",

        # Vocabulary
        "get_word_info",
        "mark_word_known",
        "mark_word_known_by_lemma",
        "get_vocabulary_stats",
        "get_vocabulary_library",
        "get_vocabulary_level",
        "search_vocabulary",
        "bulk_mark_level",
        "get_supported_languages",
        "get_test_data",
        "get_blocking_words",

        # Game
        "game_start_session",
        "game_get_session",
        "game_submit_answer",
        "game_get_user_sessions",

        # Processing (includes transcription, filtering, pipeline)
        "process_chunk",
        "full_pipeline",
        "get_task_progress",
        "filter_subtitles",
        "apply_selective_translations",
        "transcribe_video",

        # Profile
        "profile_get",
        "profile_update_languages",
        "profile_get_supported_languages",
        "profile_get_settings",
        "profile_update_settings",

        # Progress
        "progress_get_user",
        "progress_update_user",
        "progress_get_daily",
    ]

    for name in route_names:
        try:
            url = url_builder.url_for(name)
            assert url.startswith("/api/")
        except NoRouteFound:
            pytest.fail(f"Route name '{name}' not found in application")
```

---

## Migration Status

**Phase 1**: ✅ Route name documentation complete (this file)
**Phase 2**: ⏳ Update Auth tests (8 files) - Pending
**Phase 3**: ⏳ Update Vocabulary tests (5 files) - Pending
**Phase 4**: ⏳ Update Video tests (6 files) - Pending
**Phase 5**: ⏳ Update Processing tests (4 files) - Pending
**Phase 6**: ⏳ Update Integration tests (~20 files) - Pending
**Phase 7**: ⏳ Update Game/User tests - Pending
**Phase 8**: ⏳ Create migration helper and pre-commit hook - Pending

**Current Status**: 410 hardcoded paths remain in test files
**Target**: 0 hardcoded paths (all using `url_builder`)

---

## Related Documentation

- [PATH_STANDARDIZATION_PLAN.md](./PATH_STANDARDIZATION_PLAN.md) - Complete migration plan
- [CODE_SIMPLIFICATION_ROADMAP.md](../CODE_SIMPLIFICATION_ROADMAP.md) - Task 9 tracking
- [tests/conftest.py](../tests/conftest.py) - URLBuilder fixture implementation

---

**Last Updated**: 2025-10-05
**Maintainer**: Development Team
**Status**: Phase 1 Complete
