# LangPlug Refactoring Roadmap

## Executive Summary

This document outlines refactoring tasks categorized by priority. Many improvements have already been partially implemented but need completion.

---

## ✅ COMPLETED (This Session)

### Code Simplification

- ✅ Deleted `AuthenticatedUserVocabularyService` redundant wrapper (~350 lines)
- ✅ Removed duplicate `LoggingMiddleware` (~30 lines)
- ✅ Deleted legacy `services/filtering/` directory (~500 lines)
- ✅ Removed manual retry logic in frontend (~20 lines)
- ✅ Created centralized error formatter utility

**Total Code Reduction**: ~950 lines removed
**Fail-Fast Improvements**: Removed fallbacks hiding real errors

---

## 🔴 HIGH PRIORITY

### 1. Centralize API Path Definitions

#### Backend Tests - **PARTIALLY DONE**

**Status**: `SimpleURLBuilder` exists in `conftest.py` but not fully adopted

**Current State**:

```python
# conftest.py has this:
class SimpleURLBuilder:
    _routes = {
        "auth_register": "/api/auth/register",
        "auth_login": "/api/auth/login",
        ...
    }
    def url_for(self, route_name: str, **path_params) -> str:
        ...
```

**Problem**: Tests still use hardcoded paths like:

```python
response = await async_client.get("/api/vocabulary/stats")  # ❌ Hardcoded
```

**Solution**: Use `url_for` everywhere:

```python
response = await async_client.get(url_builder.url_for("get_vocabulary_stats"))  # ✅
```

**Better Solution**: Use FastAPI's built-in `app.url_path_for()`:

```python
# In conftest.py fixture
@pytest.fixture
def api_urls(app):
    """Generate URLs using FastAPI's url_path_for"""
    def url_for(route_name: str, **path_params):
        return app.url_path_for(route_name, **path_params)
    return url_for

# In tests
response = await async_client.get(api_urls("get_vocabulary_stats"))
```

**Files to Update**:

- `Backend/tests/security/test_api_security.py` (22 hardcoded paths)
- `Backend/tests/unit/test_vocabulary_routes.py` (26 hardcoded paths)
- `Backend/tests/api/test_*.py` (various files)

**Estimated Impact**: ~50-70 test files need updates

---

#### Frontend - **MOSTLY DONE** ✅

**Status**: 95% compliant - uses generated client

**Only Issue Found**:

```typescript
// Frontend/src/utils/srtApi.ts
constructor(baseUrl = '/api/srt') {  // ❌ Only hardcoded path found
```

**Action**: Either:

