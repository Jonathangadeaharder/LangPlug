# Test Coverage Improvement Plan

**Generated**: 2025-10-13
**Current Coverage**: 50.54% (backend unit tests), 58.63% (frontend)
**Target Coverage**: 80% minimum, 90% goal
**Priority**: Critical security and business logic first

---

## Executive Summary

This plan addresses **~3,500 lines of untested critical production code** identified through coverage analysis. Focus areas:

### Backend Critical Gaps (0-30% coverage):
- **Security**: auth_security.py (0% but ACTIVELY USED - password hashing)
- **Real-time**: websocket_manager.py (23%)
- **Auth middleware**: auth_dependencies.py (24%)
- **Data access**: repository_dependencies.py (22%)
- **Business logic**: lemma_resolver.py (24%), vocabulary_stats_service.py (26%)

### Frontend Critical Gaps (0-14% coverage):
- **Core hooks**: useApi.ts (0%), useAppStore.ts (0%), useVocabularyStore.ts (0%)
- **Auth flow**: auth-interceptor.ts (14%)
- **Major components**: LandingPage, VocabularyLibrary, ProfileScreen, LearningPlayer (all 0%)

---

## Phase 1: Critical Security & Infrastructure (Week 1-2)

### Priority 1A: Backend Security (CRITICAL)

#### 1. core/auth_security.py (0% → 95% target)
**Status**: Zero coverage but ACTIVELY USED by database.py for admin password hashing
**Risk**: High - password hashing, token generation, security validation

**Test Requirements**:
```python
# tests/unit/core/test_auth_security_comprehensive.py

class TestPasswordHashing:
    """Test password hashing with SecurityConfig"""

    def test_hash_password_creates_valid_bcrypt_hash(self):
        """Verify password hashing produces valid bcrypt format"""
        password = "TestPass123!"
        hashed = SecurityConfig.hash_password(password)

        assert hashed.startswith("$2b$")  # bcrypt identifier
        assert len(hashed) == 60  # bcrypt hash length
        assert hashed != password

    def test_verify_password_accepts_correct_password(self):
        """Verify correct password validation"""
        password = "TestPass123!"
        hashed = SecurityConfig.hash_password(password)

        assert SecurityConfig.verify_password(password, hashed) is True

    def test_verify_password_rejects_incorrect_password(self):
        """Verify incorrect password rejection"""
        password = "TestPass123!"
        wrong_password = "WrongPass123!"
        hashed = SecurityConfig.hash_password(password)

        assert SecurityConfig.verify_password(wrong_password, hashed) is False

    def test_hash_password_same_input_different_hashes(self):
        """Verify salting - same password produces different hashes"""
        password = "TestPass123!"
        hash1 = SecurityConfig.hash_password(password)
        hash2 = SecurityConfig.hash_password(password)

        assert hash1 != hash2
        assert SecurityConfig.verify_password(password, hash1)
        assert SecurityConfig.verify_password(password, hash2)

    def test_hash_password_handles_unicode(self):
        """Verify Unicode password support"""
        password = "Päss123!日本語"
        hashed = SecurityConfig.hash_password(password)

        assert SecurityConfig.verify_password(password, hashed)


class TestTokenGeneration:
    """Test secure token generation"""

    def test_generate_token_creates_unique_tokens(self):
        """Verify token uniqueness"""
        tokens = {SecurityConfig.generate_token() for _ in range(100)}
        assert len(tokens) == 100  # All unique

    def test_generate_token_default_length(self):
        """Verify default token length"""
        token = SecurityConfig.generate_token()
        assert len(token) == 32  # Default length

    def test_generate_token_custom_length(self):
        """Verify custom token lengths"""
        for length in [16, 32, 64]:
            token = SecurityConfig.generate_token(length=length)
            assert len(token) == length

    def test_generate_token_url_safe(self):
        """Verify tokens are URL-safe"""
        import string
        token = SecurityConfig.generate_token()
        allowed_chars = string.ascii_letters + string.digits + "-_"
        assert all(c in allowed_chars for c in token)


class TestSecurityValidation:
    """Test security validation functions"""

    def test_validate_password_strength_minimum_requirements(self):
        """Verify minimum password requirements"""
        valid = "Pass123!"
        assert SecurityConfig.validate_password_strength(valid) is True

    def test_validate_password_strength_rejects_weak_passwords(self):
        """Verify weak password rejection"""
        weak_passwords = [
            "short",           # Too short
            "onlylowercase",   # No uppercase
            "ONLYUPPERCASE",   # No lowercase
            "NoNumbers!",      # No numbers
            "NoSpecial123",    # No special chars
        ]
        for password in weak_passwords:
            assert SecurityConfig.validate_password_strength(password) is False

    def test_validate_email_format(self):
        """Verify email validation"""
        valid = ["user@example.com", "test.user+tag@domain.co.uk"]
        invalid = ["notanemail", "missing@domain", "@nodomain.com"]

        for email in valid:
            assert SecurityConfig.validate_email(email) is True
        for email in invalid:
            assert SecurityConfig.validate_email(email) is False
```

