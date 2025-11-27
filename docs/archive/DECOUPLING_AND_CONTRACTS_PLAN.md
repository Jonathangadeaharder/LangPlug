# LangPlug System Decoupling & Design by Contract Plan

## 1. Executive Summary

To ensure long-term maintainability and robustness, LangPlug will evolve from a tightly coupled monolith to a modular, layered architecture enforced by strict API contracts. This plan outlines the steps to decouple business logic from API routes, standardize communication interfaces, and rigorously test contract fulfillment.

---

## 2. Architecture Refactoring (Decoupling)

### 2.1. Layered Architecture Adoption
Move away from "Fat Routes" to a strict layered approach:

*   **Presentation Layer (API Routes)**:
    *   Responsibility: Validation (Pydantic), Request parsing, Response serialization.
    *   Constraint: NO business logic. NO direct DB access. ONLY calls Service Layer.
*   **Service Layer (Core Logic)**:
    *   Responsibility: Orchestration, Business Rules, Transaction management.
    *   Constraint: DB access only via Repositories. External API calls via Adapters.
*   **Data Access Layer (Repositories)**:
    *   Responsibility: CRUD operations, Query optimization.
    *   Constraint: Returns Domain Models, not ORM models (where feasible).

### 2.2. Proper Dependency Injection (DI)
Refactor imperative dependency calls to declarative FastAPI injections.

**Current (Bad):**
```python
@router.post("/transcribe")
async def transcribe(...):
    service = get_transcription_service()  # Hard to mock
    # ... logic ...
```

**Target (Good):**
```python
@router.post("/transcribe")
async def transcribe(
    request: TranscribeRequest,
    service: ITranscriptionService = Depends(get_transcription_service)
):
    return await service.transcribe(request)
```

### 2.3. Event-Driven Background Tasks
Decouple long-running processes (transcription, translation) using an internal Event Bus or Task Service wrapper instead of raw `BackgroundTasks`.

*   **Pattern**: `TaskService.submit(task_type, payload)`
*   **Benefit**: Allows switching backend (In-Process -> Redis/Celery) without changing routes. Allows synchronous execution in tests.

---

## 3. Design by Contract (DbC) Strategy

### 3.1. Strict Pydantic Schemas
Every endpoint must have explicit Request and Response models.

*   **Requirement**: No returning `dict`. Always return a Pydantic `BaseModel`.
*   **Benefit**: Auto-generated Swagger docs are accurate; Frontend client generation works perfectly.

**Example:**
```python
class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    estimated_completion: datetime | None = None

@router.post(..., response_model=TaskResponse)
```

### 3.2. Standardized Error Contracts
Define a uniform error response structure for the entire API.

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Video file could not be found.",
    "details": { "path": "..." },
    "timestamp": "..."
  }
}
```
*   **Action**: Update `exception_handlers.py` to map exceptions to this schema.
*   **Action**: Frontend `formatApiError` updated to handle this standard.

### 3.3. Single Source of Truth
The Backend Pydantic Models are the Truth.
*   **Frontend**: Auto-generate TypeScript interfaces using `openapi-typescript-codegen` in CI pipeline.
*   **Versioning**: Breaking changes in Pydantic models trigger CI failures if frontend isn't updated.

---

## 4. Testing Contract Fulfillment

### 4.1. Schema-Based Fuzz Testing (Schemathesis)
Implement `schemathesis` to attack the API based on OpenAPI specs.
*   **What it does**: Generates random valid/invalid inputs based on schema.
*   **What it checks**:
    *   Does endpoint crash (500)?
    *   Does endpoint return undocumented status codes?
    *   Does response structure match schema?

### 4.2. Runtime Contract Validation
Enhance existing `ContractValidationMiddleware`:
*   **Strict Mode**: In `TESTING` env, raise Exception (500) on contract violation instead of just logging warning.
*   **Coverage**: Ensure `STANDARD_HTTP_CODES` whitelist isn't masking actual undocumented behavior.

### 4.3. Consumer-Driven Contracts (Lightweight)
*   **Frontend Tests**: Use Mock Service Worker (MSW) initialized with data *strictly matching* generated types. If tests compile but fail at runtime due to mocked data mismatch, contract is broken.

---

## 5. Implementation Roadmap

### Phase 1: Hardening the Interface (Week 1)
1.  [ ] Define standard `ErrorResponse` model.
2.  [ ] Audit all routes: Add `response_model` to every endpoint.
3.  [ ] Update `exception_handlers.py` to output standard errors.
4.  [ ] Refactor `ContractValidationMiddleware` to "Strict Mode".

### Phase 2: Refactoring Internals (Week 2)
1.  [ ] Create `VideoRepository` and `TranscriptionService` (Application Layer).
2.  [ ] Refactor `transcription_routes.py` to use DI (`Depends`).
3.  [ ] Refactor `video_routes.py` to move logic to Service.

### Phase 3: Advanced Testing (Week 3)
1.  [ ] Setup `schemathesis` in CI pipeline.
2.  [ ] Run fuzz tests against `whisper-tiny` backed endpoints.
3.  [ ] Verify Frontend client generation is automated on schema change.

---

## 6. Immediate Next Action
Start with **Phase 1, Step 2**: Audit `transcription_routes.py` and apply strict Request/Response models and proper DI.
