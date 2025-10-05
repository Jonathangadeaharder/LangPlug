import { z } from 'zod';
import { schemas } from '@/schemas/api-schemas';

/**
 * Schema validation utilities using auto-generated Zod schemas from OpenAPI
 *
 * IMPORTANT: These schemas are auto-generated from the backend OpenAPI spec.
 * Do NOT modify them manually. To update:
 * 1. Run: npm run update-openapi
 * 2. Or manually: cd Backend && python export_openapi.py && cd ../Frontend && npm run generate:schemas
 */

// Re-export generated schemas for convenience
export const UserResponseSchema = schemas.UserResponse;
export const BearerResponseSchema = schemas.BearerResponse;
export const ErrorModelSchema = schemas.ErrorModel;
export const HTTPValidationErrorSchema = schemas.HTTPValidationError;
export const UserCreateSchema = schemas.UserCreate;

// Create auth response schema by combining generated schemas
export const AuthResponseSchema = z.object({
  token: z.string(),
  user: UserResponseSchema,
  expires_at: z.string(),
}).passthrough();

// Create register/login request schemas with frontend-specific validation messages
export const RegisterRequestSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  email: z.string().email('Invalid email format'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

export const LoginRequestSchema = z.object({
  username: z.string().min(1, 'Email is required'),
  password: z.string().min(1, 'Password is required'),
});

// Health check response schema (not in OpenAPI spec - internal endpoint)
export const HealthCheckResponseSchema = z.object({
  status: z.string(),
  timestamp: z.string().optional(),
});

// Validation helper functions
export class SchemaValidationError extends Error {
  constructor(message: string, public issues: z.ZodIssue[]) {
    super(message);
    this.name = 'SchemaValidationError';
  }
}

export function validateApiResponse<T>(
  data: unknown,
  schema: z.ZodSchema<T>,
  context?: string
): T {
  const result = schema.safeParse(data);

  if (!result.success) {
    const errorMessage = `Schema validation failed${context ? ` for ${context}` : ''}`;
    throw new SchemaValidationError(errorMessage, result.error.issues);
  }

  return result.data;
}

export function validateUserResponse(data: unknown): z.infer<typeof UserResponseSchema> {
  return validateApiResponse(data, UserResponseSchema, 'UserResponse');
}

export function validateAuthResponse(data: unknown): z.infer<typeof AuthResponseSchema> {
  return validateApiResponse(data, AuthResponseSchema, 'AuthResponse');
}

export function validateRegisterRequest(data: unknown): z.infer<typeof RegisterRequestSchema> {
  return validateApiResponse(data, RegisterRequestSchema, 'RegisterRequest');
}

export function validateLoginRequest(data: unknown): z.infer<typeof LoginRequestSchema> {
  return validateApiResponse(data, LoginRequestSchema, 'LoginRequest');
}

export function validateBearerResponse(data: unknown): z.infer<typeof BearerResponseSchema> {
  return validateApiResponse(data, BearerResponseSchema, 'BearerResponse');
}

// Type exports for convenience
export type UserResponse = z.infer<typeof UserResponseSchema>;
export type AuthResponse = z.infer<typeof AuthResponseSchema>;
export type RegisterRequest = z.infer<typeof RegisterRequestSchema>;
export type LoginRequest = z.infer<typeof LoginRequestSchema>;
export type HealthCheckResponse = z.infer<typeof HealthCheckResponseSchema>;
export type ErrorResponse = z.infer<typeof ErrorModelSchema>;
export type BearerResponse = z.infer<typeof BearerResponseSchema>;
export type UserCreate = z.infer<typeof UserCreateSchema>;
