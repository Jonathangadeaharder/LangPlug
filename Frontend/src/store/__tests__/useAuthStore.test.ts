import { renderHook, act } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useAuthStore } from '../useAuthStore'
import * as sdk from '@/client/services.gen'

vi.mock('@/services/api', () => ({}))

vi.mock('@/client/services.gen', () => ({
  authGetCurrentUserApiAuthMeGet: vi.fn(),
  authJwtBearerLoginApiAuthLoginPost: vi.fn(),
  authJwtBearerLogoutApiAuthLogoutPost: vi.fn(),
  registerRegisterApiAuthRegisterPost: vi.fn(),
}))

const sdkMock = vi.mocked(sdk)

const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

const sampleUser = {
  id: '11111111-1111-1111-1111-111111111111',
  username: 'demo',
  email: 'demo@example.com',
  is_active: true,
  is_superuser: false,
  is_verified: true,
  created_at: '2025-01-01T00:00:00Z',
  last_login: null,
}

describe('useAuthStore', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorageMock.getItem.mockReturnValue(null)
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      redirectPath: null,
    })
  })

  it('logs in and loads profile', async () => {
    sdkMock.authJwtBearerLoginApiAuthLoginPost.mockResolvedValue({
      access_token: 'jwt-token',
      token_type: 'bearer',
    })
    sdkMock.authGetCurrentUserApiAuthMeGet.mockResolvedValue(sampleUser)

    const { result } = renderHook(() => useAuthStore())

    await act(async () => {
      await result.current.login('demo@example.com', 'password123')
    })

    expect(sdkMock.authJwtBearerLoginApiAuthLoginPost).toHaveBeenCalledWith({
      formData: { username: 'demo@example.com', password: 'password123' },
    })
    expect(sdkMock.authGetCurrentUserApiAuthMeGet).toHaveBeenCalled()
    expect(result.current.user?.email).toBe('demo@example.com')
    expect(result.current.token).toBe('jwt-token')
    expect(result.current.isAuthenticated).toBe(true)
    expect(localStorageMock.setItem).toHaveBeenCalledWith('authToken', 'jwt-token')
  })

  it('captures login errors', async () => {
    sdkMock.authJwtBearerLoginApiAuthLoginPost.mockRejectedValue(new Error('Invalid credentials'))

    const { result } = renderHook(() => useAuthStore())

    await act(async () => {
      try {
        await result.current.login('demo@example.com', 'badpass')
      } catch (error) {
        // Expected to throw
      }
    })

    expect(result.current.error).toBe('Invalid credentials')
    expect(result.current.isAuthenticated).toBe(false)
  })

  it('registers then logs in', async () => {
    sdkMock.registerRegisterApiAuthRegisterPost.mockResolvedValue(sampleUser)
    sdkMock.authJwtBearerLoginApiAuthLoginPost.mockResolvedValue({
      access_token: 'jwt-token',
      token_type: 'bearer',
    })
    sdkMock.authGetCurrentUserApiAuthMeGet.mockResolvedValue(sampleUser)

    const { result } = renderHook(() => useAuthStore())

    await act(async () => {
      await result.current.register('new@example.com', 'password123', 'New User')
    })

    expect(sdkMock.registerRegisterApiAuthRegisterPost).toHaveBeenCalledWith({
      requestBody: {
        email: 'new@example.com',
        password: 'password123',
        username: 'New User',
      },
    })
    expect(result.current.isAuthenticated).toBe(true)
  })

  it('logs out user', async () => {
    sdkMock.authJwtBearerLogoutApiAuthLogoutPost.mockResolvedValue(undefined)

    const { result } = renderHook(() => useAuthStore())

    act(() => {
      useAuthStore.setState({
        user: { ...sampleUser, name: sampleUser.username },
        token: 'jwt-token',
        isAuthenticated: true,
      })
    })

    await act(async () => {
      await result.current.logout()
    })

    expect(sdkMock.authJwtBearerLogoutApiAuthLogoutPost).toHaveBeenCalled()
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('authToken')
    expect(result.current.isAuthenticated).toBe(false)
  })

  it('initializes session when token is stored', async () => {
    localStorageMock.getItem.mockReturnValue('jwt-token')
    sdkMock.authGetCurrentUserApiAuthMeGet.mockResolvedValue(sampleUser)

    const { result } = renderHook(() => useAuthStore())

    await act(async () => {
      await result.current.initializeAuth()
    })

    expect(sdkMock.authGetCurrentUserApiAuthMeGet).toHaveBeenCalled()
    expect(result.current.user?.email).toBe('demo@example.com')
    expect(result.current.isAuthenticated).toBe(true)
  })

  it('clears invalid stored sessions', async () => {
    localStorageMock.getItem.mockReturnValue('stale-token')
    sdkMock.authGetCurrentUserApiAuthMeGet.mockRejectedValue(new Error('Session expired'))

    const { result } = renderHook(() => useAuthStore())

    await act(async () => {
      await result.current.initializeAuth()
    })

    expect(localStorageMock.removeItem).toHaveBeenCalledWith('authToken')
    expect(result.current.isAuthenticated).toBe(false)
  })
})
