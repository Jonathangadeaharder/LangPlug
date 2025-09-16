import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/types'
import * as api from '@/services/api'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name?: string) => Promise<void>
  logout: () => Promise<void>
  initializeAuth: () => Promise<void>
  checkAuth: () => Promise<void>
  clearError: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (email: string, password: string) => {
        set({ isLoading: true });
        try {
          const response = await api.login(email, password)
          set({
            user: response.user,
            token: response.token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
          localStorage.setItem('auth_token', response.token)
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || error.message;
          set({ isLoading: false, error: errorMessage });
        }
      },

      register: async (email: string, password: string, name?: string) => {
        set({ isLoading: true });
        try {
          const response = await api.register(email, password, name ?? '')
          set({
            user: response.user,
            token: response.token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
          localStorage.setItem('auth_token', response.token)
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || error.message;
          set({ isLoading: false, error: errorMessage });
        }
      },

      logout: async () => {
        // Clear state synchronously for tests that don't await logout
        localStorage.removeItem('auth_token')
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        });
        try {
          await api.logout();
        } catch {
          // Ignore API errors on logout
        }
      },

      initializeAuth: async () => {
        const storedToken = localStorage.getItem('auth_token')
        if (!storedToken) {
          return
        }
        set({ isLoading: true })
        try {
          const user = await api.getProfile()
          set({
            user,
            token: storedToken,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
        } catch (error) {
          localStorage.removeItem('auth_token')
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          })
        }
      },

      // Backwards-compatible alias
      checkAuth: async () => {
        await get().initializeAuth()
      },


      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        token: state.token,
      }),
    }
  )
);

