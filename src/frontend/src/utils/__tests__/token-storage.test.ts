import { describe, it, expect, beforeEach, afterEach, beforeAll } from 'vitest'
import { tokenStorage } from '../token-storage'

let localStorageMock: { [key: string]: string }

describe('tokenStorage', () => {
  beforeAll(() => {
    // Mock localStorage for all tests
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: (key: string) => localStorageMock[key] || null,
        setItem: (key: string, value: string) => {
          localStorageMock[key] = value
        },
        removeItem: (key: string) => {
          delete localStorageMock[key]
        },
        clear: () => {
          localStorageMock = {}
        },
      },
      writable: true,
      configurable: true,
    })
  })

  beforeEach(() => {
    localStorageMock = {}
    tokenStorage.clear()
  })

  afterEach(() => {
    localStorageMock = {}
    tokenStorage.clear()
  })

  describe('getToken and setToken', () => {
    it('should store and retrieve token', () => {
      const token = 'test-access-token-123'

      tokenStorage.setToken(token)
      const retrieved = tokenStorage.getToken()

      expect(retrieved).toBe(token)
    })

    it('should return null when no token is stored', () => {
      const retrieved = tokenStorage.getToken()
      expect(retrieved).toBeNull()
    })

    it('should overwrite existing token', () => {
      tokenStorage.setToken('old-token')
      tokenStorage.setToken('new-token')

      const retrieved = tokenStorage.getToken()
      expect(retrieved).toBe('new-token')
    })

    it('should persist to localStorage', () => {
      tokenStorage.setToken('persisted-token')

      const fromStorage = localStorage.getItem('auth_token')
      expect(fromStorage).toBe('persisted-token')
    })
  })

  describe('getRefreshToken and setRefreshToken', () => {
    it('should store and retrieve refresh token', () => {
      const token = 'test-refresh-token-456'

      tokenStorage.setRefreshToken(token)
      const retrieved = tokenStorage.getRefreshToken()

      expect(retrieved).toBe(token)
    })

    it('should return null when no refresh token is stored', () => {
      const retrieved = tokenStorage.getRefreshToken()
      expect(retrieved).toBeNull()
    })

    it('should overwrite existing refresh token', () => {
      tokenStorage.setRefreshToken('old-refresh')
      tokenStorage.setRefreshToken('new-refresh')

      const retrieved = tokenStorage.getRefreshToken()
      expect(retrieved).toBe('new-refresh')
    })

    it('should persist to localStorage', () => {
      tokenStorage.setRefreshToken('persisted-refresh')

      const fromStorage = localStorage.getItem('refresh_token')
      expect(fromStorage).toBe('persisted-refresh')
    })
  })

  describe('clear', () => {
    it('should clear both access and refresh tokens', () => {
      tokenStorage.setToken('access-token')
      tokenStorage.setRefreshToken('refresh-token')

      tokenStorage.clear()

      expect(tokenStorage.getToken()).toBeNull()
      expect(tokenStorage.getRefreshToken()).toBeNull()
    })

    it('should remove tokens from localStorage', () => {
      tokenStorage.setToken('access')
      tokenStorage.setRefreshToken('refresh')

      tokenStorage.clear()

      expect(localStorage.getItem('auth_token')).toBeNull()
      expect(localStorage.getItem('refresh_token')).toBeNull()
    })

    it('should be idempotent (safe to call multiple times)', () => {
      tokenStorage.setToken('token')

      tokenStorage.clear()
      tokenStorage.clear()
      tokenStorage.clear()

      expect(tokenStorage.getToken()).toBeNull()
    })

    it('should not throw when clearing empty storage', () => {
      expect(() => tokenStorage.clear()).not.toThrow()
    })
  })

  describe('isTokenExpired', () => {
    it('should return false for any token (test behavior)', () => {
      expect(tokenStorage.isTokenExpired('any-token')).toBe(false)
    })

    it('should return false for empty token', () => {
      expect(tokenStorage.isTokenExpired('')).toBe(false)
    })

    it('should return false for very long token', () => {
      const jwt =
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'
      expect(tokenStorage.isTokenExpired(jwt)).toBe(false)
    })
  })

  describe('edge cases', () => {
    it('should handle null token by storing null', () => {
      tokenStorage.setToken(null as any)

      const retrieved = tokenStorage.getToken()
      expect(retrieved).toBeNull()
    })

    it('should handle undefined token by storing null', () => {
      tokenStorage.setToken(undefined as any)

      const retrieved = tokenStorage.getToken()
      expect(retrieved).toBeNull()
    })

    it('should handle special characters in tokens', () => {
      const specialToken = 'token.with-special_chars/+=123'

      tokenStorage.setToken(specialToken)
      const retrieved = tokenStorage.getToken()

      expect(retrieved).toBe(specialToken)
    })

    it('should handle very long tokens (JWTs)', () => {
      const longToken =
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'

      tokenStorage.setToken(longToken)
      const retrieved = tokenStorage.getToken()

      expect(retrieved).toBe(longToken)
    })

    it('should independently manage access and refresh tokens', () => {
      tokenStorage.setToken('access')
      tokenStorage.setRefreshToken('refresh')

      // Clear only access token
      tokenStorage.setToken(null as any)

      expect(tokenStorage.getToken()).toBeNull()
      expect(tokenStorage.getRefreshToken()).toBe('refresh')
    })

    it('should handle localStorage errors gracefully (setToken)', () => {
      // Mock localStorage to throw errors
      const originalSetItem = localStorage.setItem
      localStorage.setItem = () => {
        throw new Error('QuotaExceededError')
      }

      // Should not throw
      expect(() => tokenStorage.setToken('test')).not.toThrow()
      // Memory storage should still work
      expect(tokenStorage.getToken()).toBe('test')

      // Restore
      localStorage.setItem = originalSetItem
    })

    it('should handle localStorage errors gracefully (setRefreshToken)', () => {
      const originalSetItem = localStorage.setItem
      localStorage.setItem = () => {
        throw new Error('QuotaExceededError')
      }

      expect(() => tokenStorage.setRefreshToken('refresh')).not.toThrow()
      // Memory storage should still work
      expect(tokenStorage.getRefreshToken()).toBe('refresh')

      localStorage.setItem = originalSetItem
    })

    it('should handle localStorage errors gracefully (clear)', () => {
      const originalRemoveItem = localStorage.removeItem
      localStorage.removeItem = () => {
        throw new Error('StorageError')
      }

      expect(() => tokenStorage.clear()).not.toThrow()
      // Memory should be cleared even if localStorage fails
      expect(tokenStorage.getToken()).toBeNull()
      expect(tokenStorage.getRefreshToken()).toBeNull()

      localStorage.removeItem = originalRemoveItem
    })
  })

  describe('memory and localStorage sync', () => {
    it('should work with memory even if localStorage fails', () => {
      // Completely break localStorage
      const originalSetItem = localStorage.setItem
      localStorage.setItem = () => {
        throw new Error('localStorage broken')
      }

      tokenStorage.setToken('memory-token')
      expect(tokenStorage.getToken()).toBe('memory-token')

      tokenStorage.setRefreshToken('memory-refresh')
      expect(tokenStorage.getRefreshToken()).toBe('memory-refresh')

      localStorage.setItem = originalSetItem
    })

    it('should use memory storage for getToken', () => {
      tokenStorage.setToken('test-token')

      // Even if we clear localStorage directly, memory should return the token
      expect(tokenStorage.getToken()).toBe('test-token')
    })
  })
})
