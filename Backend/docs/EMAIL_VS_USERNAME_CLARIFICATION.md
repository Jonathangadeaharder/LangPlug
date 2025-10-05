# Email vs Username Authentication Clarification

**Created**: 2025-10-05
**Purpose**: Document the email/username authentication pattern in LangPlug

---

## Executive Summary

LangPlug uses **email-based authentication** with an additional **username field for display purposes**. The login form field labeled "username" actually expects and uses the email address for authentication.

---

## Current Authentication Flow

### Registration

**Required Fields**:

- `username`: String (3-50 chars, alphanumeric with `_` and `-`)
- `email`: EmailStr (unique, used for authentication)
- `password`: String (validated for strength)

**Implementation**: `core/auth.py` - `UserCreate` schema

```python
class UserCreate(BaseUserCreate):
    username: str  # Display name
    email: EmailStr  # Authentication credential
    password: str
```

### Login

**Form Fields**:

- `username`: Actually contains the **email address** (FastAPI-Users convention)
- `password`: User's password

**Implementation**: FastAPI-Users default OAuth2PasswordRequestForm

```python
# Test helper shows the pattern (tests/auth_helpers.py)
login_data = {
    "username": email,  # FastAPI-Users expects email in username field
    "password": password,
}
```

**Why "username" field?**: FastAPI-Users uses OAuth2PasswordRequestForm which has a field called `username` by convention. However, the actual authentication lookup uses the `email` field from the database.

### User Lookup

**Database Model** (`database/models.py`):

```python
class User(Base):
    id: int  # Primary key
    email: str  # Used for authentication (unique, indexed)
    username: str  # Used for display (unique, indexed)
    # ... other fields
```

**Authentication Flow**:

1. User submits login form with email in "username" field
2. FastAPI-Users SQLAlchemyUserDatabase looks up user by `email` field
3. Password is verified
4. JWT token is issued

---

## Key Findings

### Username Field Usage

**Used For**:

- User display name in UI (`UserResponse.username`)
- User identification in frontend
- Optional user-facing identifier

**NOT Used For**:

- Authentication/login (email is used)
- Primary user lookup in auth flow

**Database Queries**:

- `user_repository.py` has `get_by_username()` method (line 21)
- `auth_service.py` has username-based queries (lines 184, 249)
- However, FastAPI-Users authentication uses email lookup

### Email Field Usage

**Used For**:

- Primary authentication credential (login)
- User identification in FastAPI-Users
- Unique user identifier
- Password reset flows

---

## Naming Confusion

### Current Confusion Points

1. **Login Form Field Name**: "username" field actually expects email
   - Frontend: `login(email, password)` → sends `{username: email, password}`
   - Backend: Receives `username` field, looks up by email

2. **API Models Mismatch**:
   - `api/models/auth.py` has `LoginRequest` with `username` field
   - But actual authentication uses email from database

3. **Test Documentation**:
   - Tests use "username" in form data but pass email value
   - Comment clarifies: "FastAPI-Users expects email in username field"

---

## Recommendations

### Option 1: Keep Current System (Recommended)

**Rationale**:

- FastAPI-Users is designed for email-based authentication
- Both fields are used (email for auth, username for display)
- Changing would require significant refactoring

**Action Items**:

- ✅ Document the email/username pattern (this file)
- ✅ Add code comments explaining the "username" field expects email
- ✅ Update API documentation to clarify login uses email
- ✅ Add frontend documentation explaining the pattern

### Option 2: Use Username-Only (Not Recommended)

**Requires**:

- Override FastAPI-Users authentication to use username
- Remove email field from database
- Update all user identification flows

**Issues**:

- Loses email functionality (password reset, notifications)
- Conflicts with FastAPI-Users design
- High refactoring effort

### Option 3: Use Email-Only (Not Recommended)

**Requires**:

- Remove username field
- Update all display logic to use email
- Update frontend components

**Issues**:

- Email addresses as display names are not user-friendly
- Less flexibility for user identification
- Moderate refactoring effort

---

## Implementation Details

### Frontend (React/TypeScript)

**Login Flow** (`src/store/useAuthStore.ts`):

```typescript
login: async (email: string, password: string) => {
  // API client sends: {username: email, password}
  await authApi.login({ username: email, password });
};
```

**Register Flow**:

```typescript
register: async (username: string, email: string, password: string) => {
  await authApi.register({ username, email, password });
};
```

### Backend (FastAPI/Python)

**Registration** (`core/auth.py`):

- FastAPI-Users creates user with both username and email
- Both fields stored in database

**Authentication** (`core/auth.py`):

- FastAPI-Users SQLAlchemyUserDatabase
- Default behavior: lookup by email field
- OAuth2PasswordRequestForm provides "username" field (contains email)

---

## Testing Patterns

**Correct Test Pattern** (`tests/auth_helpers.py`):

```python
def login_user(self, email: str, password: str) -> tuple[int, dict]:
    login_data = {
        "username": email,  # FastAPI-Users expects email in username field
        "password": password,
    }
    response = self.client.post("/api/auth/login", data=login_data)
    return response.status_code, response.json()
```

**Registration Test**:

```python
def register_user(self, user_data: dict) -> tuple[int, dict]:
    # user_data = {"username": "john_doe", "email": "john@example.com", "password": "..."}
    response = self.client.post("/api/auth/register", json=user_data)
    return response.status_code, response.json()
```

---

## API Documentation Updates

### POST /api/auth/login

**Request Body** (form-encoded):

```json
{
  "username": "user@example.com", // Actually email address
  "password": "SecurePass123!"
}
```

**Note**: The "username" field must contain the user's **email address**, not their display username. This is a FastAPI-Users/OAuth2 convention.

### POST /api/auth/register

**Request Body** (JSON):

```json
{
  "username": "john_doe", // Display name
  "email": "john@example.com", // Authentication credential
  "password": "SecurePass123!"
}
```

Both `username` and `email` are required and must be unique.

---

## Related Files

**Backend**:

- `core/auth.py` - FastAPI-Users setup, UserCreate/UserRead schemas
- `api/models/auth.py` - API request/response models
- `database/models.py` - User database model
- `tests/auth_helpers.py` - Authentication test utilities

**Frontend**:

- `src/store/useAuthStore.ts` - Auth state management
- `src/components/auth/LoginForm.tsx` - Login UI
- `src/services/api-client.ts` - API communication

---

## Migration Guide

If in the future we decide to change the authentication pattern:

### To Username-Only Authentication

1. Override `UserManager.authenticate()` in `core/auth.py`
2. Update SQLAlchemyUserDatabase to use username field
3. Remove email field from UserCreate/UserRead
4. Update database migration to remove email column
5. Update all tests and documentation

### To Email-Only Authentication

1. Remove username from UserCreate/UserRead
2. Update UserResponse to use email for display
3. Update frontend to display email instead of username
4. Update database migration to remove username column
5. Update all tests and documentation

---

## Conclusion

The current system uses **email-based authentication** with **username for display**. The "username" field in the login form is a naming artifact from OAuth2PasswordRequestForm and actually expects the email address.

This pattern is standard for FastAPI-Users and should be documented rather than changed.

**Decision**: ✅ Keep current system, document the pattern clearly

**Status**: Documented 2025-10-05
