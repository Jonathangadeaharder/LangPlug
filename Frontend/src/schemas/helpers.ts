/**
 * Helper functions for working with Zod validation schemas
 */

import { ZodError, ZodIssue } from 'zod'

/**
 * Form errors object type
 */
export type FormErrors = Record<string, string>

/**
 * Convert Zod validation error to form errors object
 *
 * @param error - Zod validation error
 * @returns Object mapping field names to error messages
 *
 * @example
 * try {
 *   const validData = schema.parse(formData)
 * } catch (error) {
 *   const formErrors = zodErrorToFormErrors(error)
 *   // { email: "Invalid email format", password: "Must be at least 8 characters" }
 * }
 */
export function zodErrorToFormErrors(error: unknown): FormErrors {
  if (!(error instanceof ZodError)) {
    return { _general: 'Validation failed' }
  }

  const formErrors: FormErrors = {}

  error.issues.forEach((issue: ZodIssue) => {
    const fieldPath = issue.path.join('.')
    const fieldName = fieldPath || '_general'

    // Get human-readable error message
    formErrors[fieldName] = formatZodIssue(issue)
  })

  return formErrors
}

/**
 * Format a Zod issue into a user-friendly error message
 */
function formatZodIssue(issue: ZodIssue): string {
  const { code, message } = issue

  // Customize messages based on error type
  switch (code) {
    case 'too_small':
      if ('minimum' in issue) {
        return `Must be at least ${(issue as any).minimum} characters`
      }
      return message

    case 'too_big':
      if ('maximum' in issue) {
        return `Must be at most ${(issue as any).maximum} characters`
      }
      return message

    case 'invalid_string':
      if ('validation' in issue && (issue as any).validation === 'email') {
        return 'Invalid email format'
      }
      return message

    case 'invalid_type':
      if ('expected' in issue && 'received' in issue) {
        return `Expected ${(issue as any).expected}, received ${(issue as any).received}`
      }
      return message

    default:
      return message
  }
}

/**
 * Check if a Zod schema validates successfully (without throwing)
 *
 * @param schema - Zod schema
 * @param data - Data to validate
 * @returns true if valid, false if invalid
 *
 * @example
 * if (isValid(UserRegisterSchema, formData)) {
 *   // Form is valid
 * }
 */
export function isValid<T>(schema: { safeParse: (data: unknown) => { success: boolean, data?: T } }, data: unknown): data is T {
  const result = schema.safeParse(data)
  return result.success
}

/**
 * Validate data and return either the validated data or form errors
 *
 * @param schema - Zod schema
 * @param data - Data to validate
 * @returns Object with either 'data' or 'errors'
 *
 * @example
 * const result = validateWithErrors(UserRegisterSchema, formData)
 * if ('errors' in result) {
 *   setFormErrors(result.errors)
 * } else {
 *   submitForm(result.data)
 * }
 */
export function validateWithErrors<T>(
  schema: { safeParse: (data: unknown) => { success: boolean, data?: T, error?: ZodError } },
  data: unknown
): { data: T } | { errors: FormErrors } {
  const result = schema.safeParse(data)

  if (result.success) {
    return { data: result.data as T }
  } else {
    return { errors: zodErrorToFormErrors(result.error) }
  }
}

/**
 * Get a specific field error from a ZodError
 *
 * @param error - Zod error
 * @param fieldName - Field name to get error for
 * @returns Error message or undefined
 */
export function getFieldError(error: ZodError | null | undefined, fieldName: string): string | undefined {
  if (!error) return undefined

  const issue = error.issues.find(issue => {
    const path = issue.path.join('.')
    return path === fieldName
  })

  return issue ? formatZodIssue(issue) : undefined
}
