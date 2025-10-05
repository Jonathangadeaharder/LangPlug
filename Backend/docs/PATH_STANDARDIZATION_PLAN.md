# Path Standardization Plan

**Created**: 2025-10-05
**Task**: Standardize Path Definitions (Task 9)
**Status**: Frontend Complete, Backend Planned

---

## Executive Summary

This document outlines the plan to standardize path definitions across the LangPlug codebase, eliminating hardcoded API paths in favor of centralized configuration and route name resolution.

---

## Frontend: Completed ✅

### Changes Made

**1. Created Centralized Endpoint Configuration**

- File: `Frontend/src/config/api-endpoints.ts`
- Centralized all API endpoint paths
- Organized by feature (AUTH, SRT, VIDEO, PROCESSING, VOCABULARY, GAME, USER)
- Made paths constants with TypeScript `as const` for type safety

**2. Updated SRT API Client**

- File: `Frontend/src/utils/srtApi.ts`
- Changed from hardcoded `'/api/srt'` to `SRT_ENDPOINTS.BASE`
- Now imports from centralized configuration
- Eliminates magic strings

### Benefits

- **Single Source of Truth**: All endpoint paths in one location
- **Easier Maintenance**: Change endpoint in one place, updates everywhere
- **Type Safety**: TypeScript constants prevent typos
- **Discoverability**: New developers can find all endpoints easily

---

## Backend: Analysis and Plan

### Current State

**410 hardcoded API paths** found in test files:

```bash
grep -r '"/api/' tests/ --include="*.py" | wc -l
# Result: 410 occurrences
```

**Existing Solution**: URLBuilder fixture already exists in `tests/conftest.py`

```python
class URLBuilder:
    """Type-safe URL builder using FastAPI's url_path_for."""

    def __init__(self, app):
        self.app = app

    def url_for(self, route_name: str, **path_params) -> str:
        return self.app.url_path_for(route_name, **path_params)
```

**Current Usage**: Only ~10-15 test files use `url_builder`, most still use hardcoded paths

### Examples of Hardcoded Paths

**Current (Hardcoded)**:

```python
# tests/api/test_auth_endpoints.py
response = await async_http_client.post("/api/auth/login", data=login_data)
response = await async_http_client.post("/api/auth/register", json=user_data)
```

**Target (Using url_builder)**:

```python
# tests/api/test_auth_endpoints.py
login_url = url_builder.url_for("auth_login")
response = await async_http_client.post(login_url, data=login_data)

register_url = url_builder.url_for("register:register")
response = await async_http_client.post(register_url, json=user_data)
```

### Route Name Mapping

Backend routes are defined with names in FastAPI:

```python
# api/routes/auth.py
@router.post("/login", name="auth_login")
@router.post("/register", name="auth_register")

# api/routes/videos.py
@router.get("/", name="videos_list")
@router.post("/upload", name="video_upload")
```

### Implementation Plan

#### Phase 1: Document Route Names ✅ COMPLETE (1 hour)

- [x] Create `docs/ROUTE_NAMES.md` mapping all route names to paths
- [x] Document naming conventions (e.g., `{feature}_{action}`)
- [x] List all FastAPI route names using:
  ```bash
  grep -r "@router.*name=" api/routes/ --include="*.py"
  ```
- [x] Identified 40+ named routes across all modules
- [x] Identified 10+ routes without names (SRT, WebSocket, Debug, Test routes)
- [x] Created comprehensive reference documentation with examples

#### Phase 2: Update Auth Tests (2-3 hours)

- [ ] Update `tests/api/test_auth_*.py` files (~8 files)
- [ ] Replace hardcoded `/api/auth/*` with `url_builder.url_for()`
- [ ] Verify all tests pass

#### Phase 3: Update Vocabulary Tests (2-3 hours)

- [ ] Update `tests/api/test_vocabulary_*.py` files (~5 files)
- [ ] Replace hardcoded `/api/vocabulary/*` paths
- [ ] Verify all tests pass

#### Phase 4: Update Video Tests (1-2 hours)

- [ ] Update `tests/api/test_video_*.py` files (~6 files)
- [ ] Replace hardcoded `/api/videos/*` paths

#### Phase 5: Update Processing Tests (2-3 hours)

- [ ] Update `tests/api/test_processing_*.py` files (~4 files)
- [ ] Replace hardcoded `/api/process/*` paths

