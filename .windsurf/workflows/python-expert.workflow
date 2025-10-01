---
description: Python language expert for specialized Python development tasks
auto_execution_mode: 3
---

## Workflow
- **Name**: python-expert
- **Description**: Python language expert for specialized Python development tasks

## Steps
1. **Type**: specialist
   - **language**: python
   - **description**: Invoke proactively when working with Python technologies
2. **Type**: apply
   - **description**: Leverage specialized knowledge for Python-specific best practices

## Triggers
- python-expert

## Requirements
- Language experts are available: python-expert, cpp-expert, csharp-expert, react-expert, plantuml-expert, latex-expert
- Invoke proactively when working with specific technologies
- Leverage specialized knowledge for language-specific best practices
- Keep changes minimal and focused; do not refactor unrelated code
- Follow existing naming and structure; no one-letter variables
- Avoid inline comments unless necessary for clarity

## Standards
- **naming**: snake_case everything except classes (PascalCase)
- **types**: Use type hints for parameters and returns
- **idioms**: List comprehensions, context managers, enumerate()
- **docs**: Docstrings for all public functions/classes
- **strings**: Prefer f-strings over .format() or % formatting

## Testing Standards

### AsyncMock Usage (CRITICAL)
**NEVER use AsyncMock for database result objects** - This is a critical anti-pattern that causes methods like `scalar()`, `scalars()`, `first()`, etc. to return coroutines instead of actual values.

**CORRECT Pattern for Database Mocking:**
```python
# For scalar() results
def create_mock_result(value):
    # Use Mock (NOT AsyncMock) for result since scalar() is synchronous
    mock_result = Mock()
    mock_result.scalar.return_value = value
    return mock_result

# execute() returns awaitable, so wrap results in async function
async def mock_execute_side_effect(*args):
    return mock_results.pop(0)

mock_results = [create_mock_result(100), create_mock_result(200)]
mock_session.execute.side_effect = mock_execute_side_effect

# For scalars().all() results
mock_scalars = Mock()  # NOT AsyncMock
mock_scalars.all.return_value = [mock_obj1, mock_obj2]

mock_result = Mock()  # NOT AsyncMock
mock_result.scalars.return_value = mock_scalars

async def mock_execute(*args):
    return mock_result

mock_session.execute.side_effect = mock_execute
```

**WRONG Pattern (DO NOT USE):**
```python
# WRONG - AsyncMock makes scalar() return a coroutine
mock_result = AsyncMock()
mock_result.scalar.return_value = value
mock_session.execute.return_value = mock_result
```

**Key Rule:** Use `Mock` for result objects, use async functions for `session.execute()` side effects
