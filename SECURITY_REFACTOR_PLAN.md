# Grand Security & Architecture Refactoring Plan

**Objective:** Transition LangPlug from a "prototypical" security model (localStorage tokens, in-memory limits) to a production-ready, secure architecture (HttpOnly cookies, Redis rate limiting, unified API client).

**Scope:**
- **H-04 / H-09:** Secure Video Streaming (No tokens in URLs).
- **H-08:** HttpOnly Cookie Authentication (XSS Protection).
- **H-05:** Unified Auth Interceptor (Consistency).
- **H-07:** Redis Rate Limiting (Scalability).

---

## Phase 1: Infrastructure & Rate Limiting (Backend)
**Goal:** Establish the infrastructure for scalable security without breaking existing auth.

### 1.1 Implement Redis Rate Limiting (H-07)
- [ ] **Add Redis Dependency:** Update `src/backend/core/dependencies.py` or similar to provide a `get_redis_client` dependency.
- [ ] **Update Middleware:** Modify `RateLimitMiddleware` in `src/backend/core/security/security_middleware.py`.
    - Replace `defaultdict` in-memory storage with Redis calls.
    - Implement "Token Bucket" or "Fixed Window" algorithm using Redis keys (e.g., `rate_limit:{ip}`).
    - **Fallback:** Ensure it degrades gracefully to in-memory if Redis is down (optional, or hard fail depending on policy).
- [ ] **Configuration:** Ensure `REDIS_URL` is loaded from `Settings`.

---

## Phase 2: Frontend API Client Unification (Frontend)
**Goal:** Eliminate "rogue" `fetch` calls to prepare for a single switch to cookie-based auth.

### 2.1 Standardize API Calls (H-05)
- [ ] **Audit:** Find all usages of native `fetch()` in `src/frontend`.
    - Targeted areas: `useSubtitleSystem`, `auth-interceptor.ts`.
- [ ] **Refactor `auth-interceptor.ts`:**
    - Ensure the refresh logic uses the underlying Axios instance or a separate *clean* Axios instance, not `fetch`.
- [ ] **Refactor Data Fetching:**
    - Convert any direct `fetch` calls to use the `OpenAPI` generated client or the configured Axios instance.
    - This ensures that when we switch to "credentials: include", *all* requests respect it.

---

## Phase 3: The "Cookie Switch" (Full Stack)
**Goal:** Move authentication state from client-side storage to secure, server-managed cookies.

### 3.1 Backend: Enable Cookie Transport
- [ ] **Update `src/backend/core/auth/auth.py`:**
    - Configure `CookieTransport` for `fastapi_users`.
    - Set `cookie_httponly=True`, `cookie_secure=True` (prod), `cookie_samesite='lax'` or `'none'`.
    - **Dual Mode (Transitional):** Temporarily keep `BearerTransport` active if possible, or prepare for a hard cutover.
- [ ] **Update Login Route:**
    - The `/auth/login` endpoint should now set the `fastapiusersauth` cookie.
- [ ] **CORS Configuration:**
    - In `src/backend/core/config/config.py`, ensure `allow_credentials=True`.
    - Verify `allow_origins` contains the exact frontend origin (wildcards `*` are not allowed with credentials).

### 3.2 Frontend: Switch to Cookies (H-08)
- [ ] **Update `src/frontend/src/client/core/OpenAPI.ts` (or config):**
    - Set `OpenAPI.WITH_CREDENTIALS = true;`.
- [ ] **Remove Token Logic:**
    - Delete code that reads/writes `localStorage.getItem('authToken')`.
    - Remove the request interceptor that manually attaches `Authorization: Bearer ...`.
- [ ] **Update Auth Store:**
    - `useAuthStore` should no longer persist tokens. It should only track `isAuthenticated` and `user` profile.
    - "Login" action now just calls the API (which sets the cookie) and updates state.
    - "Logout" action calls the API (which clears the cookie) and clears state.

---

## Phase 4: Secure Video Streaming (H-04 / H-09)
**Goal:** Secure media delivery now that cookies are established.

### 4.1 Backend: Cookie-Based Video Access
- [ ] **Verify `stream_video` Route:**
    - Ensure `src/backend/api/routes/videos.py` uses a dependency that checks cookies, not just the Authorization header.
    - `fastapi-users` usually handles this transparently if the backend is configured with `CookieTransport`.

### 4.2 Frontend: Remove Query Params
- [ ] **Update `api.ts`:**
    - Modify `buildVideoStreamUrl` to remove `?token=...`.
    - Since the browser automatically sends cookies for `<video src="...">` requests to the same domain (or valid CORS domain), the video should play securely.
- [ ] **Testing:** Verify `ReactPlayer` works with cookies (it relies on the browser's native handling).

### 4.3 (Fallback) Signed URLs
- *Trigger:* If `ReactPlayer` / Cross-Domain issues prevent cookie auth for video tags.
- [ ] Create `GET /api/videos/{id}/sign` endpoint.
- [ ] Generate a URL with a short-lived (e.g., 1-minute) HMAC signature.
- [ ] Update Frontend to fetch signed URL before rendering the player.

---

## Execution Order & Rollback Strategy
1.  **Phase 1** can be done immediately.
2.  **Phase 2** is a prerequisite for Phase 3.
3.  **Phase 3 & 4** should be done together in a feature branch.
    - **Rollback:** If Cookie auth fails, revert the Frontend `OpenAPI` config and Backend `auth.py` changes to restore Bearer token logic.