#### Phase 6: Update Integration Tests (3-4 hours)

- [ ] Update `tests/integration/test_*.py` files (~20 files with API calls)
- [ ] Replace hardcoded paths
- [ ] Verify integration tests pass

#### Phase 7: Update Game/User Tests (1-2 hours)

- [ ] Update remaining test files
- [ ] Final verification

#### Phase 8: Create Migration Helper (1 hour)

- [ ] Create script to find remaining hardcoded paths
- [ ] Add pre-commit hook to warn about hardcoded `/api/` in new tests

### Total Estimated Effort

**Frontend**: 1 hour ✅ COMPLETE
**Backend Phase 1 (Documentation)**: 1 hour ✅ COMPLETE
**Backend Phases 2-8 (Test Migration)**: 12-19 hours ⏳ REMAINING

**Total for Task 9**: 14-21 hours (vs. original estimate of 4-6 hours)
**Completed So Far**: 2 hours
**Remaining**: 12-19 hours

---

## Benefits of Completion

### Type Safety

- Route name changes cause test failures (compile-time errors)
- Hardcoded paths silently break (runtime errors)

### Maintainability

- Refactor routes without updating dozens of test files
- Route name changes detected by TypeScript/Python type checkers

### Developer Experience

- Autocomplete for route names in IDEs
- Clear documentation of available routes

---

## Migration Strategy

### Incremental Approach (Recommended)

1. **New Tests**: Require `url_builder` usage (add to linting rules)
2. **Existing Tests**: Migrate file-by-file as they're modified
3. **Critical Paths**: Prioritize auth, vocabulary, video tests (most frequently changed)

### Big Bang Approach (Not Recommended)

- Update all 410 occurrences at once
- High risk of breaking tests
- Difficult to review changes

---

## Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
- id: check-hardcoded-api-paths
  name: Check for hardcoded API paths in tests
  entry: bash -c 'grep -r "/api/" tests/ --include="*.py" && echo "Use url_builder instead of hardcoded paths" && exit 1 || exit 0'
  language: system
  pass_filenames: false
```

---

## Route Name Documentation Template

Create `docs/ROUTE_NAMES.md`:

```markdown
# FastAPI Route Names Reference

## Authentication Routes

- `auth_login` → POST /api/auth/login
- `auth_register` → POST /api/auth/register
- `auth_logout` → POST /api/auth/logout
- `auth_refresh_token` → POST /api/auth/token/refresh
- `auth_get_current_user` → GET /api/auth/me

## Video Routes

- `videos_list` → GET /api/videos
- `video_upload` → POST /api/videos/upload
- `video_stream` → GET /api/videos/stream/{video_id}
  ...
```

---

## Testing the Migration

### Verify Route Names Exist

```python
def test_all_route_names_valid(app, url_builder):
    """Ensure all documented route names are valid."""
    route_names = [
        "auth_login",
        "auth_register",
        "videos_list",
        # ... all route names
    ]
    for name in route_names:
        try:
            url = url_builder.url_for(name)
            assert url.startswith("/api/")
        except NoRouteFound:
            pytest.fail(f"Route name '{name}' not found")
```

---

## Completion Criteria

- [ ] All test files use `url_builder` for API paths
- [ ] Zero occurrences of hardcoded `"/api/"` in test files (except route name mapping)
- [ ] All tests pass
- [ ] Pre-commit hook prevents new hardcoded paths
- [ ] `docs/ROUTE_NAMES.md` documents all route names

---

## Related Files

**Backend**:

- `tests/conftest.py` - URLBuilder fixture
- `api/routes/*` - Route definitions with names
- `tests/api/*` - API contract tests (primary targets)
- `tests/integration/*` - Integration tests with API calls

**Frontend**:

- `src/config/api-endpoints.ts` - Centralized endpoint configuration (completed)
- `src/utils/srtApi.ts` - Updated to use centralized config (completed)

---

## Status

**Frontend**: ✅ Complete (1 hour)
**Backend Phase 1**: ✅ Complete (1 hour) - Route name documentation created
**Backend Phases 2-8**: ⏳ Remaining (12-19 hours)

**Total Progress**: 2/14-21 hours complete (14%)

**Next Steps**:

- Begin Phase 2 (Update Auth Tests) - 8 files, 2-3 hours estimated
- See `docs/ROUTE_NAMES.md` for complete route name reference
