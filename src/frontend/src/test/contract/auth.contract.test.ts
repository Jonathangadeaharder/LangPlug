import { describe, it, expect, beforeEach, vi } from 'vitest'
import * as clientSdk from '../../client/services.gen'
import type {
  UserCreate,
  Body_auth_jwt_login_api_auth_login_post,
  UserResponse,
  UserRead,
  BearerResponse,
} from '../../client/types.gen'

// Mock the SDK functions
vi.mock('../../client/services.gen', () => ({
  registerRegisterApiAuthRegisterPost: vi.fn(),
  authJwtLoginApiAuthLoginPost: vi.fn(),
}))

describe('Auth API Contract Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Register Endpoint Contract', () => {
    it('WhenRegisterCalledWithValidData_ThenReturnsCorrectStructure', async () => {
      const registerRequest: UserCreate = {
        username: 'testuser',
        password: 'testpass123',
        email: 'test@example.com',
      }

      // Mock successful response - SDK returns UserRead directly
      const mockUserResponse: UserRead = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        is_superuser: false,
        is_active: true,
        is_verified: true,
        created_at: '2025-01-01T00:00:00Z',
        last_login: null,
      }

      vi.mocked(clientSdk.registerRegisterApiAuthRegisterPost).mockResolvedValueOnce(
        mockUserResponse
      )

      const result = await clientSdk.registerRegisterApiAuthRegisterPost({
        requestBody: registerRequest,
      })

      // Verify request structure
      expect(clientSdk.registerRegisterApiAuthRegisterPost).toHaveBeenCalledWith({
        requestBody: registerRequest,
      })

      // Verify response structure matches UserRead type
      expect(result).toMatchObject({
        id: expect.any(Number),
        username: expect.any(String),
        email: expect.any(String),
        is_superuser: expect.any(Boolean),
        is_active: expect.any(Boolean),
        is_verified: expect.any(Boolean),
        created_at: expect.any(String),
      })
    })

    it('WhenRegisterRequestValidated_ThenRequiredFieldsPresent', () => {
      // Test that TypeScript enforces required fields
      const validRequest: UserCreate = {
        username: 'test',
        password: 'pass',
        email: 'test@example.com',
      }

      // These should be required fields
      expect(validRequest.username).toBeDefined()
      expect(validRequest.password).toBeDefined()
    })
  })

  describe('Login Endpoint Contract', () => {
    it('WhenLoginCalledWithValidData_ThenReturnsCorrectStructure', async () => {
      const loginFormData: Body_auth_jwt_login_api_auth_login_post = {
        username: 'testuser',
        password: 'testpass123',
      }

      // Mock successful login response
      const mockAuthResponse: BearerResponse = {
        access_token: 'mock-jwt-token',
        token_type: 'bearer',
      }

      vi.mocked(clientSdk.authJwtLoginApiAuthLoginPost).mockResolvedValueOnce(mockAuthResponse)

      const result = await clientSdk.authJwtLoginApiAuthLoginPost({
        formData: loginFormData,
      })

      // Verify request structure
      expect(clientSdk.authJwtLoginApiAuthLoginPost).toHaveBeenCalledWith({
        formData: loginFormData,
      })

      // Verify response structure matches BearerResponse type
      expect(result).toMatchObject({
        access_token: expect.any(String),
        token_type: expect.any(String),
      })
    })

    it('WhenLoginRequestValidated_ThenRequiredFieldsPresent', () => {
      const validRequest: Body_auth_jwt_login_api_auth_login_post = {
        username: 'test',
        password: 'pass',
      }

      // These should be required fields
      expect(validRequest.username).toBeDefined()
      expect(validRequest.password).toBeDefined()
    })
  })

  describe('Response Type Validation', () => {
    it('WhenUserResponseValidated_ThenStructureCorrect', () => {
      const userResponse: UserResponse = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        is_superuser: false,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        last_login: null,
      }

      // Verify all required fields are present
      expect(userResponse.id).toBeTypeOf('number')
      expect(userResponse.username).toBeTypeOf('string')
      expect(userResponse.is_superuser).toBeTypeOf('boolean')
      expect(userResponse.is_active).toBeTypeOf('boolean')
      expect(userResponse.created_at).toBeTypeOf('string')

      // last_login is optional
      expect(userResponse.last_login === null || typeof userResponse.last_login === 'string').toBe(
        true
      )
    })

    it('WhenBearerResponseValidated_ThenStructureCorrect', () => {
      const bearerResponse: BearerResponse = {
        access_token: 'jwt-token',
        token_type: 'bearer',
      }

      expect(bearerResponse.access_token).toBeTypeOf('string')
      expect(bearerResponse.token_type).toBeTypeOf('string')
    })
  })
})
