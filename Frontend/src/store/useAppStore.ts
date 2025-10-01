/**
 * Global application store with improved architecture
 */
import { create } from 'zustand'
import { subscribeWithSelector, devtools } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'

export interface AppConfig {
  theme: 'light' | 'dark' | 'system'
  language: string
  autoSaveProgress: boolean
  showAdvancedFeatures: boolean
  debugMode: boolean
}

export interface NotificationState {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  duration?: number
  timestamp: number
}

export interface AppState {
  // Configuration
  config: AppConfig

  // UI State
  isLoading: boolean
  notifications: NotificationState[]
  sidebarOpen: boolean

  // Error handling
  lastError: string | null
  errorHistory: Array<{ error: string; timestamp: number }>

  // Performance tracking
  performanceMetrics: {
    loadTimes: Record<string, number>
    apiResponseTimes: Record<string, number>
  }

  // Actions
  setConfig: (config: Partial<AppConfig>) => void
  setLoading: (loading: boolean) => void
  addNotification: (notification: Omit<NotificationState, 'id' | 'timestamp'>) => void
  removeNotification: (id: string) => void
  clearNotifications: () => void
  setSidebarOpen: (open: boolean) => void
  setError: (error: string | null) => void
  clearErrorHistory: () => void
  recordLoadTime: (page: string, time: number) => void
  recordApiResponseTime: (endpoint: string, time: number) => void
  reset: () => void
}

const initialConfig: AppConfig = {
  theme: 'system',
  language: 'de',
  autoSaveProgress: true,
  showAdvancedFeatures: false,
  debugMode: import.meta.env.DEV,
}

const initialState = {
  config: initialConfig,
  isLoading: false,
  notifications: [],
  sidebarOpen: false,
  lastError: null,
  errorHistory: [],
  performanceMetrics: {
    loadTimes: {},
    apiResponseTimes: {},
  },
}

export const useAppStore = create<AppState>()(
  devtools(
    subscribeWithSelector(
      immer((set, get) => ({
        ...initialState,

        setConfig: (newConfig) => {
          set((state) => {
            state.config = { ...state.config, ...newConfig }
          })
        },

        setLoading: (loading) => {
          set((state) => {
            state.isLoading = loading
          })
        },

        addNotification: (notification) => {
          const id = `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
          set((state) => {
            state.notifications.push({
              ...notification,
              id,
              timestamp: Date.now(),
            })
          })

          // Auto-remove notification after duration
          if (notification.duration && notification.duration > 0) {
            setTimeout(() => {
              get().removeNotification(id)
            }, notification.duration)
          }
        },

        removeNotification: (id) => {
          set((state) => {
            state.notifications = state.notifications.filter((n: NotificationState) => n.id !== id)
          })
        },

        clearNotifications: () => {
          set((state) => {
            state.notifications = []
          })
        },

        setSidebarOpen: (open) => {
          set((state) => {
            state.sidebarOpen = open
          })
        },

        setError: (error) => {
          set((state) => {
            state.lastError = error
            if (error) {
              state.errorHistory.push({
                error,
                timestamp: Date.now(),
              })
              // Keep only last 10 errors
              if (state.errorHistory.length > 10) {
                state.errorHistory = state.errorHistory.slice(-10)
              }
            }
          })
        },

        clearErrorHistory: () => {
          set((state) => {
            state.errorHistory = []
            state.lastError = null
          })
        },

        recordLoadTime: (page, time) => {
          set((state) => {
            state.performanceMetrics.loadTimes[page] = time
          })
        },

        recordApiResponseTime: (endpoint, time) => {
          set((state) => {
            state.performanceMetrics.apiResponseTimes[endpoint] = time
          })
        },

        reset: () => {
          set(initialState)
        },
      }))
    ),
    {
      name: 'app-store',
    }
  )
)

// Selectors for better performance
export const useAppConfig = () => useAppStore((state) => state.config)
export const useAppLoading = () => useAppStore((state) => state.isLoading)
export const useAppNotifications = () => useAppStore((state) => state.notifications)
export const useAppError = () => useAppStore((state) => state.lastError)
export const useAppPerformance = () => useAppStore((state) => state.performanceMetrics)

// Persist config to localStorage
useAppStore.subscribe(
  (state) => state.config,
  (config) => {
    try {
      localStorage.setItem('langplug-config', JSON.stringify(config))
    } catch (error) {
      console.warn('Failed to persist config to localStorage:', error)
    }
  }
)

// Load config from localStorage on startup
try {
  const savedConfig = localStorage.getItem('langplug-config')
  if (savedConfig) {
    const parsedConfig = JSON.parse(savedConfig)
    useAppStore.getState().setConfig(parsedConfig)
  }
} catch (error) {
  console.warn('Failed to load config from localStorage:', error)
}