**Coverage Target**: 95%+ (critical security code requires high coverage)

---

#### 2. api/websocket_manager.py (23% → 80% target)
**Status**: Low coverage, handles real-time communication
**Risk**: Medium - broadcast failures affect UX

**Test Requirements**:
```python
# tests/unit/api/test_websocket_manager_comprehensive.py

@pytest.mark.asyncio
class TestWebSocketManager:
    """Test WebSocket manager connection handling"""

    async def test_connect_new_client(self, mock_websocket):
        """Verify new client connection"""
        manager = WebSocketManager()
        await manager.connect(mock_websocket, user_id=1)

        assert 1 in manager.active_connections
        assert mock_websocket in manager.active_connections[1]

    async def test_connect_multiple_clients_same_user(self, mock_websocket, mock_websocket2):
        """Verify multiple connections for same user"""
        manager = WebSocketManager()
        await manager.connect(mock_websocket, user_id=1)
        await manager.connect(mock_websocket2, user_id=1)

        assert len(manager.active_connections[1]) == 2

    async def test_disconnect_removes_client(self, mock_websocket):
        """Verify client disconnection"""
        manager = WebSocketManager()
        await manager.connect(mock_websocket, user_id=1)
        await manager.disconnect(mock_websocket, user_id=1)

        assert 1 not in manager.active_connections

    async def test_broadcast_to_user_sends_message(self, mock_websocket):
        """Verify message broadcast to user"""
        manager = WebSocketManager()
        await manager.connect(mock_websocket, user_id=1)

        await manager.broadcast_to_user(1, {"type": "test", "data": "hello"})

        mock_websocket.send_json.assert_called_once_with(
            {"type": "test", "data": "hello"}
        )

    async def test_broadcast_to_user_handles_disconnect(self, mock_websocket):
        """Verify graceful handling of disconnected clients"""
        mock_websocket.send_json.side_effect = Exception("Disconnected")
        manager = WebSocketManager()
        await manager.connect(mock_websocket, user_id=1)

        # Should not raise, should disconnect client
        await manager.broadcast_to_user(1, {"type": "test"})

        assert 1 not in manager.active_connections

    async def test_broadcast_all_sends_to_all_users(self):
        """Verify broadcast to all connected users"""
        manager = WebSocketManager()
        ws1, ws2, ws3 = Mock(), Mock(), Mock()

        await manager.connect(ws1, user_id=1)
        await manager.connect(ws2, user_id=2)
        await manager.connect(ws3, user_id=3)

        await manager.broadcast_all({"type": "announcement"})

        for ws in [ws1, ws2, ws3]:
            ws.send_json.assert_called_once()
```

**Coverage Target**: 80%+

---

#### 3. core/auth_dependencies.py (24% → 90% target)
**Status**: Low coverage, critical auth middleware
**Risk**: High - authentication bypass vulnerabilities

