/**
 * Tests for error-formatter utility
 * Ensures API errors are formatted as user-friendly messages
 */
import { describe, it, expect } from 'vitest'
import { formatApiError, isHttpError, isAuthError, isRateLimitError } from '../error-formatter'

describe('formatApiError', () => {
  it('returns fallback for null/undefined error', () => {
    expect(formatApiError(null, 'fallback')).toBe('fallback')
    expect(formatApiError(undefined, 'fallback')).toBe('fallback')
  })

  it('strips "Value error, " prefix from Pydantic validation messages', () => {
    const error = {
      body: {
        detail: [
          { loc: ['body', 'password'], msg: 'Value error, Password must be at least 12 characters', type: 'value_error' }
        ]
      }
    }
    expect(formatApiError(error, 'fallback')).toBe('Password must be at least 12 characters')
  })

  it('handles multiple validation errors with Value error prefix', () => {
    const error = {
      body: {
        detail: [
          { loc: ['body', 'password'], msg: 'Value error, Password must be at least 12 characters', type: 'value_error' },
          { loc: ['body', 'password'], msg: 'Value error, Password must contain uppercase', type: 'value_error' }
        ]
      }
    }
    expect(formatApiError(error, 'fallback')).toBe(
      'Password must be at least 12 characters; Password must contain uppercase'
    )
  })

  it('handles validation errors without Value error prefix', () => {
    const error = {
      body: {
        detail: [
          { loc: ['body', 'email'], msg: 'Invalid email format', type: 'value_error' }
        ]
      }
    }
    expect(formatApiError(error, 'fallback')).toBe('Invalid email format')
  })

  it('handles string detail in body', () => {
    const error = { body: { detail: 'Simple error message' } }
    expect(formatApiError(error, 'fallback')).toBe('Simple error message')
  })

  it('strips Value error prefix from string detail', () => {
    const error = { body: { detail: 'Value error, Custom validation failed' } }
    expect(formatApiError(error, 'fallback')).toBe('Custom validation failed')
  })

  it('handles response.data.detail array (axios format)', () => {
    const error = {
      response: {
        data: {
          detail: [
            { msg: 'Value error, Field is required' }
          ]
        }
      }
    }
    expect(formatApiError(error, 'fallback')).toBe('Field is required')
  })

  it('handles body.error.details (LangPlug custom format)', () => {
    const error = {
      body: {
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Request validation failed',
          details: [
            { loc: ['body', 'password'], msg: 'Value error, Password must be at least 12 characters', type: 'value_error' }
          ]
        }
      }
    }
    expect(formatApiError(error, 'fallback')).toBe('Password must be at least 12 characters')
  })

  it('handles response.data.error.details (axios + LangPlug format)', () => {
    const error = {
      response: {
        data: {
          error: {
            code: 'VALIDATION_ERROR',
            details: [
              { msg: 'Value error, Username is required' }
            ]
          }
        }
      }
    }
    expect(formatApiError(error, 'fallback')).toBe('Username is required')
  })

  it('handles response.data.detail string', () => {
    const error = {
      response: {
        data: {
          detail: 'Not authenticated'
        }
      }
    }
    expect(formatApiError(error, 'fallback')).toBe('Not authenticated')
  })

  it('falls back to message property', () => {
    const error = { message: 'Network error' }
    expect(formatApiError(error, 'fallback')).toBe('Network error')
  })

  it('returns fallback when no extractable message', () => {
    const error = { status: 500 }
    expect(formatApiError(error, 'Server error')).toBe('Server error')
  })
})

describe('isHttpError', () => {
  it('detects status code from status property', () => {
    expect(isHttpError({ status: 404 }, 404)).toBe(true)
    expect(isHttpError({ status: 404 }, 500)).toBe(false)
  })

  it('detects status code from response.status', () => {
    expect(isHttpError({ response: { status: 401 } }, 401)).toBe(true)
  })
})

describe('isAuthError', () => {
  it('returns true for 401 errors', () => {
    expect(isAuthError({ status: 401 })).toBe(true)
    expect(isAuthError({ status: 403 })).toBe(false)
  })
})

describe('isRateLimitError', () => {
  it('returns true for 429 errors', () => {
    expect(isRateLimitError({ status: 429 })).toBe(true)
    expect(isRateLimitError({ status: 500 })).toBe(false)
  })
})
