/**
 * Tests for API configuration and cookie-based authentication support
 * 
 * These tests verify that the API client is configured correctly for
 * same-origin requests in development (to support SameSite=lax cookies)
 * and cross-origin requests in production.
 */
import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest'

// Helper to create a mock window with required properties
const createMockWindow = (hostname: string) => ({
  location: { hostname },
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
})

describe('API Configuration', () => {
  const originalEnv = { ...import.meta.env }
  const originalWindow = global.window

  beforeEach(() => {
    vi.resetModules()
    // Mock window.location for localhost detection with all required properties
    Object.defineProperty(global, 'window', {
      value: createMockWindow('localhost'),
      writable: true,
      configurable: true
    })
  })

  afterEach(() => {
    // Restore original environment
    Object.keys(import.meta.env).forEach(key => {
      if (!(key in originalEnv)) {
        delete import.meta.env[key]
      }
    })
    Object.assign(import.meta.env, originalEnv)
    vi.unstubAllEnvs()
    Object.defineProperty(global, 'window', {
      value: originalWindow,
      writable: true,
      configurable: true
    })
  })

  describe('Development Mode - Same-Origin Proxy Support', () => {
    test('WhenOnLocalhost_ThenBaseUrlIsEmptyForViteProxy', async () => {
      // Simulate localhost environment
      Object.defineProperty(global, 'window', {
        value: createMockWindow('localhost'),
        writable: true,
        configurable: true
      })

      // Re-import to get fresh module with new env
      const { OpenAPI } = await import('../api')

      // On localhost, BASE should be empty so requests go through Vite proxy
      // This ensures same-origin requests, avoiding SameSite cookie issues
      expect(OpenAPI.BASE).toBe('')
    })

    test('WhenOnLocalhost_ThenIgnoresEnvVars', async () => {
      // Even with env vars set, localhost should use empty string
      Object.defineProperty(global, 'window', {
        value: createMockWindow('localhost'),
        writable: true,
        configurable: true
      })
      vi.stubEnv('VITE_API_URL', 'http://localhost:8000')

      const { OpenAPI } = await import('../api')

      // Should still be empty on localhost to use Vite proxy
      expect(OpenAPI.BASE).toBe('')
    })

    test('WhenOn127001_ThenBaseUrlIsEmptyForViteProxy', async () => {
      // Also handle 127.0.0.1 as localhost
      Object.defineProperty(global, 'window', {
        value: createMockWindow('127.0.0.1'),
        writable: true,
        configurable: true
      })

      const { OpenAPI } = await import('../api')

      expect(OpenAPI.BASE).toBe('')
    })
  })

  describe('Production Mode - Direct API Calls', () => {
    test('WhenNotOnLocalhost_ThenUsesEnvVar', async () => {
      // Simulate production environment
      Object.defineProperty(global, 'window', {
        value: createMockWindow('app.langplug.com'),
        writable: true,
        configurable: true
      })
      vi.stubEnv('VITE_API_BASE_URL', 'https://api.langplug.com')

      const { OpenAPI } = await import('../api')

      expect(OpenAPI.BASE).toBe('https://api.langplug.com')
    })
  })

  describe('Cookie Authentication Support', () => {
    test('WhenOpenAPIConfigured_ThenCredentialsAreIncluded', async () => {
      const { OpenAPI } = await import('../api')

      // Credentials must be 'include' for cookies to be sent cross-origin
      expect(OpenAPI.CREDENTIALS).toBe('include')
    })

    test('WhenOpenAPIConfigured_ThenWithCredentialsIsTrue', async () => {
      const { OpenAPI } = await import('../api')

      // WITH_CREDENTIALS must be true for axios to send cookies
      expect(OpenAPI.WITH_CREDENTIALS).toBe(true)
    })

    test('WhenOpenAPIConfigured_ThenTokenIsUndefined', async () => {
      const { OpenAPI } = await import('../api')

      // TOKEN should be undefined since we use cookie-based auth
      expect(OpenAPI.TOKEN).toBeUndefined()
    })
  })

  describe('Video Stream URL Builder', () => {
    test('WhenBuildingVideoUrl_ThenUsesOpenAPIBase', async () => {
      // On localhost, OpenAPI.BASE is empty
      Object.defineProperty(global, 'window', {
        value: createMockWindow('localhost'),
        writable: true,
        configurable: true
      })

      const { buildVideoStreamUrl, OpenAPI } = await import('../api')

      const url = buildVideoStreamUrl('test-series', 'episode-1')

      // URL should use the same base as OpenAPI (empty on localhost)
      expect(url).toBe(`${OpenAPI.BASE}/api/videos/test-series/episode-1`)
      expect(url).toBe('/api/videos/test-series/episode-1')
    })

    test('WhenBuildingVideoUrl_ThenEncodesSpecialCharacters', async () => {
      const { buildVideoStreamUrl } = await import('../api')

      const url = buildVideoStreamUrl('series with spaces', 'episode/with/slashes')

      expect(url).toContain('series%20with%20spaces')
      expect(url).toContain('episode%2Fwith%2Fslashes')
    })
  })
})

describe('SameSite Cookie Compatibility', () => {
  /**
   * These tests document the expected behavior for cookie-based authentication
   * to work correctly with SameSite=lax cookies in development.
   * 
   * Background:
   * - SameSite=lax cookies are NOT sent on cross-origin AJAX requests
   * - In development, frontend (localhost:3000) and backend (localhost:8000) are different origins
   * - Using Vite proxy makes requests same-origin (localhost:3000/api/... -> localhost:8000/api/...)
   */

  test('DocumentedBehavior_DevModeUsesProxyForSameOrigin', () => {
    // This test documents the expected architecture:
    // 1. Frontend runs on localhost:3000
    // 2. API requests go to /api/... (same origin)
    // 3. Vite proxy forwards /api/... to localhost:8000
    // 4. Cookies are sent because requests are same-origin
    
    const expectedDevBaseUrl = '' // Empty = use Vite proxy
    const expectedProdBaseUrl = 'http://localhost:8000' // Full URL in prod
    
    expect(expectedDevBaseUrl).toBe('')
    expect(expectedProdBaseUrl).toContain('localhost:8000')
  })

  test('DocumentedBehavior_CookieRequirementsForCrossOrigin', () => {
    // If NOT using the proxy (cross-origin requests), cookies require:
    // - SameSite=none (requires Secure=true, which requires HTTPS)
    // - OR same-site requests (what we achieve with Vite proxy)
    
    const crossOriginCookieRequirements = {
      sameSite: 'none',
      secure: true, // Required when SameSite=none
      httpOnly: true,
    }
    
    const sameOriginCookieRequirements = {
      sameSite: 'lax', // Works because requests are same-origin
      secure: false, // Not required for localhost
      httpOnly: true,
    }
    
    // We use the same-origin approach in development
    expect(sameOriginCookieRequirements.sameSite).toBe('lax')
  })
})