**Test Requirements**:
```python
# tests/unit/core/test_auth_dependencies_comprehensive.py

@pytest.mark.asyncio
class TestCurrentUser:
    """Test current user dependency"""

    async def test_get_current_user_valid_token(self, mock_token_service):
        """Verify user retrieval with valid token"""
        mock_token_service.decode_token.return_value = {
            "sub": "1",
            "email": "user@example.com"
        }

        user = await get_current_user(token="valid_token", db=mock_db)

        assert user.id == 1
        assert user.email == "user@example.com"

    async def test_get_current_user_invalid_token_raises_401(self):
        """Verify 401 on invalid token"""
        with pytest.raises(HTTPException) as exc:
            await get_current_user(token="invalid", db=mock_db)

        assert exc.value.status_code == 401

    async def test_get_current_user_expired_token_raises_401(self):
        """Verify 401 on expired token"""
        mock_token_service.decode_token.side_effect = TokenExpiredError()

        with pytest.raises(HTTPException) as exc:
            await get_current_user(token="expired", db=mock_db)

        assert exc.value.status_code == 401

    async def test_get_current_user_nonexistent_user_raises_401(self):
        """Verify 401 when user doesn't exist in DB"""
        mock_token_service.decode_token.return_value = {"sub": "999"}
        mock_db.get.return_value = None

        with pytest.raises(HTTPException) as exc:
            await get_current_user(token="valid", db=mock_db)

        assert exc.value.status_code == 401


class TestCurrentActiveUser:
    """Test active user validation"""

    def test_active_user_passes_through(self):
        """Verify active user passes validation"""
        user = Mock(is_active=True)
        result = get_current_active_user(user)
        assert result == user

    def test_inactive_user_raises_400(self):
        """Verify inactive user rejection"""
        user = Mock(is_active=False)

        with pytest.raises(HTTPException) as exc:
            get_current_active_user(user)

        assert exc.value.status_code == 400


class TestOptionalUser:
    """Test optional authentication"""

    async def test_optional_user_with_valid_token(self):
        """Verify user returned with valid token"""
        user = await get_optional_user(token="valid", db=mock_db)
        assert user is not None

    async def test_optional_user_with_no_token_returns_none(self):
        """Verify None returned without token"""
        user = await get_optional_user(token=None, db=mock_db)
        assert user is None

    async def test_optional_user_with_invalid_token_returns_none(self):
        """Verify None returned for invalid token (not exception)"""
        mock_token_service.decode_token.side_effect = JWTError()
        user = await get_optional_user(token="invalid", db=mock_db)
        assert user is None
```

**Coverage Target**: 90%+

---

### Priority 1B: Frontend Core Hooks (CRITICAL)

#### 4. hooks/useApi.ts (0% → 85% target)
**Status**: Zero coverage but ACTIVELY USED throughout app
**Risk**: High - all API communication depends on this

**Test Requirements**:
```typescript
// src/hooks/__tests__/useApi.test.ts

describe('useApi', () => {
  it('should fetch data immediately when immediate=true', async () => {
    const mockApiCall = vi.fn().mockResolvedValue({ data: { id: 1 } })
    const { result } = renderHook(() => useApi(mockApiCall))

    expect(result.current.loading).toBe(true)
    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.data).toEqual({ id: 1 })
    expect(result.current.error).toBeNull()
  })

  it('should not fetch data when immediate=false', () => {
    const mockApiCall = vi.fn()
    const { result } = renderHook(() =>
      useApi(mockApiCall, [], { immediate: false })
    )

    expect(mockApiCall).not.toHaveBeenCalled()
    expect(result.current.data).toBeNull()
  })

  it('should handle API errors gracefully', async () => {
    const mockApiCall = vi.fn().mockRejectedValue({
      message: 'Network error',
      status: 500
    })
    const { result } = renderHook(() => useApi(mockApiCall))

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.error).toBe('Network error')
    expect(result.current.data).toBeNull()
  })

  it('should retry failed requests up to retries limit', async () => {
    const mockApiCall = vi.fn()
      .mockRejectedValueOnce({ status: 500 })
      .mockRejectedValueOnce({ status: 500 })
      .mockResolvedValue({ data: { id: 1 } })

    const { result } = renderHook(() =>
      useApi(mockApiCall, [], { retries: 3, retryDelay: 10 })
    )

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(mockApiCall).toHaveBeenCalledTimes(3)
    expect(result.current.data).toEqual({ id: 1 })
  })

  it('should not retry on 401/403 errors', async () => {
    const mockApiCall = vi.fn().mockRejectedValue({
      status: 401,
      message: 'Unauthorized'
    })
    const { result } = renderHook(() =>
      useApi(mockApiCall, [], { retries: 3 })
    )

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(mockApiCall).toHaveBeenCalledTimes(1) // No retries
  })

  it('should use cached data within TTL', async () => {
    const mockApiCall = vi.fn().mockResolvedValue({ data: { id: 1 } })
    const { result, rerender } = renderHook(() =>
      useApi(mockApiCall, [], { cache: true, cacheTtl: 5000 })
    )

    await waitFor(() => expect(result.current.loading).toBe(false))

    rerender()

    expect(mockApiCall).toHaveBeenCalledTimes(1) // Used cache
    expect(result.current.data).toEqual({ id: 1 })
  })

  it('should refetch data manually', async () => {
    const mockApiCall = vi.fn()
      .mockResolvedValueOnce({ data: { count: 1 } })
      .mockResolvedValueOnce({ data: { count: 2 } })

    const { result } = renderHook(() => useApi(mockApiCall))

    await waitFor(() => expect(result.current.data).toEqual({ count: 1 }))

    await act(async () => {
      await result.current.refetch()
    })

    expect(result.current.data).toEqual({ count: 2 })
  })

  it('should reset state', async () => {
    const mockApiCall = vi.fn().mockResolvedValue({ data: { id: 1 } })
    const { result } = renderHook(() => useApi(mockApiCall))

    await waitFor(() => expect(result.current.data).toEqual({ id: 1 }))

    act(() => {
      result.current.reset()
    })

    expect(result.current.data).toBeNull()
    expect(result.current.error).toBeNull()
    expect(result.current.loading).toBe(false)
  })
})
```

