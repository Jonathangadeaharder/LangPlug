import { describe, it, expect } from 'vitest'
import {
  formatApiError,
  isHttpError,
  isAuthError,
  isRateLimitError,
  getRetryAfter,
  ApiError,
} from '../error-formatter'

describe('error-formatter', () => {
  describe('formatApiError', () => {
    it('should extract error from body.detail', () => {
      const error: ApiError = {
        body: {
          detail: 'Invalid credentials',
        },
      }

      const result = formatApiError(error, 'Fallback')
      expect(result).toBe('Invalid credentials')
    })

    it('should extract error from response.data.detail (string)', () => {
      const error: ApiError = {
        response: {
          data: {
            detail: 'User not found',
          },
        },
      }

      const result = formatApiError(error, 'Fallback')
      expect(result).toBe('User not found')
    })

    it('should extract error from response.data.detail (array)', () => {
      const error: ApiError = {
        response: {
          data: {
            detail: [
              { msg: 'Field is required' },
              { msg: 'Invalid email format' },
            ],
          },
        },
      }

      const result = formatApiError(error, 'Fallback')
      expect(result).toBe('Field is required; Invalid email format')
    })

    it('should handle validation errors without msg property', () => {
      const error: ApiError = {
        response: {
          data: {
            detail: [
              { field: 'email', error: 'invalid' },
            ],
          },
        },
      }

      const result = formatApiError(error, 'Fallback')
      expect(result).toContain('email')
    })

    it('should extract error from message property', () => {
      const error: ApiError = {
        message: 'Network error occurred',
      }

      const result = formatApiError(error, 'Fallback')
      expect(result).toBe('Network error occurred')
    })

    it('should return fallback for null error', () => {
      const result = formatApiError(null, 'Default error')
      expect(result).toBe('Default error')
    })

    it('should return fallback for undefined error', () => {
      const result = formatApiError(undefined, 'Default error')
      expect(result).toBe('Default error')
    })

    it('should return fallback for empty error object', () => {
      const result = formatApiError({}, 'Default error')
      expect(result).toBe('Default error')
    })

    it('should prioritize body.detail over response.data.detail', () => {
      const error: ApiError = {
        body: {
          detail: 'Body error',
        },
        response: {
          data: {
            detail: 'Response error',
          },
        },
      }

      const result = formatApiError(error, 'Fallback')
      expect(result).toBe('Body error')
    })

    it('should prioritize response.data.detail over message', () => {
      const error: ApiError = {
        response: {
          data: {
            detail: 'Response error',
          },
        },
        message: 'Generic error',
      }

      const result = formatApiError(error, 'Fallback')
      expect(result).toBe('Response error')
    })

    it('should handle Error instances', () => {
      const error = new Error('Something went wrong')

      const result = formatApiError(error, 'Fallback')
      expect(result).toBe('Something went wrong')
    })
  })

  describe('isHttpError', () => {
    it('should return true for matching status code', () => {
      const error: ApiError = {
        status: 404,
      }

      expect(isHttpError(error, 404)).toBe(true)
    })

    it('should return true for matching response.status code', () => {
      const error: ApiError = {
        response: {
          status: 500,
        },
      }

      expect(isHttpError(error, 500)).toBe(true)
    })

    it('should return false for non-matching status code', () => {
      const error: ApiError = {
        status: 200,
      }

      expect(isHttpError(error, 404)).toBe(false)
    })

    it('should return false for error without status', () => {
      const error: ApiError = {
        message: 'Some error',
      }

      expect(isHttpError(error, 404)).toBe(false)
    })

    it('should return false for null error', () => {
      expect(isHttpError(null, 404)).toBe(false)
    })

    it('should return false for undefined error', () => {
      expect(isHttpError(undefined, 404)).toBe(false)
    })

    it('should prioritize status over response.status', () => {
      const error: ApiError = {
        status: 400,
        response: {
          status: 500,
        },
      }

      expect(isHttpError(error, 400)).toBe(true)
      expect(isHttpError(error, 500)).toBe(false)
    })
  })

  describe('isAuthError', () => {
    it('should return true for 401 status', () => {
      const error: ApiError = {
        status: 401,
      }

      expect(isAuthError(error)).toBe(true)
    })

    it('should return true for 401 response.status', () => {
      const error: ApiError = {
        response: {
          status: 401,
        },
      }

      expect(isAuthError(error)).toBe(true)
    })

    it('should return false for non-401 status', () => {
      const error: ApiError = {
        status: 404,
      }

      expect(isAuthError(error)).toBe(false)
    })

    it('should return false for 403 (forbidden, not unauthorized)', () => {
      const error: ApiError = {
        status: 403,
      }

      expect(isAuthError(error)).toBe(false)
    })

    it('should return false for error without status', () => {
      const error: ApiError = {
        message: 'Error',
      }

      expect(isAuthError(error)).toBe(false)
    })
  })

  describe('isRateLimitError', () => {
    it('should return true for 429 status', () => {
      const error: ApiError = {
        status: 429,
      }

      expect(isRateLimitError(error)).toBe(true)
    })

    it('should return true for 429 response.status', () => {
      const error: ApiError = {
        response: {
          status: 429,
        },
      }

      expect(isRateLimitError(error)).toBe(true)
    })

    it('should return false for non-429 status', () => {
      const error: ApiError = {
        status: 500,
      }

      expect(isRateLimitError(error)).toBe(false)
    })

    it('should return false for error without status', () => {
      expect(isRateLimitError({})).toBe(false)
    })
  })

  describe('getRetryAfter', () => {
    it('should extract retry-after from response headers', () => {
      const error: ApiError = {
        response: {
          headers: {
            'retry-after': '120',
          },
        },
      }

      const result = getRetryAfter(error)
      expect(result).toBe(120)
    })

    it('should extract retry-after from direct headers', () => {
      const error: ApiError = {
        headers: {
          'retry-after': '90',
        },
      }

      const result = getRetryAfter(error)
      expect(result).toBe(90)
    })

    it('should return default 60 when no retry-after header', () => {
      const error: ApiError = {
        status: 429,
      }

      const result = getRetryAfter(error)
      expect(result).toBe(60)
    })

    it('should return default 60 for null error', () => {
      const result = getRetryAfter(null)
      expect(result).toBe(60)
    })

    it('should return default 60 for undefined error', () => {
      const result = getRetryAfter(undefined)
      expect(result).toBe(60)
    })

    it('should parse string retry-after value', () => {
      const error: ApiError = {
        headers: {
          'retry-after': '180',
        },
      }

      const result = getRetryAfter(error)
      expect(result).toBe(180)
    })

    it('should handle invalid retry-after value', () => {
      const error: ApiError = {
        headers: {
          'retry-after': 'invalid',
        },
      }

      const result = getRetryAfter(error)
      expect(result).toBe(NaN) // parseInt('invalid') returns NaN
    })

    it('should prioritize response.headers over direct headers', () => {
      const error: ApiError = {
        headers: {
          'retry-after': '30',
        },
        response: {
          headers: {
            'retry-after': '120',
          },
        },
      }

      const result = getRetryAfter(error)
      expect(result).toBe(120)
    })
  })

  describe('integration scenarios', () => {
    it('should handle complete 401 error with message', () => {
      const error: ApiError = {
        status: 401,
        body: {
          detail: 'Invalid token',
        },
      }

      expect(isAuthError(error)).toBe(true)
      expect(formatApiError(error, 'Login failed')).toBe('Invalid token')
    })

    it('should handle complete 429 error with retry-after', () => {
      const error: ApiError = {
        status: 429,
        response: {
          status: 429,
          data: {
            detail: 'Too many requests',
          },
          headers: {
            'retry-after': '300',
          },
        },
      }

      expect(isRateLimitError(error)).toBe(true)
      expect(formatApiError(error, 'Rate limited')).toBe('Too many requests')
      expect(getRetryAfter(error)).toBe(300)
    })

    it('should handle validation error (400) with multiple messages', () => {
      const error: ApiError = {
        status: 400,
        response: {
          status: 400,
          data: {
            detail: [
              { msg: 'Email is required' },
              { msg: 'Password must be at least 8 characters' },
            ],
          },
        },
      }

      expect(isHttpError(error, 400)).toBe(true)
      expect(formatApiError(error, 'Validation failed')).toBe(
        'Email is required; Password must be at least 8 characters'
      )
    })
  })
})
