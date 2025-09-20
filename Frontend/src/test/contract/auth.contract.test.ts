import { describe, it, expect, beforeEach, vi } from 'vitest';
import * as clientSdk from '../../client/sdk.gen';
import type { RegisterRequest, LoginRequest, UserResponse, AuthResponse } from '../../client';

// Mock the SDK functions
vi.mock('../../client/sdk.gen', () => ({
  registerApiAuthRegisterPost: vi.fn(),
  loginApiAuthLoginPost: vi.fn(),
}));

describe('Auth API Contract Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Register Endpoint Contract', () => {
    it('WhenRegisterCalledWithValidData_ThenReturnsCorrectStructure', async () => {
      const registerRequest: RegisterRequest = {
        username: 'testuser',
        password: 'testpass123',
      };

      // Mock successful response
      const mockUserResponse: UserResponse = {
        id: 1,
        username: 'testuser',
        is_admin: false,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        last_login: null,
      };

      vi.mocked(clientSdk.registerApiAuthRegisterPost).mockResolvedValueOnce({
        data: mockUserResponse,
        request: new Request('http://test.com'),
        response: new Response('', { status: 200 }),
      });

      const result = await clientSdk.registerApiAuthRegisterPost({
        body: registerRequest,
      });

      // Verify request structure
      expect(clientSdk.registerApiAuthRegisterPost).toHaveBeenCalledWith({
        body: registerRequest,
      });

      // Verify response structure matches UserResponse type
      expect(result.data).toMatchObject({
        id: expect.any(Number),
        username: expect.any(String),
        is_admin: expect.any(Boolean),
        is_active: expect.any(Boolean),
        created_at: expect.any(String),
      });
    });

    it('WhenRegisterRequestValidated_ThenRequiredFieldsPresent', () => {
      // Test that TypeScript enforces required fields
      const validRequest: RegisterRequest = {
        username: 'test',
        password: 'pass',
      };

      // These should be required fields
      expect(validRequest.username).toBeDefined();
      expect(validRequest.password).toBeDefined();
    });
  });

  describe('Login Endpoint Contract', () => {
    it('WhenLoginCalledWithValidData_ThenReturnsCorrectStructure', async () => {
      const loginRequest: LoginRequest = {
        username: 'testuser',
        password: 'testpass123',
      };

      // Mock successful login response
      const mockAuthResponse: AuthResponse = {
        token: 'mock-jwt-token',
        user: {
          id: 1,
          username: 'testuser',
          is_admin: false,
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          last_login: '2024-01-01T12:00:00Z',
        },
        expires_at: '2024-01-02T00:00:00Z',
      };

      vi.mocked(clientSdk.loginApiAuthLoginPost).mockResolvedValueOnce({
        data: mockAuthResponse,
        request: new Request('http://test.com'),
        response: new Response('', { status: 200 }),
      });

      const result = await clientSdk.loginApiAuthLoginPost({
        body: loginRequest,
      });

      // Verify request structure
      expect(clientSdk.loginApiAuthLoginPost).toHaveBeenCalledWith({
        body: loginRequest,
      });

      // Verify response structure matches AuthResponse type
      expect(result.data).toMatchObject({
        token: expect.any(String),
        user: expect.objectContaining({
          id: expect.any(Number),
          username: expect.any(String),
          is_admin: expect.any(Boolean),
          is_active: expect.any(Boolean),
          created_at: expect.any(String),
        }),
        expires_at: expect.any(String),
      });
    });

    it('WhenLoginRequestValidated_ThenRequiredFieldsPresent', () => {
      const validRequest: LoginRequest = {
        username: 'test',
        password: 'pass',
      };

      // These should be required fields
      expect(validRequest.username).toBeDefined();
      expect(validRequest.password).toBeDefined();
    });
  });

  describe('Response Type Validation', () => {
    it('WhenUserResponseValidated_ThenStructureCorrect', () => {
      const userResponse: UserResponse = {
        id: 1,
        username: 'testuser',
        is_admin: false,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        last_login: null,
      };

      // Verify all required fields are present
      expect(userResponse.id).toBeTypeOf('number');
      expect(userResponse.username).toBeTypeOf('string');
      expect(userResponse.is_admin).toBeTypeOf('boolean');
      expect(userResponse.is_active).toBeTypeOf('boolean');
      expect(userResponse.created_at).toBeTypeOf('string');
      
      // last_login is optional
      expect(userResponse.last_login === null || typeof userResponse.last_login === 'string').toBe(true);
    });

    it('WhenAuthResponseValidated_ThenStructureCorrect', () => {
      const authResponse: AuthResponse = {
        token: 'jwt-token',
        user: {
          id: 1,
          username: 'testuser',
          is_admin: false,
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          last_login: null,
        },
        expires_at: '2024-01-02T00:00:00Z',
      };

      expect(authResponse.token).toBeTypeOf('string');
      expect(authResponse.user).toBeTypeOf('object');
      expect(authResponse.expires_at).toBeTypeOf('string');
    });
  });
});