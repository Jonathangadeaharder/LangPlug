import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { getApiConfig } from '../../config/api-config'

describe('API Connection Configuration', () => {
  let originalEnv: string | undefined
  let originalMode: string | undefined

  beforeEach(() => {
    // Save original values
    originalEnv = import.meta.env.VITE_API_URL
    originalMode = import.meta.env.VITE_ENVIRONMENT
  })

  afterEach(() => {
    // Restore original values after each test
    if (originalEnv !== undefined) {
      import.meta.env.VITE_API_URL = originalEnv
    } else {
      delete import.meta.env.VITE_API_URL
    }
    if (originalMode !== undefined) {
      import.meta.env.VITE_ENVIRONMENT = originalMode
    } else {
      delete import.meta.env.VITE_ENVIRONMENT
    }
  })

  it('should use environment variable for API URL when provided', () => {
    // Test that VITE_API_URL overrides the default in development mode
    import.meta.env.VITE_ENVIRONMENT = 'development'
    import.meta.env.VITE_API_URL = 'http://localhost:9999'
    const config = getApiConfig()

    expect(config.baseUrl).toBe('http://localhost:9999')
  })

  it('should default to port 8000 when no environment variable is set', () => {
    // Ensure development mode with no custom URL
    import.meta.env.VITE_ENVIRONMENT = 'development'
    delete import.meta.env.VITE_API_URL

    const config = getApiConfig()
    expect(config.baseUrl).toBe('http://localhost:8000')
  })

  it('should match Backend port configuration', () => {
    // This test documents the expected coordination between Frontend and Backend
    // Use test environment which has a default baseUrl
    import.meta.env.VITE_ENVIRONMENT = 'test'

    const config = getApiConfig()
    const url = new URL(config.baseUrl)

    // Backend should be running on the same port that Frontend expects
    // This is a contract test - if this fails, Frontend and Backend are misconfigured
    expect(['8000', '8001', '8002', '8003']).toContain(url.port || '80')
  })
})
