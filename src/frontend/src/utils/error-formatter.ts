/**
 * Centralized error message formatting
 * Extracts user-friendly error messages from API errors
 */

export interface ValidationErrorItem {
  loc?: (string | number)[]
  msg?: string
  type?: string
}

export interface ApiError {
  body?: {
    detail?: string | ValidationErrorItem[]
    // Custom error format used by LangPlug backend
    error?: {
      code?: string
      message?: string
      details?: ValidationErrorItem[]
    }
  }
  message?: string
  status?: number
  headers?: {
    'retry-after'?: string
  }
  response?: {
    data?: {
      detail?: string | Array<{ msg?: string }>
      error?: {
        code?: string
        message?: string
        details?: Array<{ msg?: string }>
      }
    }
    status?: number
    headers?: {
      'retry-after'?: string
    }
  }
}

/**
 * Strip Pydantic's "Value error, " prefix from validation messages
 */
function cleanValidationMessage(msg: string): string {
  // Pydantic prefixes ValueError messages with "Value error, "
  if (msg.startsWith('Value error, ')) {
    return msg.slice('Value error, '.length)
  }
  return msg
}

/**
 * Format API error into user-friendly message
 * @param error - Error object from API call
 * @param fallback - Default message if no specific error found
 * @returns Formatted error message
 */
export function formatApiError(error: unknown, fallback: string): string {
  if (!error) return fallback

  const err = error as ApiError
  
  // Try body.error.details first (LangPlug custom validation error format)
  if (err?.body?.error?.details && Array.isArray(err.body.error.details)) {
    const messages = err.body.error.details
      .map(item => item.msg ? cleanValidationMessage(item.msg) : JSON.stringify(item))
      .filter(Boolean)
    if (messages.length > 0) return messages.join('; ')
  }
  
  // Try body.detail (standard FastAPI/OpenAPI format)
  if (err?.body?.detail) {
    const detail = err.body.detail
    // Handle array of validation errors (Pydantic/FastAPI 422 format)
    if (Array.isArray(detail)) {
      const messages = detail
        .map(item => item.msg ? cleanValidationMessage(item.msg) : JSON.stringify(item))
        .filter(Boolean)
      return messages.length > 0 ? messages.join('; ') : fallback
    }
    // Handle string detail
    if (typeof detail === 'string') {
      return cleanValidationMessage(detail)
    }
  }
  
  // Try response.data.error.details (axios + LangPlug custom format)
  if (err?.response?.data?.error?.details && Array.isArray(err.response.data.error.details)) {
    const messages = err.response.data.error.details
      .map(item => item.msg ? cleanValidationMessage(item.msg) : JSON.stringify(item))
      .filter(Boolean)
    if (messages.length > 0) return messages.join('; ')
  }
  
  // Try response.data.detail (axios-style format)
  if (err?.response?.data?.detail) {
    const detail = err.response.data.detail
    // Handle array of validation errors
    if (Array.isArray(detail)) {
      const messages = detail
        .map(item => item.msg ? cleanValidationMessage(item.msg) : JSON.stringify(item))
        .filter(Boolean)
      return messages.length > 0 ? messages.join('; ') : fallback
    }
    // Handle string detail
    if (typeof detail === 'string') {
      return cleanValidationMessage(detail)
    }
  }
  
  // Try message property
  if (err?.message) return err.message

  return fallback
}

/**
 * Check if error is a specific HTTP status code
 */
export function isHttpError(error: unknown, statusCode: number): boolean {
  const err = error as ApiError
  return err?.status === statusCode || err?.response?.status === statusCode
}

/**
 * Check if error is authentication related (401)
 */
export function isAuthError(error: unknown): boolean {
  return isHttpError(error, 401)
}

/**
 * Check if error is rate limiting (429)
 */
export function isRateLimitError(error: unknown): boolean {
  return isHttpError(error, 429)
}

/**
 * Get retry-after header from rate limit error
 */
export function getRetryAfter(error: unknown): number {
  const err = error as ApiError
  const retryAfter = err?.response?.headers?.['retry-after'] || err?.headers?.['retry-after']

  return retryAfter ? parseInt(retryAfter, 10) : 60
}
