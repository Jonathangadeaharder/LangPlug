import { z } from 'zod';

// Zod schemas for runtime validation of API responses
export const UserResponseSchema = z.object({
  id: z.number(),
  username: z.string(),
  is_admin: z.boolean(),
  is_active: z.boolean(),
  created_at: z.string(),
  last_login: z.string().nullable().optional(),
}).passthrough();

export const AuthResponseSchema = z.object({
  token: z.string(),
  user: UserResponseSchema,
  expires_at: z.string(),
}).passthrough();

export const RegisterRequestSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

export const LoginRequestSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
});

// Health check response schema
export const HealthCheckResponseSchema = z.object({
  status: z.string(),
  timestamp: z.string().optional(),
});

// Error response schema
export const ErrorResponseSchema = z.object({
  detail: z.union([
    z.string(),
    z.array(z.object({
      loc: z.array(z.union([z.string(), z.number()])),
      msg: z.string(),
      type: z.string(),
    })),
  ]),
}).passthrough();

// Generic API response wrapper
export const ApiResponseSchema = <T extends z.ZodTypeAny>(dataSchema: T) =>
  z.object({
    data: dataSchema,
    response: z.object({
      status: z.number(),
      statusText: z.string().optional(),
    }),
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

// Type exports for convenience
export type UserResponse = z.infer<typeof UserResponseSchema>;
export type AuthResponse = z.infer<typeof AuthResponseSchema>;
export type RegisterRequest = z.infer<typeof RegisterRequestSchema>;
export type LoginRequest = z.infer<typeof LoginRequestSchema>;
export type HealthCheckResponse = z.infer<typeof HealthCheckResponseSchema>;
export type ErrorResponse = z.infer<typeof ErrorResponseSchema>;
