# LangPlug Grand Testability & Quality Plan

## 1. Philosophy: The "Testable by Design" Architecture

To make LangPlug reliable, we must move from "testing after coding" to "coding for testability." This requires architectural discipline.

### Core Principles
1.  **Determinism**: Remove randomness from tests. ML models (Whisper/Translation) must be mockable or configurable to deterministic "toy" versions (like `whisper-tiny`) or completely stubbed.
2.  **Isolation**: Tests must never share state.
    *   **Database**: Transactional rollbacks for integration tests.
    *   **Filesystem**: Use temporary directories (`tmp_path` fixture) for video uploads/processing.
3.  **Observability**: The application must expose its state to tests.
    *   **Frontend**: Mandatory `data-testid` attributes on interactive elements.
    *   **Backend**: Expose "Test Seams" (e.g., ability to trigger a background task synchronously).

---

## 2. Architecture Improvements for Testability

### Backend (FastAPI/Python)
*   **Dependency Injection (DI) Everywhere**: Never import `whisper` directly in routes. Inject `ITranscriptionService`.
    *   *Benefit*: Allows swapping `WhisperService` with `MockTranscriptionService` that returns immediate "Lorem Ipsum" results without GPU usage.
*   **Configuration-Driven Models**: We implemented `LANGPLUG_TRANSCRIPTION_SERVICE` env var. We must formalize this to allow a "No-Op" model for logic testing.
*   **Background Task Exposure**: Extract `BackgroundTasks` logic into a `TaskQueue` service that can be run synchronously in tests (avoiding `asyncio.sleep` loops).

### Frontend (React/Vite)
*   **Stable Selectors**: Enforce a lint rule or code review standard requiring `data-testid` on all:
    *   Inputs, Buttons, Links.
    *   Dynamic lists (e.g., `data-testid="word-card-{id}"`).
*   **API Client Generation**: Continue using `openapi-typescript-codegen` but mock the network layer in Unit/Component tests using MSW (Mock Service Worker) to test UI edge cases (network error, 500s) without killing the backend.

---

## 3. The Testing Pyramid Strategy

We will structure tests into three distinct layers.

### Layer 1: Unit Tests (Fast, Mocked, 70% of volume)
*   **Goal**: Validate logic in isolation. < 50ms per test.
*   **Backend**:
    *   Test `PasswordValidator`, `SubtitleParser`, `SpacedRepetitionAlgo`.
    *   **Crucial**: Mock database sessions. Do not hit SQLite.
*   **Frontend**:
    *   Test utility functions (`formatApiError`).
    *   Test individual components (`RegisterForm` validation logic) using React Testing Library.

### Layer 2: Integration Tests (Realistic, Isolated DB, 20% of volume)
*   **Goal**: Verify modules work together. < 500ms per test.
*   **Backend**:
    *   Use `TestClient` with `app.dependency_overrides`.
    *   Use a real SQLite file (created per test run) but override heavy services (Transcription).
    *   *Example*: Test the full "Register -> Login -> Get Token" flow.
*   **Frontend**:
    *   Component Integration tests (e.g., `VocabularyLibrary` loading data and rendering list).

### Layer 3: E2E Smoke Tests (Full Stack, "Golden Path", 10% of volume)
*   **Goal**: Verify user stories work on deployed/assembled app. Slower.
*   **Tooling**: Playwright.
*   **Configuration**:
    *   Backend runs with `whisper-tiny`.
    *   Database is seeded with known fixture data (e.g., "Superstore Episode 1").
*   **Scope**: Only critical paths (Login, Video Playback, Core Vocabulary Action).

---

## 4. Detailed Test Scenarios (What to Test)

### A. Authentication & Security
1.  **Registration**:
    *   Valid registration (Happy Path).
    *   Duplicate email (Error 400).
    *   Weak password (Error 422 - Verified Fix).
2.  **Session**:
    *   Login returns valid JWT.
    *   Access protected route without Token -> Redirect to Login.
    *   Token refresh flow (if implemented).
    *   Logout clears local storage.

### B. Video Processing (The Core Loop)
1.  **Ingestion**:
    *   Scanner detects new files in `videos/`.
    *   Scanner ignores non-video files.
2.  **Processing Pipeline**:
    *   **Audio Extraction**: Input MP4 -> Output WAV. Handle 0-byte file corruption gracefully.
    *   **Transcription**: WAV -> SRT. Validate timestamp formats.
    *   **Translation**: SRT (DE) -> SRT (ES/EN). Verify line counts match.
3.  **Playback**:
    *   Frontend requests video stream (Range headers).
    *   Frontend requests subtitles (VTT/SRT format).
    *   Video player syncs subtitles correctly.

### C. Vocabulary Learning
1.  **Library**:
    *   List loads with pagination.
    *   Search filters by word/lemma.
    *   Level tabs switch data sets (A1 -> A2).
2.  **Interaction**:
    *   Toggle "Known/Unknown". Verify persistence.
    *   "Mark All Known" action.
3.  **Context**:
    *   Clicking a word in Subtitles (during video) opens word modal. (Critical Feature).

### D. Performance (Non-Functional)
1.  **Startup Time**: Server ready < 5s.
2.  **Latency**: API responses < 200ms (p95) for non-ML endpoints.
3.  **Throughput**: Concurrent requests (e.g., 5 users hitting `/vocabulary`) don't deadlock.

---

## 5. Implementation Roadmap

### Step 1: Consolidate Test Runners
*   **Decision**: We currently have Python-based E2E (`tests/manual/smoke`) and TypeScript-based E2E (`tests/e2e`).
*   **Action**: Migrate all logic to **TypeScript Playwright (`tests/e2e`)** as the source of truth for E2E. It integrates better with the frontend ecosystem. Keep Python scripts only for backend-specific dev debugging.

### Step 2: Fix Infrastructure (Completed)
*   ✅ Enforce `whisper-tiny` for tests.
*   ✅ Fix video paths.
*   ✅ Fix frontend selectors (`data-testid`).

### Step 3: Add "Seeding" Capability
*   Create a script `scripts/seed_test_data.py` that:
    *   Drops DB.
    *   Creates User `e2etest`.
    *   Inserts "Mock Video" entries into DB (bypassing scanning/transcription) for pure frontend testing.

### Step 4: CI/CD Integration
*   Create `.github/workflows/test.yml`:
    1.  Install deps (Python + Node).
    2.  Run Backend Unit Tests (`pytest`).
    3.  Run Frontend Unit Tests (`npm test`).
    4.  Start Servers (Debug Mode).
    5.  Run Playwright E2E.

## 6. How to Run Tests (The "Standard")

**Unit/Integration (Fast):**
```bash
# Backend
cd src/backend
pytest tests/unit tests/integration

# Frontend
cd src/frontend
npm test
```

**E2E (Full Stack):**
```bash
# Root directory
# 1. Start Environment (with test config)
./scripts/start-all-debug.bat

# 2. Run Playwright (TypeScript Suite)
npx playwright test
```
