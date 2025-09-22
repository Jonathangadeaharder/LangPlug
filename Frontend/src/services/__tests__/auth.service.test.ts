/**
 * Unit tests for Authentication Service
 * Following best practices: isolation, mocking, comprehensive coverage
 */

import { describe, it, expect, beforeEach, afterEach, vi, Mock } from 'vitest';
import { AuthService } from '../auth.service';
import { apiClient } from '../../client/api-client';
import { tokenStorage } from '../../utils/token-storage';

// Mock dependencies
vi.mock('../../client/api-client');
vi.mock('../../utils/token-storage');

describe('AuthService', () => {
  let authService: AuthService;
  let mockApiClient: any;
  let mockTokenStorage: any;

  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks();
    
    // Setup mock implementations
    mockApiClient = apiClient as any;
    mockTokenStorage = tokenStorage as any;
    
    // Create service instance
    authService = new AuthService();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('register', () => {
    const mockUserData = {
      username: 'testuser',
      email: 'test@example.com',
      password: 'SecurePassword123!',
    };

    it('should successfully register a new user', async () => {
      // Arrange
      const mockResponse = {
        id: '123',
        username: 'testuser',
        email: 'test@example.com',
        is_active: true,
        is_verified: false,
      };
      mockApiClient.post = vi.fn().mockResolvedValue({ data: mockResponse });

      // Act
      const result = await authService.register(mockUserData);

      // Assert
      expect(result).toEqual(mockResponse);
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/auth/register', mockUserData);
      expect(mockApiClient.post).toHaveBeenCalledTimes(1);
    });

    it('should handle registration with duplicate email', async () => {
      // Arrange
      const errorResponse = {
        response: {
          status: 400,
          data: { detail: 'User with this email already exists' },
        },
      };
      mockApiClient.post = vi.fn().mockRejectedValue(errorResponse);

      // Act & Assert
      await expect(authService.register(mockUserData)).rejects.toThrow('User with this email already exists');
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/auth/register', mockUserData);
    });

    it('should validate email format before sending request', async () => {
      // Arrange
      const invalidData = {
        ...mockUserData,
        email: 'invalid-email',
      };

      // Act & Assert
      await expect(authService.register(invalidData)).rejects.toThrow('Invalid email format');
      expect(mockApiClient.post).not.toHaveBeenCalled();
    });

    it('should validate password strength before sending request', async () => {
      // Arrange
      const weakPasswordData = {
        ...mockUserData,
        password: 'weak',
      };

      // Act & Assert
      await expect(authService.register(weakPasswordData)).rejects.toThrow('Password must be at least 8 characters');
      expect(mockApiClient.post).not.toHaveBeenCalled();
    });

    it('should handle network errors gracefully', async () => {
      // Arrange
      mockApiClient.post = vi.fn().mockRejectedValue(new Error('Network error'));

      // Act & Assert
      await expect(authService.register(mockUserData)).rejects.toThrow('Network error');
    });
  });

  describe('login', () => {
    const mockCredentials = {
      email: 'test@example.com',
      password: 'SecurePassword123!',
    };

    it('should successfully login and store token', async () => {
      // Arrange
      const mockResponse = {
        access_token: 'mock-jwt-token',
        token_type: 'bearer',
        expires_in: 3600,
      };
      mockApiClient.post = vi.fn().mockResolvedValue({ data: mockResponse });
      mockTokenStorage.setToken = vi.fn();
      mockTokenStorage.setRefreshToken = vi.fn();

      // Act
      const result = await authService.login(mockCredentials);

      // Assert
      expect(result).toEqual(mockResponse);
      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/api/auth/login',
        expect.any(URLSearchParams),
        expect.objectContaining({
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        })
      );
      expect(mockTokenStorage.setToken).toHaveBeenCalledWith('mock-jwt-token');
      expect(mockTokenStorage.setToken).toHaveBeenCalledTimes(1);
    });

    it('should handle invalid credentials', async () => {
      // Arrange
      const errorResponse = {
        response: {
          status: 400,
          data: { detail: 'Incorrect username or password' },
        },
      };
      mockApiClient.post = vi.fn().mockRejectedValue(errorResponse);

      // Act & Assert
      await expect(authService.login(mockCredentials)).rejects.toThrow('Incorrect username or password');
      expect(mockTokenStorage.setToken).not.toHaveBeenCalled();
    });

    it('should clear tokens on login failure', async () => {
      // Arrange
      mockApiClient.post = vi.fn().mockRejectedValue(new Error('Login failed'));
      mockTokenStorage.clear = vi.fn();

      // Act
      try {
        await authService.login(mockCredentials);
      } catch (error) {
        // Expected error
      }

      // Assert
      expect(mockTokenStorage.clear).toHaveBeenCalled();
    });

    it('should handle expired tokens', async () => {
      // Arrange
      const expiredTokenResponse = {
        response: {
          status: 401,
          data: { detail: 'Token has expired' },
        },
      };
      mockApiClient.post = vi.fn().mockRejectedValue(expiredTokenResponse);

      // Act & Assert
      await expect(authService.login(mockCredentials)).rejects.toThrow('Token has expired');
    });
  });

  describe('logout', () => {
    it('should successfully logout and clear tokens', async () => {
      // Arrange
      mockApiClient.post = vi.fn().mockResolvedValue({ data: {} });
      mockTokenStorage.clear = vi.fn();
      mockTokenStorage.getToken = vi.fn().mockReturnValue('mock-token');

      // Act
      await authService.logout();

      // Assert
      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/api/auth/logout',
        {},
        expect.objectContaining({
          headers: { Authorization: 'Bearer mock-token' },
        })
      );
      expect(mockTokenStorage.clear).toHaveBeenCalled();
    });

    it('should clear tokens even if logout API fails', async () => {
      // Arrange
      mockApiClient.post = vi.fn().mockRejectedValue(new Error('Logout failed'));
      mockTokenStorage.clear = vi.fn();

      // Act
      await authService.logout();

      // Assert
      expect(mockTokenStorage.clear).toHaveBeenCalled();
    });

    it('should handle logout without token', async () => {
      // Arrange
      mockTokenStorage.getToken = vi.fn().mockReturnValue(null);
      mockTokenStorage.clear = vi.fn();

      // Act
      await authService.logout();

      // Assert
      expect(mockApiClient.post).not.toHaveBeenCalled();
      expect(mockTokenStorage.clear).toHaveBeenCalled();
    });
  });

  describe('getCurrentUser', () => {
    it('should fetch and return current user data', async () => {
      // Arrange
      const mockUser = {
        id: '123',
        email: 'test@example.com',
        username: 'testuser',
        is_active: true,
      };
      mockApiClient.get = vi.fn().mockResolvedValue({ data: mockUser });
      mockTokenStorage.getToken = vi.fn().mockReturnValue('mock-token');

      // Act
      const result = await authService.getCurrentUser();

      // Assert
      expect(result).toEqual(mockUser);
      expect(mockApiClient.get).toHaveBeenCalledWith(
        '/api/auth/me',
        expect.objectContaining({
          headers: { Authorization: 'Bearer mock-token' },
        })
      );
    });

    it('should return null if no token is available', async () => {
      // Arrange
      mockTokenStorage.getToken = vi.fn().mockReturnValue(null);

      // Act
      const result = await authService.getCurrentUser();

      // Assert
      expect(result).toBeNull();
      expect(mockApiClient.get).not.toHaveBeenCalled();
    });

    it('should handle unauthorized errors', async () => {
      // Arrange
      mockTokenStorage.getToken = vi.fn().mockReturnValue('invalid-token');
      mockApiClient.get = vi.fn().mockRejectedValue({
        response: { status: 401, data: { detail: 'Invalid token' } },
      });
      mockTokenStorage.clear = vi.fn();

      // Act
      const result = await authService.getCurrentUser();

      // Assert
      expect(result).toBeNull();
      expect(mockTokenStorage.clear).toHaveBeenCalled();
    });

    it('should cache user data for performance', async () => {
      // Arrange
      const mockUser = { id: '123', email: 'test@example.com' };
      mockApiClient.get = vi.fn().mockResolvedValue({ data: mockUser });
      mockTokenStorage.getToken = vi.fn().mockReturnValue('mock-token');

      // Act
      const result1 = await authService.getCurrentUser();
      const result2 = await authService.getCurrentUser();

      // Assert
      expect(result1).toEqual(mockUser);
      expect(result2).toEqual(mockUser);
      expect(mockApiClient.get).toHaveBeenCalledTimes(1); // Should use cache for second call
    });
  });

  describe('refreshToken', () => {
    it('should successfully refresh access token', async () => {
      // Arrange
      const mockResponse = {
        access_token: 'new-token',
        token_type: 'bearer',
        expires_in: 3600,
      };
      mockTokenStorage.getRefreshToken = vi.fn().mockReturnValue('refresh-token');
      mockApiClient.post = vi.fn().mockResolvedValue({ data: mockResponse });
      mockTokenStorage.setToken = vi.fn();

      // Act
      const result = await authService.refreshToken();

      // Assert
      expect(result).toEqual(mockResponse);
      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/api/auth/refresh',
        expect.objectContaining({ refresh_token: 'refresh-token' })
      );
      expect(mockTokenStorage.setToken).toHaveBeenCalledWith('new-token');
    });

    it('should handle refresh token expiration', async () => {
      // Arrange
      mockTokenStorage.getRefreshToken = vi.fn().mockReturnValue('expired-refresh');
      mockApiClient.post = vi.fn().mockRejectedValue({
        response: { status: 401, data: { detail: 'Refresh token expired' } },
      });
      mockTokenStorage.clear = vi.fn();

      // Act & Assert
      await expect(authService.refreshToken()).rejects.toThrow('Refresh token expired');
      expect(mockTokenStorage.clear).toHaveBeenCalled();
    });

    it('should handle missing refresh token', async () => {
      // Arrange
      mockTokenStorage.getRefreshToken = vi.fn().mockReturnValue(null);

      // Act & Assert
      await expect(authService.refreshToken()).rejects.toThrow('No refresh token available');
      expect(mockApiClient.post).not.toHaveBeenCalled();
    });
  });

  describe('isAuthenticated', () => {
    it('should return true when valid token exists', () => {
      // Arrange
      mockTokenStorage.getToken = vi.fn().mockReturnValue('valid-token');
      mockTokenStorage.isTokenExpired = vi.fn().mockReturnValue(false);

      // Act
      const result = authService.isAuthenticated();

      // Assert
      expect(result).toBe(true);
    });

    it('should return false when no token exists', () => {
      // Arrange
      mockTokenStorage.getToken = vi.fn().mockReturnValue(null);

      // Act
      const result = authService.isAuthenticated();

      // Assert
      expect(result).toBe(false);
    });

    it('should return false when token is expired', () => {
      // Arrange
      mockTokenStorage.getToken = vi.fn().mockReturnValue('expired-token');
      mockTokenStorage.isTokenExpired = vi.fn().mockReturnValue(true);

      // Act
      const result = authService.isAuthenticated();

      // Assert
      expect(result).toBe(false);
    });
  });

  describe('changePassword', () => {
    it('should successfully change password', async () => {
      // Arrange
      const passwordData = {
        current_password: 'OldPassword123!',
        new_password: 'NewPassword123!',
      };
      mockTokenStorage.getToken = vi.fn().mockReturnValue('mock-token');
      mockApiClient.post = vi.fn().mockResolvedValue({ data: { success: true } });

      // Act
      const result = await authService.changePassword(
        passwordData.current_password,
        passwordData.new_password
      );

      // Assert
      expect(result).toEqual({ success: true });
      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/api/auth/change-password',
        passwordData,
        expect.objectContaining({
          headers: { Authorization: 'Bearer mock-token' },
        })
      );
    });

    it('should validate new password strength', async () => {
      // Arrange
      const weakNewPassword = 'weak';

      // Act & Assert
      await expect(
        authService.changePassword('OldPassword123!', weakNewPassword)
      ).rejects.toThrow('Password must be at least 8 characters');
      expect(mockApiClient.post).not.toHaveBeenCalled();
    });

    it('should handle incorrect current password', async () => {
      // Arrange
      mockTokenStorage.getToken = vi.fn().mockReturnValue('mock-token');
      mockApiClient.post = vi.fn().mockRejectedValue({
        response: { status: 400, data: { detail: 'Current password is incorrect' } },
      });

      // Act & Assert
      await expect(
        authService.changePassword('WrongPassword', 'NewPassword123!')
      ).rejects.toThrow('Current password is incorrect');
    });
  });

  describe('resetPassword', () => {
    it('should send password reset email', async () => {
      // Arrange
      const email = 'test@example.com';
      mockApiClient.post = vi.fn().mockResolvedValue({ data: { message: 'Email sent' } });

      // Act
      const result = await authService.requestPasswordReset(email);

      // Assert
      expect(result).toEqual({ message: 'Email sent' });
      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/api/auth/forgot-password',
        { email }
      );
    });

    it('should confirm password reset with token', async () => {
      // Arrange
      const resetData = {
        token: 'reset-token',
        new_password: 'NewPassword123!',
      };
      mockApiClient.post = vi.fn().mockResolvedValue({ data: { success: true } });

      // Act
      const result = await authService.confirmPasswordReset(
        resetData.token,
        resetData.new_password
      );

      // Assert
      expect(result).toEqual({ success: true });
      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/api/auth/reset-password',
        resetData
      );
    });

    it('should handle invalid reset token', async () => {
      // Arrange
      mockApiClient.post = vi.fn().mockRejectedValue({
        response: { status: 400, data: { detail: 'Invalid or expired token' } },
      });

      // Act & Assert
      await expect(
        authService.confirmPasswordReset('invalid-token', 'NewPassword123!')
      ).rejects.toThrow('Invalid or expired token');
    });
  });

  describe('Error Handling', () => {
    it('should handle network timeouts', async () => {
      // Arrange
      mockApiClient.post = vi.fn().mockRejectedValue(new Error('Network timeout'));

      // Act & Assert
      await expect(authService.login({ email: 'test@example.com', password: 'pass' }))
        .rejects.toThrow('Network timeout');
    });

    it('should handle server errors (5xx)', async () => {
      // Arrange
      mockApiClient.post = vi.fn().mockRejectedValue({
        response: { status: 500, data: { detail: 'Internal server error' } },
      });

      // Act & Assert
      await expect(authService.login({ email: 'test@example.com', password: 'pass' }))
        .rejects.toThrow('Internal server error');
    });

    it('should handle rate limiting', async () => {
      // Arrange
      mockApiClient.post = vi.fn().mockRejectedValue({
        response: { status: 429, data: { detail: 'Too many requests' } },
      });

      // Act & Assert
      await expect(authService.login({ email: 'test@example.com', password: 'pass' }))
        .rejects.toThrow('Too many requests');
    });
  });
});
