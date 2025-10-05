/**
 * Centralized error message formatting
 * Extracts user-friendly error messages from API errors
 */

export interface ApiError {
  body?: {
    detail?: string
  }
  message?: string
  status?: number
  response?: {
    data?: {
      detail?: string | Array<{ msg?: string }>
    }
    status?: number
  }
}

/**
 * Format API error into user-friendly message
 * @param error - Error object from API call
 * @param fallback - Default message if no specific error found
 * @returns Formatted error message
 */
export function formatApiError(error: any, fallback: string): string {
  if (!error) return fallback

  // Try different error structures
  if (error?.body?.detail) return error.body.detail
  if (error?.response?.data?.detail) {
    const detail = error.response.data.detail
    // Handle array of validation errors
    if (Array.isArray(detail)) {
      return detail.map(err => err.msg || JSON.stringify(err)).join('; ')
    }
    return detail
  }
  if (error?.message) return error.message

  return fallback
}

/**
 * Check if error is a specific HTTP status code
 */
export function isHttpError(error: any, statusCode: number): boolean {
  return error?.status === statusCode || error?.response?.status === statusCode
}

/**
 * Check if error is authentication related (401)
 */
export function isAuthError(error: any): boolean {
  return isHttpError(error, 401)
}

/**
 * Check if error is rate limiting (429)
 */
export function isRateLimitError(error: any): boolean {
  return isHttpError(error, 429)
}

/**
 * Get retry-after header from rate limit error
 */
export function getRetryAfter(error: any): number {
  const retryAfter = error?.response?.headers?.['retry-after']
    || error?.headers?.['retry-after']

  return retryAfter ? parseInt(retryAfter, 10) : 60
}
