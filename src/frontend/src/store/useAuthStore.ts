import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import '@/services/api'
import { ApiError } from '@/client/core/ApiError'
import {
  authGetCurrentUserApiAuthMeGet,
  authJwtLoginApiAuthLoginPost,
  authJwtLogoutApiAuthLogoutPost,
  registerRegisterApiAuthRegisterPost,
} from '@/client/services.gen'
import type { BearerResponse, UserRead, UserResponse } from '@/client/types.gen'
import type { AuthResponse, User } from '@/types'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  redirectPath?: string | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name?: string) => Promise<void>
  logout: () => Promise<void>
  initializeAuth: () => Promise<void>
  checkAuth: () => Promise<void>
  clearError: () => void
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
  setAuthenticated: (val: boolean) => void
  setRedirectPath: (path: string | null) => void
  reset: () => void
}

const mapUser = (user: UserRead | UserResponse): User =>
  ({
    ...user,
    name: user.username,
    is_verified: 'is_verified' in user ? user.is_verified : false,
  }) as User

/**
 * Strip Pydantic's "Value error, " prefix from validation messages
 */
const cleanValidationMessage = (msg: string): string => {
  if (msg.startsWith('Value error, ')) {
    return msg.slice('Value error, '.length)
  }
  return msg
}

const extractErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof ApiError) {
    const body = error.body as {
      detail?: string | Array<{ msg?: string }>
      error?: { details?: Array<{ msg?: string }> }
    }
    
    // Handle LangPlug custom error format: { error: { details: [...] } }
    if (body?.error?.details && Array.isArray(body.error.details)) {
      const messages = body.error.details
        .map(item => item.msg ? cleanValidationMessage(item.msg) : null)
        .filter(Boolean)
      if (messages.length > 0) return messages.join('; ')
    }
    
    // Handle standard FastAPI format: { detail: [...] } or { detail: "string" }
    if (body?.detail) {
      if (Array.isArray(body.detail)) {
        const messages = body.detail
          .map(item => item.msg ? cleanValidationMessage(item.msg) : null)
          .filter(Boolean)
        if (messages.length > 0) return messages.join('; ')
      }
      if (typeof body.detail === 'string') {
        return cleanValidationMessage(body.detail)
      }
    }
    
    if (error.statusText) return error.statusText
  }

  if (typeof error === 'object' && error !== null) {
    const errObj = error as {
      message?: string
      response?: { status?: number; data?: { detail?: string } | unknown }
    }
    const detail = (errObj.response?.data as { detail?: string })?.detail
    if (detail) return detail
    if (errObj.message) return errObj.message
  }

  if (error instanceof Error && error.message) {
    return error.message
  }

  return fallback
}

const authenticate = async (email: string, password: string): Promise<AuthResponse> => {
  try {
    const bearer = (await authJwtLoginApiAuthLoginPost({
      formData: { username: email, password },
    })) as BearerResponse

    const token = bearer.access_token
    if (!token) {
      throw new Error('No access token received from server')
    }

    localStorage.setItem('authToken', token)

    const userRead = await authGetCurrentUserApiAuthMeGet()
    return {
      token,
      user: mapUser(userRead),
      expires_at: '',
    }
  } catch (error) {
    localStorage.removeItem('authToken')
    throw error
  }
}

// Export this reference so we can call it from outside React components
let clearAuthStateRef: (() => void) | null = null

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      redirectPath: null,

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          const response = await authenticate(email, password)
          set({
            user: response.user,
            token: response.token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
        } catch (error) {
          const errorMessage = extractErrorMessage(error, 'Login failed')
          set({
            isLoading: false,
            error: errorMessage,
          })
          throw error // Re-throw to let the component handle it
        }
      },

      register: async (email: string, password: string, name?: string) => {
        set({ isLoading: true, error: null })
        try {
          await registerRegisterApiAuthRegisterPost({
            requestBody: {
              email,
              password,
              username: name ?? email,
            },
          })

          const response = await authenticate(email, password)
          set({
            user: response.user,
            token: response.token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
        } catch (error) {
          const errorMessage = extractErrorMessage(error, 'Registration failed')
          set({
            isLoading: false,
            error: errorMessage,
          })
          throw error // Re-throw to let the component handle it
        }
      },

      logout: async () => {
        localStorage.removeItem('authToken')
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
          redirectPath: '/login',
        })
        try {
          await authJwtLogoutApiAuthLogoutPost()
        } catch {
          // ignore
        }
      },

      initializeAuth: async () => {
        const storedToken = localStorage.getItem('authToken')
        if (!storedToken) {
          // No token, ensure state is clean
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          })
          return
        }

        set({ isLoading: true })
        try {
          const userRead = await authGetCurrentUserApiAuthMeGet()
          set({
            user: mapUser(userRead),
            token: storedToken,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
        } catch (error) {
          // Auth failed - clear all tokens and state
          localStorage.removeItem('authToken')
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
            error: extractErrorMessage(error, 'Session expired'),
          })
        }
      },

      checkAuth: async () => {
        await get().initializeAuth()
      },

      clearError: () => {
        set({ error: null })
      },

      setUser: (user: User | null) => set({ user }),
      setToken: (token: string | null) => set({ token }),
      setAuthenticated: (val: boolean) => set({ isAuthenticated: val }),
      setRedirectPath: (path: string | null) => set({ redirectPath: path }),

      reset: () => {
        localStorage.removeItem('authToken')
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
          redirectPath: null,
        })
      },
    }),
    {
      name: 'auth-storage',
      partialize: state => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        token: state.token,
        redirectPath: state.redirectPath,
      }),
    }
  )
)

// Initialize the clearAuthStateRef after store creation
clearAuthStateRef = () => {
  useAuthStore.getState().reset()
}

// Export a function that can be called from anywhere to clear auth state
export const clearAuthState = () => {
  if (clearAuthStateRef) {
    clearAuthStateRef()
  }
}
