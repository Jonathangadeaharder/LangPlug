import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import {
  authRequestInterceptor,
  authResponseInterceptor,
  setupAuthInterceptors,
} from '../auth-interceptor'
import { AxiosRequestConfig, AxiosResponse } from 'axios'
import * as authStore from '@/store/useAuthStore'
import { OpenAPI } from '@/client/core/OpenAPI'

// Mock dependencies
let mockTOKEN: (() => Promise<string>) | null = null

vi.mock('@/client/core/OpenAPI', () => {
  const mockOpenAPI = {
    BASE: 'http://localhost:8000',
    get TOKEN() {
      return mockTOKEN
    },
    set TOKEN(value) {
      mockTOKEN = value
    },
    interceptors: {
      request: {
        use: vi.fn(),
      },
      response: {
        use: vi.fn(),
      },
    },
  }
  return { OpenAPI: mockOpenAPI }
})

vi.mock('@/services/logger', () => ({
  logger: {
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
}))

vi.mock('@/store/useAuthStore', () => ({
  clearAuthState: vi.fn(),
}))

describe('auth-interceptor', () => {
  const originalFetch = global.fetch
  const originalLocation = window.location
  let localStorageMock: { [key: string]: string }

  beforeEach(() => {
    // Reset all mocks
    vi.clearAllMocks()

    // Reset TOKEN
    mockTOKEN = null

    // Create a fresh localStorage mock for each test
    localStorageMock = {}

    // Mock localStorage methods
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

    // Mock fetch
    global.fetch = vi.fn()

    // Mock window.location
    delete (window as any).location
    window.location = {
      ...originalLocation,
      href: '',
      pathname: '/dashboard',
    }
  })

  afterEach(() => {
    global.fetch = originalFetch
    window.location = originalLocation
    localStorageMock = {}
  })

  describe('authRequestInterceptor', () => {
    it('should add Authorization header when access_token exists', async () => {
      localStorage.setItem('access_token', 'test-access-token')

      const config: AxiosRequestConfig = {
        url: '/api/test',
        method: 'GET',
      }

      const result = await authRequestInterceptor(config)

      expect(result.headers).toBeDefined()
      expect(result.headers!['Authorization']).toBe('Bearer test-access-token')
    })

    it('should use authToken as fallback when access_token not present', async () => {
      localStorage.setItem('authToken', 'legacy-token')

      const config: AxiosRequestConfig = {
        url: '/api/test',
        method: 'GET',
      }

      const result = await authRequestInterceptor(config)

      expect(result.headers!['Authorization']).toBe('Bearer legacy-token')
    })

    it('should prefer access_token over authToken', async () => {
      localStorage.setItem('access_token', 'new-token')
      localStorage.setItem('authToken', 'legacy-token')

      const config: AxiosRequestConfig = {
        url: '/api/test',
        method: 'GET',
      }

      const result = await authRequestInterceptor(config)

      expect(result.headers!['Authorization']).toBe('Bearer new-token')
    })

    it('should not add Authorization header when no token exists', async () => {
      const config: AxiosRequestConfig = {
        url: '/api/test',
        method: 'GET',
      }

      const result = await authRequestInterceptor(config)

      expect(result.headers?.['Authorization']).toBeUndefined()
    })

    it('should preserve existing headers', async () => {
      localStorage.setItem('access_token', 'test-token')

      const config: AxiosRequestConfig = {
        url: '/api/test',
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Custom-Header': 'custom-value',
        },
      }

      const result = await authRequestInterceptor(config)

      expect(result.headers!['Content-Type']).toBe('application/json')
      expect(result.headers!['X-Custom-Header']).toBe('custom-value')
      expect(result.headers!['Authorization']).toBe('Bearer test-token')
    })

    it('should initialize headers if not present', async () => {
      localStorage.setItem('access_token', 'test-token')

      const config: AxiosRequestConfig = {
        url: '/api/test',
        method: 'GET',
      }

      const result = await authRequestInterceptor(config)

      expect(result.headers).toBeDefined()
      expect(result.headers!['Authorization']).toBe('Bearer test-token')
    })
  })

  describe('authResponseInterceptor', () => {
    it('should return response immediately if status is not 401', async () => {
      const response: AxiosResponse = {
        status: 200,
        statusText: 'OK',
        data: { message: 'success' },
        headers: {},
        config: {},
      } as AxiosResponse

      const result = await authResponseInterceptor(response)

      expect(result).toBe(response)
      expect(global.fetch).not.toHaveBeenCalled()
    })

    it('should return non-401 errors without intervention', async () => {
      const response: AxiosResponse = {
        status: 500,
        statusText: 'Internal Server Error',
        data: { error: 'server error' },
        headers: {},
        config: {},
      } as AxiosResponse

      const result = await authResponseInterceptor(response)

      expect(result).toBe(response)
      expect(global.fetch).not.toHaveBeenCalled()
    })

    it('should attempt token refresh on 401 error', async () => {
      localStorage.setItem('refresh_token', 'test-refresh-token')

      const mockRefreshResponse = {
        ok: true,
        json: async () => ({ access_token: 'new-access-token' }),
      }
      ;(global.fetch as any).mockResolvedValueOnce(mockRefreshResponse)

      const response: AxiosResponse = {
        status: 401,
        statusText: 'Unauthorized',
        data: {},
        headers: {},
        config: {
          url: 'http://localhost:8000/api/protected',
          method: 'GET',
          headers: {},
        },
      } as AxiosResponse

      const mockRetryResponse = {
        status: 200,
        statusText: 'OK',
        json: async () => ({ data: 'protected data' }),
      }
      ;(global.fetch as any).mockResolvedValueOnce(mockRetryResponse)

      const result = await authResponseInterceptor(response)

      // Verify refresh was called
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/auth/refresh',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: 'test-refresh-token' }),
        })
      )

      // Verify new token was stored
      expect(localStorage.getItem('access_token')).toBe('new-access-token')
      expect(localStorage.getItem('authToken')).toBe('new-access-token')

      // Verify retry was successful
      expect(result.status).toBe(200)
      expect(result.data).toEqual({ data: 'protected data' })
    })

    it('should clear auth and redirect to login when refresh token is missing', async () => {
      const response: AxiosResponse = {
        status: 401,
        statusText: 'Unauthorized',
        data: {},
        headers: {},
        config: {},
      } as AxiosResponse

      const result = await authResponseInterceptor(response)

      expect(authStore.clearAuthState).toHaveBeenCalled()
      expect(window.location.href).toBe('/login')
      expect(result.status).toBe(401)
    })

    it('should clear auth and redirect when token refresh fails', async () => {
      localStorage.setItem('refresh_token', 'invalid-refresh-token')

      const mockRefreshResponse = {
        ok: false,
        status: 401,
      }
      ;(global.fetch as any).mockResolvedValueOnce(mockRefreshResponse)

      const response: AxiosResponse = {
        status: 401,
        statusText: 'Unauthorized',
        data: {},
        headers: {},
        config: {},
      } as AxiosResponse

      const result = await authResponseInterceptor(response)

      expect(authStore.clearAuthState).toHaveBeenCalled()
      expect(window.location.href).toBe('/login')
      expect(result.status).toBe(401)
    })

    it('should not redirect if already on login page', async () => {
      window.location.pathname = '/login'
      localStorage.setItem('refresh_token', 'test-token')

      const mockRefreshResponse = {
        ok: false,
        status: 401,
      }
      ;(global.fetch as any).mockResolvedValueOnce(mockRefreshResponse)

      const response: AxiosResponse = {
        status: 401,
        statusText: 'Unauthorized',
        data: {},
        headers: {},
        config: {},
      } as AxiosResponse

      await authResponseInterceptor(response)

      expect(window.location.href).toBe('')
    })

    it('should handle network errors during token refresh', async () => {
      localStorage.setItem('refresh_token', 'test-refresh-token')

      ;(global.fetch as any).mockRejectedValueOnce(new Error('Network error'))

      const response: AxiosResponse = {
        status: 401,
        statusText: 'Unauthorized',
        data: {},
        headers: {},
        config: {},
      } as AxiosResponse

      const result = await authResponseInterceptor(response)

      expect(authStore.clearAuthState).toHaveBeenCalled()
      expect(window.location.href).toBe('/login')
      expect(result.status).toBe(401)
    })

    it('should return original response if retry request fails', async () => {
      localStorage.setItem('refresh_token', 'test-refresh-token')

      const mockRefreshResponse = {
        ok: true,
        json: async () => ({ access_token: 'new-token' }),
      }
      ;(global.fetch as any).mockResolvedValueOnce(mockRefreshResponse)

      const response: AxiosResponse = {
        status: 401,
        statusText: 'Unauthorized',
        data: {},
        headers: {},
        config: {
          url: 'http://localhost:8000/api/protected',
          method: 'GET',
          headers: {},
        },
      } as AxiosResponse

      // Mock retry to fail
      ;(global.fetch as any).mockRejectedValueOnce(new Error('Retry failed'))

      const result = await authResponseInterceptor(response)

      // Should still return the response (error is logged but not thrown)
      expect(result.status).toBe(401)
    })

    it('should return original response if config has no url', async () => {
      localStorage.setItem('refresh_token', 'test-refresh-token')

      const mockRefreshResponse = {
        ok: true,
        json: async () => ({ access_token: 'new-token' }),
      }
      ;(global.fetch as any).mockResolvedValueOnce(mockRefreshResponse)

      const response: AxiosResponse = {
        status: 401,
        statusText: 'Unauthorized',
        data: {},
        headers: {},
        config: {
          // No URL
          method: 'GET',
          headers: {},
        },
      } as AxiosResponse

      const result = await authResponseInterceptor(response)

      expect(result.status).toBe(401)
      expect(global.fetch).toHaveBeenCalledTimes(1) // Only refresh call
    })
  })

  describe('setupAuthInterceptors', () => {
    it('should register request and response interceptors', () => {
      setupAuthInterceptors()

      expect(OpenAPI.interceptors.request.use).toHaveBeenCalledWith(authRequestInterceptor)
      expect(OpenAPI.interceptors.response.use).toHaveBeenCalledWith(authResponseInterceptor)
    })

    it('should set up TOKEN function to retrieve from localStorage', async () => {
      localStorage.setItem('access_token', 'stored-token')

      setupAuthInterceptors()

      const token = await OpenAPI.TOKEN()

      expect(token).toBe('stored-token')
    })

    it('should return empty string when no token exists', async () => {
      setupAuthInterceptors()

      const token = await OpenAPI.TOKEN()

      expect(token).toBe('')
    })

    it('should prefer access_token in TOKEN function', async () => {
      localStorage.setItem('access_token', 'new-token')
      localStorage.setItem('authToken', 'legacy-token')

      setupAuthInterceptors()

      const token = await OpenAPI.TOKEN()

      expect(token).toBe('new-token')
    })

    it('should fallback to authToken in TOKEN function', async () => {
      localStorage.setItem('authToken', 'legacy-token')

      setupAuthInterceptors()

      const token = await OpenAPI.TOKEN()

      expect(token).toBe('legacy-token')
    })
  })

  describe('edge cases', () => {
    it('should handle empty token values gracefully', async () => {
      localStorage.setItem('access_token', '')

      const config: AxiosRequestConfig = {
        url: '/api/test',
        method: 'GET',
      }

      const result = await authRequestInterceptor(config)

      // Empty string is treated as falsy, no header should be added
      expect(result.headers).toBeUndefined()
    })

    it('should handle special characters in tokens', async () => {
      const specialToken = 'token.with-special_chars/+=123'
      localStorage.setItem('access_token', specialToken)

      const config: AxiosRequestConfig = {
        url: '/api/test',
        method: 'GET',
      }

      const result = await authRequestInterceptor(config)

      expect(result.headers!['Authorization']).toBe(`Bearer ${specialToken}`)
    })

    it('should handle very long JWT tokens', async () => {
      const longJwt =
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'
      localStorage.setItem('access_token', longJwt)

      const config: AxiosRequestConfig = {
        url: '/api/test',
        method: 'GET',
      }

      const result = await authRequestInterceptor(config)

      expect(result.headers!['Authorization']).toBe(`Bearer ${longJwt}`)
    })

    it('should handle POST requests with data during retry', async () => {
      localStorage.setItem('refresh_token', 'test-refresh-token')

      const mockRefreshResponse = {
        ok: true,
        json: async () => ({ access_token: 'new-token' }),
      }
      ;(global.fetch as any).mockResolvedValueOnce(mockRefreshResponse)

      const postData = { key: 'value', nested: { data: 123 } }

      const response: AxiosResponse = {
        status: 401,
        statusText: 'Unauthorized',
        data: {},
        headers: {},
        config: {
          url: 'http://localhost:8000/api/submit',
          method: 'POST',
          headers: {},
          data: postData,
        },
      } as AxiosResponse

      const mockRetryResponse = {
        status: 200,
        statusText: 'OK',
        json: async () => ({ success: true }),
      }
      ;(global.fetch as any).mockResolvedValueOnce(mockRetryResponse)

      await authResponseInterceptor(response)

      // Verify retry included POST data
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/submit',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(postData),
        })
      )
    })

    it('should handle undefined config during 401 response', async () => {
      localStorage.setItem('refresh_token', 'test-refresh-token')

      const mockRefreshResponse = {
        ok: true,
        json: async () => ({ access_token: 'new-token' }),
      }
      ;(global.fetch as any).mockResolvedValueOnce(mockRefreshResponse)

      const response: AxiosResponse = {
        status: 401,
        statusText: 'Unauthorized',
        data: {},
        headers: {},
        config: undefined as any,
      } as AxiosResponse

      const result = await authResponseInterceptor(response)

      // Should complete without crashing
      expect(result.status).toBe(401)
    })
  })

  describe('integration scenarios', () => {
    it('should complete full auth flow: 401 → refresh → retry → success', async () => {
      localStorage.setItem('refresh_token', 'valid-refresh')

      // Step 1: Original request gets 401
      const response: AxiosResponse = {
        status: 401,
        statusText: 'Unauthorized',
        data: { error: 'Token expired' },
        headers: {},
        config: {
          url: 'http://localhost:8000/api/user/profile',
          method: 'GET',
          headers: {},
        },
      } as AxiosResponse

      // Step 2: Mock successful token refresh
      const mockRefreshResponse = {
        ok: true,
        json: async () => ({ access_token: 'fresh-new-token' }),
      }
      ;(global.fetch as any).mockResolvedValueOnce(mockRefreshResponse)

      // Step 3: Mock successful retry
      const mockRetryResponse = {
        status: 200,
        statusText: 'OK',
        json: async () => ({ username: 'testuser', email: 'test@example.com' }),
      }
      ;(global.fetch as any).mockResolvedValueOnce(mockRetryResponse)

      const result = await authResponseInterceptor(response)

      expect(result.status).toBe(200)
      expect(result.data).toEqual({ username: 'testuser', email: 'test@example.com' })
      expect(localStorage.getItem('access_token')).toBe('fresh-new-token')
    })

    it('should complete full failure flow: 401 → refresh fail → clear → redirect', async () => {
      localStorage.setItem('refresh_token', 'invalid-refresh')
      localStorage.setItem('access_token', 'old-token')

      const response: AxiosResponse = {
        status: 401,
        statusText: 'Unauthorized',
        data: {},
        headers: {},
        config: {},
      } as AxiosResponse

      const mockRefreshResponse = {
        ok: false,
        status: 401,
      }
      ;(global.fetch as any).mockResolvedValueOnce(mockRefreshResponse)

      await authResponseInterceptor(response)

      expect(authStore.clearAuthState).toHaveBeenCalled()
      expect(window.location.href).toBe('/login')
    })
  })
})
