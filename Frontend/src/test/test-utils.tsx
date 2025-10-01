/**
 * Enhanced testing utilities for React components with improved architecture
 */
import React, { ReactElement } from 'react'
import { render, RenderOptions, RenderResult } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import userEvent from '@testing-library/user-event'

import { useAppStore } from '@/store/useAppStore'
import { useVocabularyStore } from '@/store/useVocabularyStore'
import { useAuthStore } from '@/store/useAuthStore'
import { useGameStore } from '@/store/useGameStore'
import ErrorBoundary from '@/components/common/ErrorBoundary'

// Mock API client for testing
export const mockApiClient = {
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  clearCache: jest.fn(),
  clearCachePattern: jest.fn(),
}

// Mock API responses
export const mockApiResponses = {
  auth: {
    login: {
      access_token: 'mock_token_123',
      token_type: 'bearer',
      expires_in: 3600,
      user: {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        is_active: true,
        is_verified: true,
        created_at: '2023-01-01T00:00:00Z',
        last_login: null,
      },
    },
    getCurrentUser: {
      id: 1,
      username: 'testuser',
      email: 'test@example.com',
      is_active: true,
      is_verified: true,
      created_at: '2023-01-01T00:00:00Z',
      last_login: null,
    },
  },
  vocabulary: {
    search: [
      {
        id: 1,
        word: 'der Hund',
        lemma: 'Hund',
        language: 'de',
        difficulty_level: 'A1',
        part_of_speech: 'noun',
        gender: 'der',
        translation_en: 'dog',
        frequency_rank: 100,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
      },
    ],
    getByLevel: [
      {
        id: 1,
        word: 'der Hund',
        lemma: 'Hund',
        language: 'de',
        difficulty_level: 'A1',
        part_of_speech: 'noun',
        gender: 'der',
        translation_en: 'dog',
        frequency_rank: 100,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
      },
      {
        id: 2,
        word: 'die Katze',
        lemma: 'Katze',
        language: 'de',
        difficulty_level: 'A1',
        part_of_speech: 'noun',
        gender: 'die',
        translation_en: 'cat',
        frequency_rank: 150,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
      },
    ],
    getStats: {
      total_reviewed: 10,
      known_words: 7,
      unknown_words: 3,
      percentage_known: 70.0,
      level_breakdown: {
        A1: 5,
        A2: 3,
        B1: 2,
      },
    },
  },
}

// Test wrapper component with all providers
interface TestWrapperProps {
  children: React.ReactNode
  initialAuth?: {
    isAuthenticated: boolean
    user?: any
    token?: string
  }
  initialVocabulary?: any
  initialApp?: any
  initialGame?: any
}

const TestWrapper: React.FC<TestWrapperProps> = ({
  children,
  initialAuth,
  initialVocabulary,
  initialApp,
  initialGame,
}) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  })

  // Initialize stores with test data
  React.useEffect(() => {
    if (initialAuth) {
      const authStore = useAuthStore.getState()
      if (initialAuth.isAuthenticated) {
        authStore.setUser(initialAuth.user || mockApiResponses.auth.getCurrentUser)
        authStore.setToken(initialAuth.token || 'mock_token_123')
        authStore.setAuthenticated(true)
      }
    }

    if (initialVocabulary) {
      const vocabStore = useVocabularyStore.getState() as any
      Object.keys(initialVocabulary).forEach((key) => {
        if (typeof vocabStore[key] === 'function') {
          vocabStore[key](initialVocabulary[key])
        }
      })
    }

    if (initialApp) {
      const appStore = useAppStore.getState() as any
      Object.keys(initialApp).forEach((key) => {
        if (typeof appStore[key] === 'function') {
          appStore[key](initialApp[key])
        }
      })
    }

    if (initialGame) {
      const gameStore = useGameStore.getState() as any
      Object.keys(initialGame).forEach((key) => {
        if (typeof gameStore[key] === 'function') {
          gameStore[key](initialGame[key])
        }
      })
    }
  }, [initialAuth, initialVocabulary, initialApp, initialGame])

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          {children}
          <Toaster />
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

// Custom render function with providers
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  wrapperProps?: TestWrapperProps
}

export function renderWithProviders(
  ui: ReactElement,
  options: CustomRenderOptions = {}
): RenderResult & { user: ReturnType<typeof userEvent.setup> } {
  const { wrapperProps, ...renderOptions } = options

  const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <TestWrapper {...wrapperProps}>{children}</TestWrapper>
  )

  const result = render(ui, { wrapper: Wrapper, ...renderOptions })
  const user = userEvent.setup()

  return {
    ...result,
    user,
  }
}

