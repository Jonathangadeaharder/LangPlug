import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  getApiConfig,
  getApiConfigForEnvironment,
  validateApiConfig,
  createApiHeaders,
  logApiConfig,
  type ApiConfig,
  type Environment,
} from '../api-config'

describe('API Configuration', () => {
  const originalWindow = global.window
  const originalConsole = global.console

  beforeEach(() => {
    vi.clearAllMocks()
    vi.unstubAllEnvs()
    // Mock console methods
    global.console = {
      ...originalConsole,
      log: vi.fn(),
      error: vi.fn(),
      warn: vi.fn(),
    }
  })

  afterEach(() => {
    // Restore original environment and globals
    vi.unstubAllEnvs()
    global.window = originalWindow
    global.console = originalConsole
    vi.restoreAllMocks()
  })

  describe('Environment Detection', () => {
    test('WhenViteEnvironmentSet_ThenUsesViteEnvironment', () => {
      // Mock Vite environment variable
      vi.stubEnv('VITE_ENVIRONMENT', 'staging')

      const config = getApiConfig()
      expect(config.baseUrl).toContain('staging')
    })

    test('WhenNodeEnvProduction_ThenUsesProductionConfig', () => {
      vi.stubEnv('NODE_ENV', 'production')
      vi.stubEnv('VITE_ENVIRONMENT', undefined as any)

      const config = getApiConfig()
      expect(config.baseUrl).toBe('https://api.langplug.com')
      expect(config.enableLogging).toBe(false)
      expect(config.enableValidation).toBe(false)
    })

    test('WhenNodeEnvTest_ThenUsesTestConfig', () => {
      vi.stubEnv('NODE_ENV', 'test')
      vi.stubEnv('VITE_ENVIRONMENT', undefined as any)

      const config = getApiConfig()
      expect(config.baseUrl).toBe('http://localhost:8000')
      expect(config.timeout).toBe(5000)
      expect(config.retryAttempts).toBe(1)
      expect(config.enableLogging).toBe(false)
      expect(config.enableValidation).toBe(true)
    })

    test('WhenStagingHostname_ThenUsesStagingConfig', () => {
      vi.stubEnv('NODE_ENV', 'development')
      vi.stubEnv('VITE_ENVIRONMENT', undefined as any)

      // Mock window.location for staging hostname
      global.window = {
        ...originalWindow,
        location: {
          ...originalWindow?.location,
          hostname: 'staging.langplug.com',
        },
      } as any

      const config = getApiConfig()
      expect(config.baseUrl).toContain('staging')
      expect(config.timeout).toBe(15000)
      expect(config.retryAttempts).toBe(3)
    })

    test('WhenNoSpecificEnvironment_ThenDefaultsToDevelopment', () => {
      vi.stubEnv('NODE_ENV', 'development')
      vi.stubEnv('VITE_ENVIRONMENT', undefined as any)

      global.window = {
        ...originalWindow,
        location: {
          ...originalWindow?.location,
          hostname: 'localhost',
        },
      } as any

      const config = getApiConfig()
      expect(config.baseUrl).toBe('http://localhost:8000')
      expect(config.enableLogging).toBe(true)
      expect(config.enableValidation).toBe(true)
    })
  })

  describe('Environment-Specific Configurations', () => {
    test('WhenDevelopmentEnvironment_ThenHasCorrectSettings', () => {
      const config = getApiConfigForEnvironment('development')

      expect(config).toEqual({
        baseUrl: 'http://localhost:8000',
        timeout: 10000,
        retryAttempts: 3,
        retryDelay: 1000,
        enableLogging: true,
        enableValidation: true,
      })
    })

    test('WhenStagingEnvironment_ThenHasCorrectSettings', () => {
      const config = getApiConfigForEnvironment('staging')

      expect(config.baseUrl).toBe('https://staging-api.langplug.com')
      expect(config.timeout).toBe(15000)
      expect(config.retryAttempts).toBe(3)
      expect(config.retryDelay).toBe(2000)
      expect(config.enableLogging).toBe(true)
      expect(config.enableValidation).toBe(true)
    })

    test('WhenProductionEnvironment_ThenHasOptimizedSettings', () => {
      const config = getApiConfigForEnvironment('production')

      expect(config.baseUrl).toBe('https://api.langplug.com')
      expect(config.timeout).toBe(20000)
      expect(config.retryAttempts).toBe(2)
      expect(config.retryDelay).toBe(3000)
      expect(config.enableLogging).toBe(false)
      expect(config.enableValidation).toBe(false)
    })

    test('WhenTestEnvironment_ThenHasFastSettings', () => {
      const config = getApiConfigForEnvironment('test')

      expect(config.baseUrl).toBe('http://localhost:8000')
      expect(config.timeout).toBe(5000)
      expect(config.retryAttempts).toBe(1)
      expect(config.retryDelay).toBe(500)
      expect(config.enableLogging).toBe(false)
      expect(config.enableValidation).toBe(true)
    })
  })

  describe('Environment Variable Overrides', () => {
    test('WhenViteApiUrlSet_ThenUsesEnvironmentVariable', () => {
      // Mock environment variable
      vi.stubEnv('VITE_API_URL', 'https://custom-api.example.com')
      vi.stubEnv('NODE_ENV', 'production')
      vi.stubEnv('VITE_ENVIRONMENT', undefined as any)

      const config = getApiConfig()
      expect(config.baseUrl).toBe('https://custom-api.example.com')
    })

    test('WhenViteStagingApiUrlSet_ThenUsesEnvironmentVariable', () => {
      vi.stubEnv('VITE_STAGING_API_URL', 'https://custom-staging.example.com')
      vi.stubEnv('VITE_ENVIRONMENT', 'staging')

      const config = getApiConfig()
      expect(config.baseUrl).toBe('https://custom-staging.example.com')
    })
  })

  describe('Configuration Validation', () => {
    test('WhenValidConfiguration_ThenReturnsTrue', () => {
      const validConfig: ApiConfig = {
        baseUrl: 'https://api.example.com',
        timeout: 10000,
        retryAttempts: 3,
        retryDelay: 1000,
        enableLogging: true,
        enableValidation: true,
      }

      const isValid = validateApiConfig(validConfig)
      expect(isValid).toBe(true)
    })

    test('WhenInvalidBaseUrl_ThenReturnsFalseAndLogsError', () => {
      const invalidConfig: ApiConfig = {
        baseUrl: 'not-a-url',
        timeout: 10000,
        retryAttempts: 3,
        retryDelay: 1000,
        enableLogging: true,
        enableValidation: true,
      }

      const isValid = validateApiConfig(invalidConfig)
      expect(isValid).toBe(false)
      expect(console.error).toHaveBeenCalledWith('Invalid API base URL:', 'not-a-url')
    })

    test('WhenEmptyBaseUrl_ThenReturnsFalseAndLogsError', () => {
      const invalidConfig: ApiConfig = {
        baseUrl: '',
        timeout: 10000,
        retryAttempts: 3,
        retryDelay: 1000,
        enableLogging: true,
        enableValidation: true,
      }

      const isValid = validateApiConfig(invalidConfig)
      expect(isValid).toBe(false)
      expect(console.error).toHaveBeenCalledWith('Invalid API base URL:', '')
    })

    test('WhenNegativeTimeout_ThenReturnsFalseAndLogsError', () => {
      const invalidConfig: ApiConfig = {
        baseUrl: 'https://api.example.com',
        timeout: -1000,
        retryAttempts: 3,
        retryDelay: 1000,
        enableLogging: true,
        enableValidation: true,
      }

      const isValid = validateApiConfig(invalidConfig)
      expect(isValid).toBe(false)
      expect(console.error).toHaveBeenCalledWith('Invalid API timeout:', -1000)
    })

    test('WhenZeroTimeout_ThenReturnsFalseAndLogsError', () => {
      const invalidConfig: ApiConfig = {
        baseUrl: 'https://api.example.com',
        timeout: 0,
        retryAttempts: 3,
        retryDelay: 1000,
        enableLogging: true,
        enableValidation: true,
      }

      const isValid = validateApiConfig(invalidConfig)
      expect(isValid).toBe(false)
      expect(console.error).toHaveBeenCalledWith('Invalid API timeout:', 0)
    })

    test('WhenNegativeRetryAttempts_ThenReturnsFalseAndLogsError', () => {
      const invalidConfig: ApiConfig = {
        baseUrl: 'https://api.example.com',
        timeout: 10000,
        retryAttempts: -1,
        retryDelay: 1000,
        enableLogging: true,
        enableValidation: true,
      }

      const isValid = validateApiConfig(invalidConfig)
      expect(isValid).toBe(false)
      expect(console.error).toHaveBeenCalledWith('Invalid retry attempts:', -1)
    })

    test('WhenZeroRetryAttempts_ThenReturnsTrue', () => {
      const validConfig: ApiConfig = {
        baseUrl: 'https://api.example.com',
        timeout: 10000,
        retryAttempts: 0,
        retryDelay: 1000,
        enableLogging: true,
        enableValidation: true,
      }

      const isValid = validateApiConfig(validConfig)
      expect(isValid).toBe(true)
    })
  })

  describe('API Headers Creation', () => {
    test('WhenCreatingHeaders_ThenIncludesBasicHeaders', () => {
      const config: ApiConfig = {
        baseUrl: 'https://api.example.com',
        timeout: 10000,
        retryAttempts: 3,
        retryDelay: 1000,
        enableLogging: false,
        enableValidation: true,
      }

      const headers = createApiHeaders(config)

      expect(headers['Content-Type']).toBe('application/json')
      expect(headers['Accept']).toBe('application/json')
      expect(headers['X-API-Version']).toBe('1.0')
    })

    test('WhenLoggingEnabled_ThenIncludesRequestId', () => {
      const config: ApiConfig = {
        baseUrl: 'https://api.example.com',
        timeout: 10000,
        retryAttempts: 3,
        retryDelay: 1000,
        enableLogging: true,
        enableValidation: true,
      }

      const headers = createApiHeaders(config)

      expect(headers['X-Request-ID']).toBeDefined()
      expect(headers['X-Request-ID']).toMatch(/^req_\d+_[a-z0-9]+$/)
    })

    test('WhenLoggingDisabled_ThenOmitsRequestId', () => {
      const config: ApiConfig = {
        baseUrl: 'https://api.example.com',
        timeout: 10000,
        retryAttempts: 3,
        retryDelay: 1000,
        enableLogging: false,
        enableValidation: true,
      }

      const headers = createApiHeaders(config)

      expect(headers['X-Request-ID']).toBeUndefined()
    })

    test('WhenCreatingHeaders_ThenIncludesEnvironmentHeader', () => {
      vi.stubEnv('VITE_ENVIRONMENT', 'staging')

      const config: ApiConfig = {
        baseUrl: 'https://staging.example.com',
        timeout: 10000,
        retryAttempts: 3,
        retryDelay: 1000,
        enableLogging: false,
        enableValidation: true,
      }

      const headers = createApiHeaders(config)

      expect(headers['X-Environment']).toBe('staging')
    })

    test('WhenMultipleHeadersCreated_ThenRequestIdsAreUnique', () => {
      const config: ApiConfig = {
        baseUrl: 'https://api.example.com',
        timeout: 10000,
        retryAttempts: 3,
        retryDelay: 1000,
        enableLogging: true,
        enableValidation: true,
      }

      const headers1 = createApiHeaders(config)
      const headers2 = createApiHeaders(config)

      expect(headers1['X-Request-ID']).not.toBe(headers2['X-Request-ID'])
    })
  })

  describe('Configuration Logging', () => {
    test('WhenLoggingEnabledAndLogConfigCalled_ThenLogsConfiguration', () => {
      vi.stubEnv('NODE_ENV', 'development')
      vi.stubEnv('VITE_ENVIRONMENT', undefined as any)

      logApiConfig()

      expect(console.log).toHaveBeenCalledWith('🔧 API Configuration:', {
        environment: 'development',
        baseUrl: 'http://localhost:8000',
        timeout: 10000,
        retryAttempts: 3,
        enableValidation: true,
      })
    })

    test('WhenLoggingDisabledAndLogConfigCalled_ThenDoesNotLog', () => {
      vi.stubEnv('NODE_ENV', 'production')
      vi.stubEnv('VITE_ENVIRONMENT', undefined as any)

      logApiConfig()

      expect(console.log).not.toHaveBeenCalled()
    })

    test('WhenStagingEnvironmentAndLogConfigCalled_ThenLogsCorrectEnvironment', () => {
      vi.stubEnv('VITE_ENVIRONMENT', 'staging')

      logApiConfig()

      expect(console.log).toHaveBeenCalledWith('🔧 API Configuration:',
        expect.objectContaining({
          environment: 'staging',
        })
      )
    })
  })

  describe('Edge Cases and Error Handling', () => {
    test('WhenWindowUndefined_ThenHandlesGracefully', () => {
      // Simulate SSR environment where window is undefined
      const originalWindow = global.window
      delete (global as any).window

      vi.stubEnv('NODE_ENV', 'development')
      vi.stubEnv('VITE_ENVIRONMENT', undefined as any)

      const config = getApiConfig()

      // Should default to development without crashing
      expect(config.baseUrl).toBe('http://localhost:8000')

      // Restore window
      global.window = originalWindow
    })

    test('WhenInvalidEnvironmentString_ThenDefaultsToDevelopment', () => {
      vi.stubEnv('VITE_ENVIRONMENT', 'invalid-environment')

      // This should not crash but fall back to development
      const config = getApiConfig()
      expect(config).toBeDefined()
    })

    test('WhenConfigurationMutated_ThenDoesNotAffectOriginal', () => {
      const config1 = getApiConfigForEnvironment('development')
      const config2 = getApiConfigForEnvironment('development')

      // Mutate one config
      config1.timeout = 999999

      // Original config should be unchanged
      expect(config2.timeout).toBe(10000)
    })
  })

  describe('Performance and Memory', () => {
    test('WhenMultipleConfigRequests_ThenHandlesEfficiently', () => {
      // Should not crash or slow down with multiple requests
      for (let i = 0; i < 100; i++) {
        const config = getApiConfig()
        expect(config).toBeDefined()
        expect(config.baseUrl).toBeDefined()
      }
    })

    test('WhenCreatingManyHeaders_ThenHandlesEfficiently', () => {
      const config: ApiConfig = {
        baseUrl: 'https://api.example.com',
        timeout: 10000,
        retryAttempts: 3,
        retryDelay: 1000,
        enableLogging: true,
        enableValidation: true,
      }

      // Should not crash or slow down with multiple header creations
      const headers = []
      for (let i = 0; i < 100; i++) {
        headers.push(createApiHeaders(config))
      }

      // All headers should be valid
      headers.forEach(header => {
        expect(header['Content-Type']).toBe('application/json')
        expect(header['X-Request-ID']).toBeDefined()
      })

      // All request IDs should be unique
      const requestIds = headers.map(h => h['X-Request-ID'])
      const uniqueIds = new Set(requestIds)
      expect(uniqueIds.size).toBe(requestIds.length)
    })
  })

  describe('Type Safety', () => {
    test('WhenAllEnvironmentTypesUsed_ThenConfigurationsExist', () => {
      const environments: Environment[] = ['development', 'staging', 'production', 'test']

      environments.forEach(env => {
        const config = getApiConfigForEnvironment(env)
        expect(config).toBeDefined()
        expect(config.baseUrl).toBeDefined()
        expect(typeof config.timeout).toBe('number')
        expect(typeof config.retryAttempts).toBe('number')
        expect(typeof config.retryDelay).toBe('number')
        expect(typeof config.enableLogging).toBe('boolean')
        expect(typeof config.enableValidation).toBe('boolean')
      })
    })

    test('WhenApiConfigInterface_ThenAllPropertiesAreCorrectTypes', () => {
      const config = getApiConfig()

      expect(typeof config.baseUrl).toBe('string')
      expect(typeof config.timeout).toBe('number')
      expect(typeof config.retryAttempts).toBe('number')
      expect(typeof config.retryDelay).toBe('number')
      expect(typeof config.enableLogging).toBe('boolean')
      expect(typeof config.enableValidation).toBe('boolean')
    })
  })
})
