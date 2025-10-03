# DTO (Data Transfer Object) Standards

## Purpose

DTOs provide clean separation between:

- **API Layer**: Request/Response models for HTTP endpoints
- **Domain Layer**: Business logic and service models
- **Database Layer**: ORM models (SQLAlchemy)

## Directory Structure

```
api/
├── dtos/              # Centralized DTO definitions
│   ├── __init__.py   # Export all DTOs
│   ├── auth_dto.py
│   ├── video_dto.py
│   ├── vocabulary_dto.py
│   ├── game_dto.py
│   ├── progress_dto.py
│   ├── user_profile_dto.py
│   └── srt_dto.py
├── routes/            # API route handlers (thin layer)
│   ├── auth.py
│   ├── videos.py
│   └── ...
└── models/            # DEPRECATED - Use dtos/ instead
```

## Naming Conventions

### Response DTOs

Use `EntityNameDTO` suffix for response models:

```python
class UserDTO(BaseModel):
    """DTO for user representation"""
    id: int
    username: str
    email: str
```

### Request DTOs

Use `EntityNameRequest` suffix for request models:

```python
class UpdateProfileRequest(BaseModel):
    """DTO for profile update request"""
    email: str | None
    level: str | None
```

### Avoid

- ❌ `EntityResponse`, `EntityModel` (unclear)
- ❌ Inline definitions in route files
- ❌ Mixing DTOs with database models

## DTO Structure

### Basic Template

```python
"""
Entity Data Transfer Objects
API request/response models for entity management
"""

from pydantic import BaseModel, Field, ConfigDict


class EntityDTO(BaseModel):
    """DTO for entity representation"""

    model_config = ConfigDict(from_attributes=True)  # Enable ORM mode

    id: int = Field(..., description="Unique identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Entity name")
    is_active: bool = Field(default=True, description="Active status")


class CreateEntityRequest(BaseModel):
    """DTO for entity creation request"""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)


class UpdateEntityRequest(BaseModel):
    """DTO for entity update request"""

    name: str | None = Field(None, min_length=1, max_length=100)
    is_active: bool | None = None
```

### Field Documentation

Always include descriptions for API documentation:

```python
class UserDTO(BaseModel):
    id: int = Field(..., description="Unique user identifier")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: str = Field(..., description="Email address")
```

### Validation

Use Pydantic validators for business rules:

```python
from pydantic import field_validator

class RegisterRequest(BaseModel):
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain uppercase")
        return v
```

## Route Integration

### Import from DTOs

```python
from api.dtos import UserDTO, UpdateProfileRequest

@router.get("/profile", response_model=UserDTO)
async def get_profile(
    current_user: User = Depends(current_active_user)
):
    return UserDTO.model_validate(current_user)


@router.put("/profile", response_model=UserDTO)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(current_active_user)
):
    # Update logic
    return UserDTO.model_validate(updated_user)
```

### ORM Conversion

Use `model_validate` for ORM → DTO conversion:

```python
# From database model
user_dto = UserDTO.model_validate(user)  # Requires from_attributes=True

# From dict
user_dto = UserDTO(**user_dict)

# To dict
user_dict = user_dto.model_dump()
```

## Organization Guidelines

### Group by Domain

Each DTO file should contain related models:

```python
# video_dto.py
class VideoInfoDTO(BaseModel): ...
class ProcessingStatusDTO(BaseModel): ...
class UploadVideoRequest(BaseModel): ...
```

### Single Responsibility

One DTO per use case:

- ✅ `CreateUserRequest`, `UpdateUserRequest`, `UserDTO`
- ❌ `UserRequest` (ambiguous - create or update?)

### Reusability

Extract common patterns:

```python
class PaginationParams(BaseModel):
    """Reusable pagination parameters"""
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class PaginatedResponse(BaseModel, Generic[T]):
    """Reusable paginated response wrapper"""
    items: list[T]
    total: int
    limit: int
    offset: int
```

## Migration Path

### For New Routes

1. Create DTOs in `api/dtos/entity_dto.py`
2. Export from `api/dtos/__init__.py`
3. Import in route: `from api.dtos import EntityDTO`

### For Existing Routes

1. Identify inline BaseModel classes in route files
2. Move to appropriate DTO file in `api/dtos/`
3. Update imports in route file
4. Remove inline definitions
5. Test endpoint still works

Example:

```python
# Before (inline DTO in route file)
# api/routes/videos.py
class ProcessingStatus(BaseModel):
    status: str
    progress: float

# After (centralized DTO)
# api/dtos/video_dto.py
class ProcessingStatusDTO(BaseModel):
    status: str = Field(..., description="Status")
    progress: float = Field(..., ge=0, le=100, description="Progress %")

# api/routes/videos.py
from api.dtos import ProcessingStatusDTO
```

## Common Patterns

### Optional Fields for Updates

```python
class UpdateEntityRequest(BaseModel):
    """All fields optional for partial updates"""
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None
```

### Nested DTOs

```python
class AddressDTO(BaseModel):
    street: str
    city: str
    country: str


class UserDTO(BaseModel):
    id: int
    name: str
    address: AddressDTO  # Nested DTO
```

### List Responses

```python
class VideoListResponse(BaseModel):
    videos: list[VideoInfoDTO]
    total_count: int
```

## Anti-Patterns to Avoid

### ❌ DTOs in Multiple Locations

```python
# DON'T: Split DTOs across dtos/ and models/
api/dtos/user_dto.py      # UserDTO
api/models/user.py        # UserResponse (duplicate!)
```

### ❌ Mixing Layers

```python
# DON'T: Import database models in route responses
from database.models import User  # ORM model

@router.get("/users", response_model=User)  # Wrong!
```

### ❌ Overly Generic Names

```python
# DON'T: Ambiguous class names
class Request(BaseModel): ...  # Too generic
class Data(BaseModel): ...     # Meaningless
```

### ❌ Inline Route DTOs

```python
# DON'T: Define DTOs inside route files
# api/routes/videos.py
class VideoInfo(BaseModel):  # Should be in dtos/
    ...
```

## Benefits

1. **Type Safety**: Pydantic validation at API boundary
2. **Documentation**: Auto-generated OpenAPI schemas
3. **Separation**: Clean layers (API ≠ Domain ≠ Database)
4. **Maintainability**: Central DTO location
5. **Testability**: Easy to mock/test DTOs
6. **Versioning**: Can version DTOs independently

## References

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [FastAPI Response Models](https://fastapi.tiangolo.com/tutorial/response-model/)
- Backend architecture: `docs/ARCHITECTURE_OVERVIEW.md`
