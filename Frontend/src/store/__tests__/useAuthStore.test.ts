import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAuthStore } from '../useAuthStore';
import * as api from '@/services/api';
import type { AuthResponse } from '@/types';

// Mock the API service
vi.mock('@/services/api');
const mockApi = vi.mocked(api);

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

describe('useAuthStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset store state
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  });

  describe('Initial State', () => {
    it('has correct initial state', () => {
      const { result } = renderHook(() => useAuthStore());
      
      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });

  describe('Login', () => {
    it('logs in user successfully', async () => {
      const mockLoginResponse = {
        token: 'jwt-token-123',
        user: {
          id: 1,
          username: 'testuser',
          is_admin: false,
          is_active: true,
          created_at: '2025-01-01T00:00:00Z',
        },
        expires_at: '2025-12-31T00:00:00Z',
      };
      
      mockApi.login.mockResolvedValue(mockLoginResponse);
      
      const { result } = renderHook(() => useAuthStore());
      
      await act(async () => {
        await result.current.login('test@example.com', 'password123');
      });
      
      expect(mockApi.login).toHaveBeenCalledWith('test@example.com', 'password123');
      expect(result.current.user).toEqual(mockLoginResponse.user);
      expect(result.current.token).toBe('jwt-token-123');
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(localStorageMock.setItem).toHaveBeenCalledWith('auth_token', 'jwt-token-123');
    });

    it('handles login error', async () => {
      const loginError = new Error('Invalid credentials');
      mockApi.login.mockRejectedValue(loginError);
      
      const { result } = renderHook(() => useAuthStore());
      
      await act(async () => {
        await result.current.login('test@example.com', 'wrongpassword');
      });
      
      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBe('Invalid credentials');
    });

    it('sets loading state during login', async () => {
      let resolveLogin: (value: AuthResponse) => void;
      const loginPromise = new Promise<AuthResponse>((resolve) => {
        resolveLogin = resolve;
      });
      
      mockApi.login.mockReturnValue(loginPromise);
      
      const { result } = renderHook(() => useAuthStore());
      
      act(() => {
        result.current.login('test@example.com', 'password123');
      });
      
      expect(result.current.isLoading).toBe(true);
      
      await act(async () => {
        resolveLogin!({
          token: 'jwt-token-123',
          user: {
            id: 1,
            username: 'testuser',
            is_admin: false,
            is_active: true,
            created_at: '2025-01-01T00:00:00Z',
          },
          expires_at: '2025-12-31T00:00:00Z',
        });
        await loginPromise;
      });
      
      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('Register', () => {
    it('registers user successfully', async () => {
      const mockRegisterResponse = {
        token: 'jwt-token-456',
        user: {
          id: 2,
          username: 'newuser',
          is_admin: false,
          is_active: true,
          created_at: '2025-01-02T00:00:00Z',
        },
        expires_at: '2026-12-31T00:00:00Z',
      };
      
      mockApi.register.mockResolvedValue(mockRegisterResponse);
      
      const { result } = renderHook(() => useAuthStore());
      
      await act(async () => {
        await result.current.register('new@example.com', 'password123', 'New User');
      });
      
      expect(mockApi.register).toHaveBeenCalledWith('new@example.com', 'password123', 'New User');
      expect(result.current.user).toEqual(mockRegisterResponse.user);
      expect(result.current.token).toBe('jwt-token-456');
      expect(result.current.isAuthenticated).toBe(true);
      expect(localStorageMock.setItem).toHaveBeenCalledWith('auth_token', 'jwt-token-456');
    });

    it('handles registration error', async () => {
      const registerError = new Error('Email already exists');
      mockApi.register.mockRejectedValue(registerError);
      
      const { result } = renderHook(() => useAuthStore());
      
      await act(async () => {
        await result.current.register('existing@example.com', 'password123', 'User');
      });
      
      expect(result.current.error).toBe('Email already exists');
      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('Logout', () => {
    it('logs out user successfully', () => {
      const { result } = renderHook(() => useAuthStore());
      
      // Set initial authenticated state
      act(() => {
        useAuthStore.setState({
          user: {
            id: 1,
            username: 'testuser',
            is_admin: false,
            is_active: true,
            created_at: '2025-01-01T00:00:00Z',
          },
          token: 'jwt-token-123',
          isAuthenticated: true,
        });
      });
      
      act(() => {
        result.current.logout();
      });
      
      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.error).toBeNull();
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth_token');
    });
  });

  describe('Token Persistence', () => {
    it('initializes from localStorage token', async () => {
      const mockProfile = {
        id: 1,
        username: 'testuser',
        is_admin: false,
        is_active: true,
        created_at: '2025-01-01T00:00:00Z',
      };
      
      localStorageMock.getItem.mockReturnValue('stored-token-123');
      mockApi.getProfile.mockResolvedValue(mockProfile);
      
      const { result } = renderHook(() => useAuthStore());
      
      await act(async () => {
        await result.current.initializeAuth();
      });
      
      expect(mockApi.getProfile).toHaveBeenCalled();
      expect(result.current.user).toEqual(mockProfile);
      expect(result.current.token).toBe('stored-token-123');
      expect(result.current.isAuthenticated).toBe(true);
    });

    it('handles invalid stored token', async () => {
      localStorageMock.getItem.mockReturnValue('invalid-token');
      mockApi.getProfile.mockRejectedValue(new Error('Unauthorized'));
      
      const { result } = renderHook(() => useAuthStore());
      
      await act(async () => {
        await result.current.initializeAuth();
      });
      
      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth_token');
    });
  });

  describe('Clear Error', () => {
    it('clears error state', () => {
      const { result } = renderHook(() => useAuthStore());
      
      // Set error state
      act(() => {
        useAuthStore.setState({ error: 'Some error' });
      });
      
      expect(result.current.error).toBe('Some error');
      
      act(() => {
        result.current.clearError();
      });
      
      expect(result.current.error).toBeNull();
    });
  });
});
