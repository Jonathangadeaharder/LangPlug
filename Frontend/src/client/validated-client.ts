import * as sdk from './sdk.gen'
import {
  validateRegisterRequest,
  validateLoginRequest,
  validateAuthResponse,
  validateUserResponse,
  HealthCheckResponseSchema,
  validateApiResponse,
  SchemaValidationError
} from '@/utils/schema-validation'

// Custom error types expected by tests
export class ApiValidationError extends Error {
  constructor(
    message: string,
    public endpoint: string,
    public validationErrors?: any
  ) {
    super(message)
    this.name = 'ApiValidationError'
  }
}

export class ApiRequestError extends Error {
  constructor(
    message: string,
    public endpoint: string,
    public statusCode?: number,
    public response?: unknown
  ) {
    super(message)
    this.name = 'ApiRequestError'
  }
}

export class ValidatedApiClient {
  static async register(params: { username: string; password: string }) {
    try {
      // validate request
      validateRegisterRequest(params)

      const resp = await (sdk as any).registerApiAuthRegisterPost({
        body: { username: params.username, password: params.password }
      } as any)

      // validate response data
      validateUserResponse(resp.data)
      return resp
    } catch (err: any) {
      if (err instanceof SchemaValidationError) {
        throw new ApiValidationError('Registration validation failed', '/auth/register', err.issues)
      }
      // wrap network/http errors
      const status = err?.response?.status
      throw new ApiRequestError(err?.message || 'Request failed', '/auth/register', status, err?.response?.data)
    }
  }

  static async login(params: { username: string; password: string }) {
    try {
      // validate request
      validateLoginRequest(params)

      const resp = await (sdk as any).loginApiAuthLoginPost({
        body: { username: params.username, password: params.password }
      } as any)

      // validate response data
      validateAuthResponse(resp.data)
      return resp
    } catch (err: any) {
      if (err instanceof SchemaValidationError) {
        throw new ApiValidationError('Login validation failed', '/auth/login', err.issues)
      }
      const status = err?.response?.status
      throw new ApiRequestError(err?.message || 'Request failed', '/auth/login', status, err?.response?.data)
    }
  }

  static async healthCheck() {
    try {
      const resp = await (sdk as any).healthCheckHealthGet({} as any)
      // validate response data
      validateApiResponse(resp.data, HealthCheckResponseSchema, 'HealthCheck')
      return resp
    } catch (err: any) {
      if (err instanceof SchemaValidationError) {
        throw new ApiValidationError('Health check validation failed', '/health', err.issues)
      }
      const status = err?.response?.status
      throw new ApiRequestError(err?.message || 'Request failed', '/health', status, err?.response?.data)
    }
  }
}

// Structured API client object expected by tests
export const apiClient = {
  auth: {
    register: ValidatedApiClient.register,
    login: ValidatedApiClient.login,
  },
  health: {
    check: ValidatedApiClient.healthCheck,
  },
}