**Coverage Target**: 85%+

---

#### 5. store/useAppStore.ts (0% → 85% target)
**Status**: Zero coverage but ACTIVELY USED for global state
**Risk**: Medium - affects error handling, notifications, config

**Test Requirements**:
```typescript
// src/store/__tests__/useAppStore.test.ts

describe('useAppStore', () => {
  beforeEach(() => {
    useAppStore.getState().reset()
  })

  describe('Configuration', () => {
    it('should update config partially', () => {
      act(() => {
        useAppStore.getState().setConfig({ theme: 'dark' })
      })

      expect(useAppStore.getState().config.theme).toBe('dark')
      expect(useAppStore.getState().config.language).toBe('de') // Unchanged
    })

    it('should persist config to localStorage', () => {
      const setItemSpy = vi.spyOn(Storage.prototype, 'setItem')

      act(() => {
        useAppStore.getState().setConfig({ showAdvancedFeatures: true })
      })

      expect(setItemSpy).toHaveBeenCalledWith(
        'langplug-config',
        expect.stringContaining('showAdvancedFeatures')
      )
    })
  })

  describe('Error Handling', () => {
    it('should track last error', () => {
      act(() => {
        useAppStore.getState().setError('Test error')
      })

      expect(useAppStore.getState().lastError).toBe('Test error')
    })

    it('should maintain error history (max 10)', () => {
      act(() => {
        for (let i = 0; i < 15; i++) {
          useAppStore.getState().setError(`Error ${i}`)
        }
      })

      expect(useAppStore.getState().errorHistory.length).toBe(10)
      expect(useAppStore.getState().errorHistory[9].error).toBe('Error 14')
    })

    it('should clear error history', () => {
      act(() => {
        useAppStore.getState().setError('Error 1')
        useAppStore.getState().clearErrorHistory()
      })

      expect(useAppStore.getState().errorHistory).toEqual([])
      expect(useAppStore.getState().lastError).toBeNull()
    })
  })

  describe('Notifications', () => {
    it('should add notification with auto-remove', async () => {
      vi.useFakeTimers()

      act(() => {
        useAppStore.getState().addNotification({
          type: 'success',
          title: 'Test',
          message: 'Test message',
          duration: 1000
        })
      })

      expect(useAppStore.getState().notifications).toHaveLength(1)

      vi.advanceTimersByTime(1000)
      await waitFor(() => {
        expect(useAppStore.getState().notifications).toHaveLength(0)
      })

      vi.useRealTimers()
    })

    it('should remove notification by id', () => {
      act(() => {
        useAppStore.getState().addNotification({
          type: 'info',
          title: 'Test',
          message: 'Test'
        })
      })

      const id = useAppStore.getState().notifications[0].id

      act(() => {
        useAppStore.getState().removeNotification(id)
      })

      expect(useAppStore.getState().notifications).toHaveLength(0)
    })
  })

  describe('Performance Tracking', () => {
    it('should record load times', () => {
      act(() => {
        useAppStore.getState().recordLoadTime('videos', 1234)
      })

      expect(useAppStore.getState().performanceMetrics.loadTimes.videos).toBe(1234)
    })

    it('should record API response times', () => {
      act(() => {
        useAppStore.getState().recordApiResponseTime('/api/videos', 567)
      })

      expect(
        useAppStore.getState().performanceMetrics.apiResponseTimes['/api/videos']
      ).toBe(567)
    })
  })
})
```