// Helper functions for common test scenarios
export const createMockUser = (overrides = {}) => ({
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  is_active: true,
  is_verified: true,
  created_at: '2023-01-01T00:00:00Z',
  last_login: null,
  ...overrides,
})

export const createMockVocabularyWord = (overrides = {}) => ({
  id: 1,
  word: 'der Hund',
  lemma: 'Hund',
  language: 'de',
  difficulty_level: 'A1',
  part_of_speech: 'noun',
  gender: 'der',
  translation_en: 'dog',
  frequency_rank: 100,
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
  ...overrides,
})

export const createMockProgress = (overrides = {}) => ({
  id: 1,
  user_id: 1,
  vocabulary_id: 1,
  lemma: 'Hund',
  language: 'de',
  is_known: false,
  confidence_level: 0,
  review_count: 0,
  first_seen_at: '2023-01-01T00:00:00Z',
  last_reviewed_at: null,
  ...overrides,
})

// Mock API calls for testing
export const mockApi = (apiClient: any) => {
  apiClient.get.mockImplementation((url: string) => {
    if (url.includes('/auth/me')) {
      return Promise.resolve({ data: mockApiResponses.auth.getCurrentUser, status: 200 })
    }
    if (url.includes('/vocabulary/search')) {
      return Promise.resolve({ data: mockApiResponses.vocabulary.search, status: 200 })
    }
    if (url.includes('/vocabulary/level/')) {
      return Promise.resolve({ data: mockApiResponses.vocabulary.getByLevel, status: 200 })
    }
    if (url.includes('/vocabulary/stats')) {
      return Promise.resolve({ data: mockApiResponses.vocabulary.getStats, status: 200 })
    }
    return Promise.resolve({ data: [], status: 200 })
  })

  apiClient.post.mockImplementation((url: string, data: any) => {
    if (url.includes('/auth/login')) {
      return Promise.resolve({ data: mockApiResponses.auth.login, status: 200 })
    }
    if (url.includes('/vocabulary/mark')) {
      return Promise.resolve({
        data: createMockProgress({ is_known: data.is_known }),
        status: 200,
      })
    }
    return Promise.resolve({ data: {}, status: 200 })
  })
}

// Test helpers for async operations
export const waitForApiCall = async (apiMethod: jest.Mock, timeout = 5000) => {
  const startTime = Date.now()
  while (Date.now() - startTime < timeout) {
    if (apiMethod.mock.calls.length > 0) {
      return
    }
    await new Promise((resolve) => setTimeout(resolve, 10))
  }
  throw new Error('API call timeout')
}

// Helper for testing error scenarios
export const mockApiError = (apiClient: any, status = 500, message = 'Server error') => {
  const error = new Error(message)
  ;(error as any).status = status
  ;(error as any).response = { status, data: { detail: message } }

  apiClient.get.mockRejectedValue(error)
  apiClient.post.mockRejectedValue(error)
  apiClient.put.mockRejectedValue(error)
  apiClient.delete.mockRejectedValue(error)
}

// Store reset utilities
export const resetAllStores = () => {
  useAppStore.getState().reset()
  useVocabularyStore.getState().reset()
  useAuthStore.getState().reset()
  useGameStore.getState().reset()
}

// Custom matchers for testing
expect.extend({
  toBeAuthenticated(received) {
    const pass = received.isAuthenticated === true && received.user !== null
    return {
      message: () =>
        pass
          ? `Expected user not to be authenticated`
          : `Expected user to be authenticated`,
      pass,
    }
  },
  toHaveLoadingState(received, expected) {
    const pass = received.isLoading === expected
    return {
      message: () =>
        pass
          ? `Expected loading state not to be ${expected}`
          : `Expected loading state to be ${expected}, but got ${received.isLoading}`,
      pass,
    }
  },
})

// TypeScript declarations for custom matchers
declare global {
  namespace jest {
    interface Matchers<R> {
      toBeAuthenticated(): R
      toHaveLoadingState(expected: boolean): R
    }
  }
}

// Performance testing helpers
export const measureRenderTime = (renderFn: () => void): number => {
  const start = performance.now()
  renderFn()
  const end = performance.now()
  return end - start
}

export const measureAsyncOperation = async (operation: () => Promise<void>): Promise<number> => {
  const start = performance.now()
  await operation()
  const end = performance.now()
  return end - start
}

// Mock intersection observer for testing
global.IntersectionObserver = class IntersectionObserver {
  readonly root: Element | null = null
  readonly rootMargin: string = ''
  readonly thresholds: ReadonlyArray<number> = []

  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords(): IntersectionObserverEntry[] {
    return []
  }
  unobserve() {}
} as any

// Mock ResizeObserver for testing
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}

// Export everything for easy importing
export * from '@testing-library/react'
export { renderWithProviders as render }
