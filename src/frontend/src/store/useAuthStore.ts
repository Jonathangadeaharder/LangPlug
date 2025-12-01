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

const authenticate = async (email: string, password: string): Promise<User> => {
  // Login sets the HttpOnly cookie
  await authJwtLoginApiAuthLoginPost({
    formData: { username: email, password },
  })

  // Fetch user details using the cookie
  const userRead = await authGetCurrentUserApiAuthMeGet()
  return mapUser(userRead)
}

// Export this reference so we can call it from outside React components
let clearAuthStateRef: (() => void) | null = null

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      redirectPath: null,

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          const user = await authenticate(email, password)
          set({
            user,
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

          const user = await authenticate(email, password)
          set({
            user,
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
        // Client-side clear
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
          redirectPath: '/login',
        })
        // Server-side clear (removes cookie)
        try {
          await authJwtLogoutApiAuthLogoutPost()
        } catch {
          // ignore
        }
      },

      initializeAuth: async () => {
        set({ isLoading: true })
        try {
          // Try to get user. If cookie is valid, this will succeed.
          const userRead = await authGetCurrentUserApiAuthMeGet()
          set({
            user: mapUser(userRead),
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
        } catch (error) {
          // Auth failed - clear state
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            // Don't set error here as it might be just "not logged in"
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
      setAuthenticated: (val: boolean) => set({ isAuthenticated: val }),
      setRedirectPath: (path: string | null) => set({ redirectPath: path }),

      reset: () => {
        set({
          user: null,
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