**Coverage Target**: 85%+

---

#### 6. store/useVocabularyStore.ts (0% → 85% target)
**Status**: Zero coverage but ACTIVELY USED for vocabulary state
**Risk**: High - critical business logic

**Test Requirements**:
```typescript
// src/store/__tests__/useVocabularyStore.test.ts

describe('useVocabularyStore', () => {
  beforeEach(() => {
    useVocabularyStore.getState().reset()
    vi.clearAllMocks()
  })

  describe('Word Management', () => {
    it('should set words', () => {
      const words = [
        { id: 1, word: 'Haus', lemma: 'Haus', language: 'de', difficulty_level: 'A1' }
      ]

      act(() => {
        useVocabularyStore.getState().setWords(words)
      })

      expect(useVocabularyStore.getState().words[1]).toEqual(words[0])
    })

    it('should update existing words', () => {
      const word1 = { id: 1, word: 'Haus', frequency_rank: 100 }
      const word2 = { id: 1, word: 'Haus', frequency_rank: 50 }

      act(() => {
        useVocabularyStore.getState().setWords([word1])
        useVocabularyStore.getState().setWords([word2])
      })

      expect(useVocabularyStore.getState().words[1].frequency_rank).toBe(50)
    })
  })

  describe('Search', () => {
    it('should search words and update state', async () => {
      const mockWords = [
        { id: 1, word: 'Haus', lemma: 'Haus' },
        { id: 2, word: 'Häuser', lemma: 'Haus' }
      ]

      vi.mocked(api.vocabulary.search).mockResolvedValue({
        data: mockWords
      })

      await act(async () => {
        await useVocabularyStore.getState().searchWords('Haus', 'de', 20)
      })

      expect(useVocabularyStore.getState().searchResults).toEqual(mockWords)
      expect(useVocabularyStore.getState().searchQuery).toBe('Haus')
      expect(useVocabularyStore.getState().isSearching).toBe(false)
    })

    it('should handle search errors', async () => {
      vi.mocked(api.vocabulary.search).mockRejectedValue(
        new Error('Network error')
      )

      await act(async () => {
        await useVocabularyStore.getState().searchWords('test')
      })

      expect(useVocabularyStore.getState().searchResults).toEqual([])
      expect(useVocabularyStore.getState().isSearching).toBe(false)
    })
  })

  describe('Caching', () => {
    it('should use cache within TTL', async () => {
      vi.mocked(api.vocabulary.getByLevel).mockResolvedValue({
        data: [{ id: 1, word: 'Haus' }]
      })

      await act(async () => {
        await useVocabularyStore.getState().fetchWordsByLevel('A1', 'de')
      })

      vi.mocked(api.vocabulary.getByLevel).mockClear()

      await act(async () => {
        await useVocabularyStore.getState().fetchWordsByLevel('A1', 'de')
      })

      expect(api.vocabulary.getByLevel).not.toHaveBeenCalled() // Used cache
    })
  })

  describe('Mark Words', () => {
    it('should mark word as known', async () => {
      const progress = { vocabulary_id: 1, is_known: true }
      vi.mocked(api.vocabulary.markWord).mockResolvedValue({ data: progress })
      vi.mocked(api.vocabulary.getStats).mockResolvedValue({
        data: { known_words: 1 }
      })

      await act(async () => {
        await useVocabularyStore.getState().markWord(1, true)
      })

      expect(useVocabularyStore.getState().userProgress[1]).toEqual(progress)
      expect(api.vocabulary.getStats).toHaveBeenCalled() // Refreshes stats
    })

    it('should bulk mark words', async () => {
      const progressList = [
        { vocabulary_id: 1, is_known: true },
        { vocabulary_id: 2, is_known: true }
      ]
      vi.mocked(api.vocabulary.bulkMarkWords).mockResolvedValue({
        data: progressList
      })

      await act(async () => {
        await useVocabularyStore.getState().bulkMarkWords([1, 2], true)
      })

      expect(useVocabularyStore.getState().userProgress[1]).toEqual(progressList[0])
      expect(useVocabularyStore.getState().userProgress[2]).toEqual(progressList[1])
    })
  })
})
```

**Coverage Target**: 85%+

---

## Phase 2: Business Logic & Components (Week 3-4)

### Priority 2A: Backend Business Logic

