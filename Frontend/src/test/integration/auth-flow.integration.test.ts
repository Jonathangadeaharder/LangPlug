/**
 * Integration tests for Authentication Flow
 * Tests the complete auth flow including API interactions and state management
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from '../../store/useAuthStore';
import { AuthService } from '../../services/auth.service';
import { apiClient } from '../../client/api-client';
import { tokenStorage } from '../../utils/token-storage';
import React from 'react';

// Mock server for integration tests
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

// MSW v2 compatibility shim for legacy rest API used in these tests
const rest = {
  post: (path: string, handler: any) =>
    http.post(path, (args: any) => {
      const req = args.request;
      const ctx = {
        status: (n: number) => ({ __t: 'status', v: n }),
        json: (obj: any) => ({ __t: 'json', v: obj }),
        set: (name: string, value: string) => ({ __t: 'header', name, v: value }),
      };
      const res = (...parts: any[]) => {
        let status = 200;
        const headers: Record<string, string> = {};
        let body: any = undefined;
        for (const p of parts) {
          if (!p) continue;
          if (p.__t === 'status') status = p.v;
          else if (p.__t === 'json') body = p.v;
          else if (p.__t === 'header') headers[p.name] = p.v;
        }
        if (status === 204) return new Response(null, { status, headers });
        return HttpResponse.json(body ?? {}, { status, headers });
      };
      return handler(req, res, ctx);
    }),
  get: (path: string, handler: any) =>
    http.get(path, (args: any) => {
      const req = args.request;
      const ctx = {
        status: (n: number) => ({ __t: 'status', v: n }),
        json: (obj: any) => ({ __t: 'json', v: obj }),
        set: (name: string, value: string) => ({ __t: 'header', name, v: value }),
      };
      const res = (...parts: any[]) => {
        let status = 200;
        const headers: Record<string, string> = {};
        let body: any = undefined;
        for (const p of parts) {
          if (!p) continue;
          if (p.__t === 'status') status = p.v;
          else if (p.__t === 'json') body = p.v;
          else if (p.__t === 'header') headers[p.name] = p.v;
        }
        if (status === 204) return new Response(null, { status, headers });
        return HttpResponse.json(body ?? {}, { status, headers });
      };
      return handler(req, res, ctx);
    }),
};

// Setup MSW server for mocking API responses
const server = setupServer(
  rest.post('/api/auth/register', (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        id: '123',
        email: 'test@example.com',
        username: 'testuser',
        is_active: true,
        is_verified: false,
      })
    );
  }),
  rest.post('/api/auth/login', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        access_token: 'mock-jwt-token',
        token_type: 'bearer',
        expires_in: 3600,
      })
    );
  }),
  rest.get('/api/auth/me', (req, res, ctx) => {
    const authHeader = req.headers.get('Authorization');
    if (authHeader === 'Bearer mock-jwt-token') {
      return res(
        ctx.status(200),
        ctx.json({
          id: '123',
          email: 'test@example.com',
          username: 'testuser',
          is_active: true,
        })
      );
    }
    return res(ctx.status(401), ctx.json({ detail: 'Unauthorized' }));
  }),
  rest.post('/api/auth/logout', (req, res, ctx) => {
    return res(ctx.status(204));
  })
);

// Start server before all tests
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Authentication Flow Integration', () => {
  let queryClient: QueryClient;
  let authService: AuthService;

  beforeEach(() => {
    // Create fresh instances for each test
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    authService = new AuthService();
    
    // Clear any stored tokens
    tokenStorage.clear();
    
    // Reset auth store
    useAuthStore.getState().logout();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);

  describe('Complete Registration and Login Flow', () => {
    it('should register, login, and fetch user profile', async () => {
      // Step 1: Register new user
      const registerData = {
        username: 'testuser',
        email: 'test@example.com',
        password: 'SecurePassword123!',
      };

      const registrationResult = await authService.register(registerData);
      expect(registrationResult).toMatchObject({
        id: '123',
        email: 'test@example.com',
        username: 'testuser',
      });

      // Step 2: Login with credentials
      const loginResult = await authService.login({
        email: 'test@example.com',
        password: 'SecurePassword123!',
      });
      expect(loginResult).toMatchObject({
        access_token: 'mock-jwt-token',
        token_type: 'bearer',
      });

      // Verify token is stored
      expect(tokenStorage.getToken()).toBe('mock-jwt-token');

      // Step 3: Fetch current user
      const currentUser = await authService.getCurrentUser();
      expect(currentUser).toMatchObject({
        id: '123',
        email: 'test@example.com',
        username: 'testuser',
      });

      // Step 4: Verify auth store is updated
      const { result } = renderHook(() => useAuthStore(), { wrapper });
      
      act(() => {
        result.current.setUser(currentUser!);
        result.current.setAuthenticated(true);
      });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toMatchObject({
        email: 'test@example.com',
        username: 'testuser',
      });

      // Step 5: Logout
      await authService.logout();
      
      act(() => {
        result.current.logout();
      });

      expect(tokenStorage.getToken()).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });

    it('should handle registration errors gracefully', async () => {
      // Override handler for this test
      server.use(
        rest.post('/api/auth/register', (req, res, ctx) => {
          return res(
            ctx.status(400),
            ctx.json({ detail: 'Email already registered' })
          );
        })
      );

      const registerData = {
        username: 'existinguser',
        email: 'existing@example.com',
        password: 'SecurePassword123!',
      };

      await expect(authService.register(registerData)).rejects.toThrow(
        'Email already registered'
      );

      // Verify no token is stored
      expect(tokenStorage.getToken()).toBeNull();
    });

    it('should handle login errors and clear tokens', async () => {
      // Override handler for this test
      server.use(
        rest.post('/api/auth/login', (req, res, ctx) => {
          return res(
            ctx.status(400),
            ctx.json({ detail: 'Invalid credentials' })
          );
        })
      );

      await expect(
        authService.login({
          email: 'test@example.com',
          password: 'WrongPassword',
        })
      ).rejects.toThrow('Invalid credentials');

      // Verify tokens are cleared
      expect(tokenStorage.getToken()).toBeNull();
      
      // Verify auth store is not authenticated
      const { result } = renderHook(() => useAuthStore(), { wrapper });
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('should automatically refresh expired tokens', async () => {
      let tokenCallCount = 0;
      
      // Setup handler for token refresh
      server.use(
        rest.post('/api/auth/refresh', (req, res, ctx) => {
          tokenCallCount++;
          return res(
            ctx.status(200),
            ctx.json({
              access_token: `refreshed-token-${tokenCallCount}`,
              token_type: 'bearer',
              expires_in: 3600,
            })
          );
        }),
        rest.get('/api/auth/me', (req, res, ctx) => {
          const authHeader = req.headers.get('Authorization');
          if (authHeader?.includes('refreshed-token')) {
            return res(
              ctx.status(200),
              ctx.json({
                id: '123',
                email: 'test@example.com',
                username: 'testuser',
              })
            );
          }
          return res(
            ctx.status(401),
            ctx.json({ detail: 'Token expired' })
          );
        })
      );

      // Set expired token
      tokenStorage.setToken('expired-token');
      tokenStorage.setRefreshToken('valid-refresh-token');

      // Attempt to fetch user (should trigger refresh)
      const currentUser = await authService.getCurrentUser();
      
      // Should have refreshed token and fetched user
      expect(tokenStorage.getToken()).toContain('refreshed-token');
      expect(currentUser).toBeTruthy();
    });
  });

  describe('Protected Route Access', () => {
    it('should redirect to login when accessing protected routes without auth', async () => {
      const { result } = renderHook(() => useAuthStore(), { wrapper });
      
      // Verify not authenticated
      expect(result.current.isAuthenticated).toBe(false);
      
      // Attempt to access protected endpoint
      try {
        await apiClient.get('/api/videos');
      } catch (error: any) {
        expect(error.response?.status).toBe(401);
      }
      
      // Should trigger redirect to login (in real app)
      expect(result.current.redirectPath).toBe('/login');
    });

    it('should allow access to protected routes after login', async () => {
      // Login first
      await authService.login({
        email: 'test@example.com',
        password: 'SecurePassword123!',
      });

      // Setup protected endpoint
      server.use(
        rest.get('/api/videos', (req, res, ctx) => {
          const authHeader = req.headers.get('Authorization');
          if (authHeader === 'Bearer mock-jwt-token') {
            return res(
              ctx.status(200),
              ctx.json({ videos: [] })
            );
          }
          return res(ctx.status(401));
        })
      );

      // Access protected endpoint
      const response = await apiClient.get('/api/videos', {
        headers: { Authorization: `Bearer ${tokenStorage.getToken()}` },
      });
      
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('videos');
    });
  });

  describe('Session Management', () => {
    it('should maintain session across page refreshes', async () => {
      // Login
      await authService.login({
        email: 'test@example.com',
        password: 'SecurePassword123!',
      });

      const token = tokenStorage.getToken();
      expect(token).toBe('mock-jwt-token');

      // Simulate page refresh by creating new service instance
      const newAuthService = new AuthService();
      
      // Should still have token
      expect(tokenStorage.getToken()).toBe('mock-jwt-token');
      
      // Should be able to fetch user
      const currentUser = await newAuthService.getCurrentUser();
      expect(currentUser).toBeTruthy();
    });

    it('should handle concurrent requests with same token', async () => {
      // Login
      await authService.login({
        email: 'test@example.com',
        password: 'SecurePassword123!',
      });

      // Make concurrent requests
      const requests = Array.from({ length: 5 }, () => 
        authService.getCurrentUser()
      );
      
      const results = await Promise.all(requests);
      
      // All should succeed with same user data
      results.forEach(user => {
        expect(user).toMatchObject({
          email: 'test@example.com',
          username: 'testuser',
        });
      });
    });

    it('should handle token expiration during active session', async () => {
      // Login
      await authService.login({
        email: 'test@example.com',
        password: 'SecurePassword123!',
      });

      // Simulate token expiration
      server.use(
        rest.get('/api/auth/me', (req, res, ctx) => {
          return res(
            ctx.status(401),
            ctx.json({ detail: 'Token expired' })
          );
        })
      );

      // Should handle gracefully
      const currentUser = await authService.getCurrentUser();
      expect(currentUser).toBeNull();
      expect(tokenStorage.getToken()).toBeNull();
    });
  });

  describe('Error Recovery', () => {
    it('should recover from network errors', async () => {
      let attemptCount = 0;
      
      server.use(
        rest.post('/api/auth/login', (req, res, ctx) => {
          attemptCount++;
          if (attemptCount < 3) {
            return res.networkError('Network error');
          }
          return res(
            ctx.status(200),
            ctx.json({
              access_token: 'mock-jwt-token',
              token_type: 'bearer',
            })
          );
        })
      );

      // Should retry and eventually succeed
      const loginWithRetry = async () => {
        for (let i = 0; i < 3; i++) {
          try {
            return await authService.login({
              email: 'test@example.com',
              password: 'SecurePassword123!',
            });
          } catch (error) {
            if (i === 2) throw error;
            await new Promise(resolve => setTimeout(resolve, 100));
          }
        }
      };

      const result = await loginWithRetry();
      expect(result).toMatchObject({
        access_token: 'mock-jwt-token',
      });
    });

    it('should handle rate limiting gracefully', async () => {
      server.use(
        rest.post('/api/auth/login', (req, res, ctx) => {
          return res(
            ctx.status(429),
            ctx.json({ detail: 'Too many requests. Please try again later.' }),
            ctx.set('Retry-After', '60')
          );
        })
      );

      await expect(
        authService.login({
          email: 'test@example.com',
          password: 'SecurePassword123!',
        })
      ).rejects.toThrow('Too many requests');
      
      // Should not store any tokens
      expect(tokenStorage.getToken()).toBeNull();
    });
  });

  describe('State Synchronization', () => {
    it('should sync auth state across multiple components', async () => {
      // Create multiple hook instances (simulating multiple components)
      const { result: result1 } = renderHook(() => useAuthStore(), { wrapper });
      const { result: result2 } = renderHook(() => useAuthStore(), { wrapper });
      
      // Login and update state in first component
      await authService.login({
        email: 'test@example.com',
        password: 'SecurePassword123!',
      });
      
      const user = await authService.getCurrentUser();
      
      act(() => {
        result1.current.setUser(user!);
        result1.current.setAuthenticated(true);
      });
      
      // State should be synced in second component
      expect(result2.current.isAuthenticated).toBe(true);
      expect(result2.current.user).toEqual(user);
      
      // Logout from second component
      act(() => {
        result2.current.logout();
      });
      
      // Should be reflected in first component
      expect(result1.current.isAuthenticated).toBe(false);
      expect(result1.current.user).toBeNull();
    });
  });
});
