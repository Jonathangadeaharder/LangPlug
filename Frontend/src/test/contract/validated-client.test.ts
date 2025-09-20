import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ValidatedApiClient, ApiValidationError, ApiRequestError } from '../../client/validated-client';
import * as sdkGen from '../../client/sdk.gen';
import { SchemaValidationError } from '../../utils/schema-validation';

// Mock the SDK functions
vi.mock('../../client/sdk.gen', () => ({
  registerApiAuthRegisterPost: vi.fn(),
  loginApiAuthLoginPost: vi.fn(),
  healthCheckHealthGet: vi.fn(),
}));

describe('ValidatedApiClient Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Register Method', () => {
    it('should validate request and response successfully', async () => {
      const mockResponse = {
        data: {
          id: 1,
          username: 'testuser',
          is_admin: false,
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          last_login: null,
        },
        request: new Request('http://test.com'),
        response: new Response('', { status: 200 }),
      };

      vi.mocked(sdkGen.registerApiAuthRegisterPost).mockResolvedValue(mockResponse);

      const result = await ValidatedApiClient.register({
        username: 'testuser',
        password: 'password123',
      });

      expect(sdkGen.registerApiAuthRegisterPost).toHaveBeenCalledWith({
        body: {
          username: 'testuser',
          password: 'password123',
        },
      });

      expect(result.data).toEqual(mockResponse.data);
      expect(result.response.status).toBe(200);
    });

    it('should reject invalid request data', async () => {
      await expect(
        ValidatedApiClient.register({
          username: '', // invalid - empty
          password: '123', // invalid - too short
        })
      ).rejects.toThrow();

      expect(sdkGen.registerApiAuthRegisterPost).not.toHaveBeenCalled();
    });

    it('should handle invalid response data', async () => {
      const mockInvalidResponse = {
        data: {
          id: 'not-a-number', // invalid type
          username: 'testuser',
          is_admin: false,
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          // missing required fields
        } as any,
        request: new Request('http://test.com'),
        response: new Response('', { status: 200 }),
      };

      vi.mocked(sdkGen.registerApiAuthRegisterPost).mockResolvedValue(mockInvalidResponse);

      await expect(
        ValidatedApiClient.register({
          username: 'testuser',
          password: 'password123',
        })
      ).rejects.toThrow('Registration validation failed');
    });
  });

  describe('Login Method', () => {
    it('should validate request and response successfully', async () => {
      const mockResponse = {
        data: {
          token: 'jwt-token',
          user: {
            id: 1,
            username: 'testuser',
            is_admin: false,
            is_active: true,
            created_at: '2024-01-01T00:00:00Z',
            last_login: '2024-01-01T12:00:00Z',
          },
          expires_at: '2024-01-02T00:00:00Z',
        },
        request: new Request('http://test.com'),
        response: new Response('', { status: 200 }),
      };

      vi.mocked(sdkGen.loginApiAuthLoginPost).mockResolvedValue(mockResponse);

      const result = await ValidatedApiClient.login({
        username: 'testuser',
        password: 'password123',
      });

      expect(sdkGen.loginApiAuthLoginPost).toHaveBeenCalledWith({
        body: {
          username: 'testuser',
          password: 'password123',
        },
      });

      expect(result.data).toEqual(mockResponse.data);
      expect(result.response.status).toBe(200);
    });

    it('should reject invalid login request', async () => {
      await expect(
        ValidatedApiClient.login({
          username: '', // invalid - empty
          password: '', // invalid - empty
        })
      ).rejects.toThrow();

      expect(sdkGen.loginApiAuthLoginPost).not.toHaveBeenCalled();
    });

    it('should handle invalid login response', async () => {
      const mockInvalidResponse = {
        data: {
          token: 'jwt-token',
          user: {
            id: 1,
            username: 'testuser',
            is_admin: false,
            is_active: true,
            created_at: '2024-01-01T00:00:00Z',
            // missing required user fields
          },
          // missing expires_at
        } as any,
        request: new Request('http://test.com'),
        response: new Response('', { status: 200 }),
      };

      vi.mocked(sdkGen.loginApiAuthLoginPost).mockResolvedValue(mockInvalidResponse);

      await expect(
        ValidatedApiClient.login({
          username: 'testuser',
          password: 'password123',
        })
      ).rejects.toThrow('Login validation failed');
    });
  });

  describe('Health Check Method', () => {
    it('should validate health check response successfully', async () => {
      const mockResponse = {
        data: {
          status: 'healthy',
          timestamp: '2024-01-01T00:00:00Z',
        },
        request: new Request('http://test.com'),
        response: new Response('', { status: 200 }),
      };

      vi.mocked(sdkGen.healthCheckHealthGet).mockResolvedValue(mockResponse);

      const result = await ValidatedApiClient.healthCheck();

      expect(sdkGen.healthCheckHealthGet).toHaveBeenCalled();
      expect(result.data).toEqual(mockResponse.data);
    });

    it('should handle invalid health check response', async () => {
      const mockInvalidResponse = {
        data: {
          // missing status field
          timestamp: '2024-01-01T00:00:00Z',
        } as any,
        request: new Request('http://test.com'),
        response: new Response('', { status: 200 }),
      };

      vi.mocked(sdkGen.healthCheckHealthGet).mockResolvedValue(mockInvalidResponse);

      await expect(
        ValidatedApiClient.healthCheck()
      ).rejects.toThrow();
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      const networkError = new Error('Network error');
      vi.mocked(sdkGen.registerApiAuthRegisterPost).mockRejectedValue(networkError);

      await expect(
        ValidatedApiClient.register({
          username: 'testuser',
          password: 'password123',
        })
      ).rejects.toThrow('Network error');
    });

    it('should handle HTTP errors', async () => {
      const httpError = {
        response: {
          status: 400,
          data: { detail: 'Bad request' },
        },
      };
      vi.mocked(sdkGen.loginApiAuthLoginPost).mockRejectedValue(httpError);

      await expect(
        ValidatedApiClient.login({
          username: 'testuser',
          password: 'password123',
        })
      ).rejects.toThrow();
    });
  });

  describe('API Client Object', () => {
    it('should provide structured API access', async () => {
      const { apiClient } = await import('../../client/validated-client');
      
      expect(apiClient.auth.register).toBe(ValidatedApiClient.register);
      expect(apiClient.auth.login).toBe(ValidatedApiClient.login);
      expect(apiClient.health.check).toBe(ValidatedApiClient.healthCheck);
    });
  });

  describe('Custom Error Types', () => {
    it('should create ApiValidationError correctly', () => {
      const error = new ApiValidationError(
        'Validation failed',
        '/auth/login',
        [{ path: ['username'], message: 'Required' }]
      );

      expect(error.name).toBe('ApiValidationError');
      expect(error.message).toBe('Validation failed');
      expect(error.endpoint).toBe('/auth/login');
      expect(error.validationErrors).toHaveLength(1);
    });

    it('should create ApiRequestError correctly', () => {
      const error = new ApiRequestError(
        'Request failed',
        '/auth/register',
        400,
        { detail: 'Bad request' }
      );

      expect(error.name).toBe('ApiRequestError');
      expect(error.message).toBe('Request failed');
      expect(error.endpoint).toBe('/auth/register');
      expect(error.statusCode).toBe(400);
      expect(error.response).toEqual({ detail: 'Bad request' });
    });
  });
});