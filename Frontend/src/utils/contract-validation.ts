import { z } from 'zod'
import { logger } from '@/services/logger'

// Base API response schema
const BaseResponseSchema = z.object({
  status: z.string().optional(),
  timestamp: z.string().optional(),
  version: z.string().optional(),
})

// Health check response schema
export const HealthCheckResponseSchema = BaseResponseSchema.extend({
  status: z.literal('healthy'),
  timestamp: z.string(),
  version: z.string(),
  debug: z.boolean(),
})

// User schemas
export const UserSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  username: z.string().min(1),
  is_active: z.boolean(),
  is_superuser: z.boolean(),
  is_verified: z.boolean(),
})

export const CreateUserSchema = z.object({
  email: z.string().email(),
  username: z.string().min(1),
  password: z.string().min(6),
})

export const LoginRequestSchema = z.object({
  username: z.string().min(1),
  password: z.string().min(1),
})

export const AuthResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.literal('bearer'),
  user: UserSchema,
})

// Profile schemas
export const ProfileLanguageSchema = z.object({
  code: z.string(),
  name: z.string(),
  flag: z.string(),
})

export const LanguageRuntimeSchema = z.object({
  native: z.string(),
  target: z.string(),
  translation_service: z.string(),
  translation_model: z.string(),
  translation_fallback_service: z.string(),
  translation_fallback_model: z.string(),
  transcription_service: z.string(),
  spacy_models: z.object({
    target: z.string(),
    native: z.string(),
  }),
})

export const ProfileResponseSchema = z.object({
  id: z.string().uuid(),
  username: z.string(),
  is_admin: z.boolean(),
  created_at: z.string().nullable(),
  last_login: z.string().nullable(),
  native_language: ProfileLanguageSchema,
  target_language: ProfileLanguageSchema,
  language_runtime: LanguageRuntimeSchema,
})

export const LanguagePreferencesRequestSchema = z.object({
  native_language: z.string(),
  target_language: z.string(),
})

export const LanguagePreferencesResponseSchema = z.object({
  success: z.boolean(),
  message: z.string(),
  native_language: ProfileLanguageSchema,
  target_language: ProfileLanguageSchema,
  language_runtime: LanguageRuntimeSchema,
})

// Video schemas
export const VideoSchema = z.object({
  id: z.string().uuid(),
  title: z.string(),
  description: z.string().optional(),
  file_path: z.string(),
  duration: z.number().optional(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
})

export const VideoListResponseSchema = z.object({
  videos: z.array(VideoSchema),
  total: z.number(),
  page: z.number(),
  limit: z.number(),
})

// Processing schemas
export const ProcessingStatusSchema = z.object({
  task_id: z.string(),
  status: z.enum(['pending', 'processing', 'completed', 'failed']),
  progress: z.number().min(0).max(100),
  current_step: z.string().optional(),
  message: z.string().optional(),
  started_at: z.string().datetime().optional(),
  completed_at: z.string().datetime().optional(),
  error: z.string().optional(),
})

// Vocabulary schemas
export const VocabularyItemSchema = z.object({
  id: z.string().uuid(),
  german_word: z.string(),
  english_translation: z.string(),
  context: z.string().optional(),
  difficulty: z.enum(['A1', 'A2', 'B1', 'B2', 'C1', 'C2']),
  frequency: z.number().optional(),
  learned: z.boolean().default(false),
})

export const VocabularyResponseSchema = z.object({
  vocabulary: z.array(VocabularyItemSchema),
  total: z.number(),
  learned_count: z.number(),
  total_count: z.number(),
})

// Game schemas
export const GameQuestionSchema = z.object({
  id: z.string(),
  question: z.string(),
  options: z.array(z.string()),
  correct_answer: z.string(),
  difficulty: z.enum(['A1', 'A2', 'B1', 'B2', 'C1', 'C2']),
})

export const GameSessionSchema = z.object({
  session_id: z.string(),
  questions: z.array(GameQuestionSchema),
  current_question: z.number(),
  score: z.number(),
  total_questions: z.number(),
})

// Error response schema
export const ErrorResponseSchema = z.object({
  detail: z.union([
    z.string(),
    z.array(z.object({
      loc: z.array(z.union([z.string(), z.number()])),
      msg: z.string(),
      type: z.string(),
    }))
  ]),
  path: z.string().optional(),
  method: z.string().optional(),
  errors: z.array(z.any()).optional(),
})

// Contract validation error
export class ContractValidationError extends Error {
  constructor(
    message: string,
    public endpoint: string,
    public validationErrors?: z.ZodError
  ) {
    super(message)
    this.name = 'ContractValidationError'
  }
}

// Validation helper functions
export function validateApiResponse<T>(
  data: unknown,
  schema: z.ZodSchema<T>,
  endpoint: string
): T {
  try {
    return schema.parse(data)
  } catch (error) {
    if (error instanceof z.ZodError) {
      logger.error('API response validation failed', `${endpoint}: ${error.issues.map(i => i.message).join(', ')}`)
      throw new ContractValidationError(
        `Invalid API response from ${endpoint}`,
        endpoint,
        error
      )
    }
    throw error
  }
}

export function validateApiRequest<T>(
  data: unknown,
  schema: z.ZodSchema<T>,
  endpoint: string
): T {
  try {
    return schema.parse(data)
  } catch (error) {
    if (error instanceof z.ZodError) {
      logger.error('API request validation failed', `${endpoint}: ${error.issues.map(i => i.message).join(', ')}`)
      throw new ContractValidationError(
        `Invalid API request to ${endpoint}`,
        endpoint,
        error
      )
    }
    throw error
  }
}

// Type exports for use in components
export type HealthCheckResponse = z.infer<typeof HealthCheckResponseSchema>
export type User = z.infer<typeof UserSchema>
export type CreateUserRequest = z.infer<typeof CreateUserSchema>
export type LoginRequest = z.infer<typeof LoginRequestSchema>
export type AuthResponse = z.infer<typeof AuthResponseSchema>
export type ProfileResponse = z.infer<typeof ProfileResponseSchema>
export type ProfileLanguage = z.infer<typeof ProfileLanguageSchema>
export type LanguageRuntime = z.infer<typeof LanguageRuntimeSchema>
export type LanguagePreferencesRequest = z.infer<typeof LanguagePreferencesRequestSchema>
export type LanguagePreferencesResponse = z.infer<typeof LanguagePreferencesResponseSchema>
export type Video = z.infer<typeof VideoSchema>
export type VideoListResponse = z.infer<typeof VideoListResponseSchema>
export type ProcessingStatus = z.infer<typeof ProcessingStatusSchema>
export type VocabularyItem = z.infer<typeof VocabularyItemSchema>
export type VocabularyResponse = z.infer<typeof VocabularyResponseSchema>
export type GameQuestion = z.infer<typeof GameQuestionSchema>
export type GameSession = z.infer<typeof GameSessionSchema>
export type ErrorResponse = z.infer<typeof ErrorResponseSchema>