1. Add `/api/srt` to OpenAPI spec and regenerate client
2. Or document this as intentional exception (if it's a static resource)

---

### 2. Unify Validation Logic

#### Current State Analysis

**Backend** (Single Source of Truth ✅):

```python
# Backend uses Pydantic models correctly
class UserRegister(BaseModel):
    email: EmailStr = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    username: str | None = Field(None, min_length=3, max_length=50)
```

**Frontend** (Manual Duplication ❌):

```typescript
// Frontend/src/components/auth/RegisterForm.tsx
const validateForm = () => {
  if (formData.email.length > 255) {  // ❌ Duplicates backend rule
    errors.email = 'Email must be less than 255 characters'
  }
  if (formData.password.length < 8) {  // ❌ Duplicates backend rule
    errors.password = 'Password must be at least 8 characters'
  }
  ...
}
```

**Problem**: Frontend validation rules are manually duplicated and can drift from backend.

---

#### Solution: Generate Zod Schemas from OpenAPI

**Step 1**: Install schema generator

```bash
cd Frontend
npm install openapi-zod-client
```

**Step 2**: Add generation script to `package.json`:

```json
{
  "scripts": {
    "generate:schemas": "openapi-zod-client http://localhost:8000/openapi.json -o src/schemas/api-schemas.ts"
  }
}
```

**Step 3**: Generated schema will look like:

```typescript
// Auto-generated from OpenAPI
export const UserRegisterSchema = z.object({
  email: z.string().email().max(255),
  password: z.string().min(8).max(128),
  username: z.string().min(3).max(50).optional(),
});
```

**Step 4**: Use in `RegisterForm.tsx`:

```typescript
import { UserRegisterSchema } from "@/schemas/api-schemas";

const validateForm = () => {
  try {
    UserRegisterSchema.parse(formData); // ✅ Single source of truth
    return {};
  } catch (error) {
    return zodErrorToFormErrors(error);
  }
};
```

**Benefits**:

- ✅ Frontend/backend validation always in sync
- ✅ Type-safe
- ✅ Generated automatically
- ✅ No manual duplication

---

#### Email vs Username Clarification

**Investigation Needed**:

```python
# Backend model has BOTH email and username
class UserRegister(BaseModel):
    email: EmailStr
    username: str | None  # Optional?
```

**Questions**:

1. Is username optional or required?
2. Do users log in with email or username?
3. Should username be removed if not used?

**Recommendation**:

- If email-only login → Remove `username` field entirely
- If username login → Make `username` required, document clearly

---

## 🟡 MEDIUM PRIORITY

### 3. Review Configuration Files

#### Current Files:

```
.env.example              # Template
.env.production           # Production settings
Backend/.env.testing      # Test settings
Backend/core/config.py    # Settings loader
```

**Issues**:

1. Duplication between files
2. No clear documentation of which file is used when
3. Possible conflicts

**Action Items**:

1. Create `docs/CONFIGURATION.md` documenting each file's purpose
2. Audit for duplicated/conflicting settings
3. Consider consolidating test-specific overrides into `conftest.py` environment setup

---

### 4. Standardize Database Schema Access

**Problem**: Hardcoded table/column names scattered in codebase.

**Bad Pattern**:

```python
# ❌ Hardcoded table name
query = "SELECT * FROM users WHERE email = ?"

# ❌ Hardcoded column name
result = db.execute(f"SELECT {col} FROM {table}")
```

**Good Pattern**:

```python
# ✅ Use SQLAlchemy models
from database.models import User

query = select(User).where(User.email == email)
column_name = User.email.key
table_name = User.__tablename__
```

**Search Pattern**:

```bash
# Find potential hardcoded references
grep -r "\"users\"" Backend/
grep -r "'vocabulary'" Backend/
grep -r "SELECT.*FROM" Backend/
```

**Estimated**: ~20-30 locations to review

---

## 🟢 LOW PRIORITY

### 5. Centralize User Roles

**Current Pattern** (if roles exist as strings):

```python
# ❌ String typos possible
if user.role == "admin":
if user.role == "admn":   # Typo!
```

**Better Pattern**:

```python
# ✅ Enum prevents typos
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"

if user.role == UserRole.ADMIN:  # Type-safe
```

**Search for Roles**:

```bash
grep -r "role.*=.*['\"]" Backend/database/models.py
grep -r "user.*role" Backend/
```

---

## 📋 Implementation Plan

### Phase 1: High-Impact, Low-Risk (Week 1)

- [x] Code simplification (DONE)
- [ ] Frontend: Fix srtApi hardcoded path
- [ ] Backend: Update SimpleURLBuilder with ALL routes
- [ ] Document email vs username usage

### Phase 2: Validation Unification (Week 2)

- [ ] Install openapi-zod-client
- [ ] Generate Zod schemas
- [ ] Refactor RegisterForm.tsx
- [ ] Test validation parity
- [ ] Update other forms

### Phase 3: Test Refactoring (Week 3-4)

- [ ] Create pytest fixture using `app.url_path_for()`
- [ ] Batch update test files with url_for
- [ ] Run full test suite to verify

### Phase 4: Configuration & Schema (Week 5)

- [ ] Document configuration files
- [ ] Audit for schema hardcoding
- [ ] Centralize user roles (if applicable)

---

## 🎯 Success Metrics

| Metric                      | Before | Target   |
| --------------------------- | ------ | -------- |
| Hardcoded paths in tests    | ~70    | 0        |
| Hardcoded paths in frontend | 1      | 0        |
| Validation duplication      | Yes    | No       |
| Config documentation        | None   | Complete |
| User role typo risk         | High   | Zero     |

---

## ⚠️ Risks & Mitigations

| Risk                           | Mitigation                                |
| ------------------------------ | ----------------------------------------- |
| Breaking tests during refactor | Update in batches, run tests after each   |
| Schema generation issues       | Test with small model first, then expand  |
| Configuration conflicts        | Review all env files before consolidation |
| Time investment                | Prioritize high-impact items first        |

---

## 📚 References

- FastAPI URL Path For: https://www.starlette.io/routing/#reverse-url-lookups
- OpenAPI Zod Client: https://github.com/astahmer/openapi-zod-client
- Pydantic Validation: https://docs.pydantic.dev/latest/concepts/validators/

---

## Next Steps

**Immediate Actions**:

1. Review this roadmap with team
2. Prioritize which phase to tackle first
3. Create GitHub issues for tracking
4. Assign ownership

**Quick Wins** (< 1 hour each):

- Fix `srtApi.ts` hardcoded path
- Document email/username usage
- Create `CONFIGURATION.md`
- Search for user roles and create enum if needed