#### 7. services/lemma_resolver.py (24% → 75% target)
**Test Focus**: Lemmatization accuracy, language support, edge cases

#### 8. services/vocabulary/vocabulary_stats_service.py (26% → 75% target)
**Test Focus**: Statistics calculation, level breakdowns, performance

#### 9. core/repository_dependencies.py (22% → 80% target)
**Test Focus**: Repository injection, transaction management, error handling

---

### Priority 2B: Frontend Major Components

#### 10. components/LandingPage.tsx (0% → 70% target)
**Test Focus**: Navigation, authentication redirects, UI interactions

#### 11. components/VocabularyLibrary.tsx (0% → 70% target)
**Test Focus**: Word list rendering, filtering, pagination, marking words

#### 12. components/ProfileScreen.tsx (0% → 70% target)
**Test Focus**: User data display, settings updates, error handling

#### 13. components/LearningPlayer.tsx (0% → 70% target)
**Test Focus**: Video playback, subtitle sync, interaction states

#### 14. services/auth-interceptor.ts (14% → 85% target)
**Test Focus**: Token refresh, request interception, error handling

---

## Implementation Guidelines

### Backend Testing Standards

```python
# Test Structure Pattern
class TestFeatureName:
    """Test feature with clear scenarios"""

    def test_happy_path(self):
        """Test successful operation"""
        pass

    def test_error_handling(self):
        """Test error scenarios"""
        pass

    def test_edge_cases(self):
        """Test boundary conditions"""
        pass

    def test_validation(self):
        """Test input validation"""
        pass
```

**Requirements**:
- ✅ No mock call counting (test behavior, not implementation)
- ✅ Test observable behavior and return values
- ✅ Use descriptive test names
- ✅ Arrange-Act-Assert pattern
- ✅ Use fixtures for common setup
- ✅ No hard-coded paths or credentials
- ✅ Tests must pass with `--random-order`

---

### Frontend Testing Standards

```typescript
// Test Structure Pattern
describe('ComponentName', () => {
  it('should render with default props', () => {
    // Test initial state
  })

  it('should handle user interaction', async () => {
    // Test user actions
  })

  it('should display error states', () => {
    // Test error handling
  })

  it('should update based on props changes', () => {
    // Test reactivity
  })
})
```

**Requirements**:
- ✅ Test user-visible behavior
- ✅ Use semantic queries (getByRole, getByLabelText)
- ✅ Mock API calls, not React internals
- ✅ Test accessibility
- ✅ Test loading states
- ✅ Test error boundaries

---

## Success Metrics

### Coverage Targets by Phase

**Phase 1 (Weeks 1-2)**:
- Backend: 50.54% → 65%
- Frontend: 58.63% → 70%

**Phase 2 (Weeks 3-4)**:
- Backend: 65% → 80%
- Frontend: 70% → 80%

**Goal State**:
- Backend: 80%+ (Critical modules 90%+)
- Frontend: 80%+ (Core hooks 85%+)

---

## Priority Order Summary

1. **Week 1**: auth_security.py, useApi.ts, useAppStore.ts
2. **Week 2**: websocket_manager.py, auth_dependencies.py, useVocabularyStore.ts
3. **Week 3**: auth-interceptor.ts, LandingPage, VocabularyLibrary
4. **Week 4**: LearningPlayer, ProfileScreen, business logic services

---

## Maintenance & CI Integration

### Pre-Commit Requirements
- All new code must have accompanying tests
- Coverage must not decrease below current baseline
- Tests must pass with `--random-order`

### CI Checks
```yaml
# .github/workflows/coverage-gate.yml
- name: Check Coverage
  run: |
    pytest --cov --cov-fail-under=60

- name: Check Coverage Trend
  run: |
    # Fail if coverage decreased by >2%
    python scripts/check_coverage_trend.py
```

---

## Next Steps

1. **Review & Prioritize**: Team reviews priority order
2. **Allocate Resources**: Assign test writing to developers
3. **Set Up Tracking**: Create GitHub issues for each component
4. **Start Phase 1**: Begin with auth_security.py tests
5. **Weekly Reviews**: Track progress, adjust priorities

---

**Questions or concerns?** Contact the testing team or refer to:
- `tests/TESTING_BEST_PRACTICES.md`
- `CLAUDE.md` - Testing standards section
- `tests/monitoring/coverage_monitor.py` - Coverage tracking tool
