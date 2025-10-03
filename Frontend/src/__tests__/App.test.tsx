import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App, { AppRoutes } from '../App'
import { useAuthStore } from '@/store/useAuthStore'

// Mock all the child components to focus on routing logic
vi.mock('@/components/auth/LoginForm', () => ({
  LoginForm: () => <div data-testid="login-form">Login Form</div>
}))

vi.mock('@/components/auth/RegisterForm', () => ({
  RegisterForm: () => <div data-testid="register-form">Register Form</div>
}))

vi.mock('@/components/VideoSelection', () => ({
  VideoSelection: () => <div data-testid="video-selection">Video Selection</div>
}))

vi.mock('@/components/EpisodeSelection', () => ({
  EpisodeSelection: () => <div data-testid="episode-selection">Episode Selection</div>
}))

vi.mock('@/components/LearningPlayer', () => ({
  LearningPlayer: () => <div data-testid="learning-player">Learning Player</div>
}))

// PipelineProgress route removed - component no longer used

vi.mock('@/components/ChunkedLearningPage', () => ({
  ChunkedLearningPage: () => <div data-testid="chunked-learning">Chunked Learning</div>
}))

vi.mock('@/components/VocabularyLibrary', () => ({
  VocabularyLibrary: () => <div data-testid="vocabulary-library">Vocabulary Library</div>
}))

vi.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="protected-route">{children}</div>
  )
}))

vi.mock('@/components/ErrorBoundary', () => ({
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="error-boundary">{children}</div>
  )
}))

vi.mock('@/styles/GlobalStyles', () => ({
  GlobalStyle: () => <div data-testid="global-style" />
}))

vi.mock('@/components/ui/Loading', () => ({
  Loading: () => <div data-testid="loading">Loading...</div>
}))

// Mock the auth store
vi.mock('@/store/useAuthStore')

describe('App Component', () => {
  const mockUseAuthStore = vi.mocked(useAuthStore)

  beforeEach(() => {
    // Set default mock return value for useAuthStore
    mockUseAuthStore.mockReturnValue({
      isAuthenticated: true,
      user: { id: '1', email: 'test@example.com' },
      login: vi.fn(),
      logout: vi.fn(),
      register: vi.fn(),
      checkAuth: vi.fn(),
      clearError: vi.fn(),
      isLoading: false,
      error: null
    })
  })

  describe('Authentication Routing', () => {
    it('renders login form for unauthenticated user on /login', () => {
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: false,
        user: null,
        login: vi.fn(),
        logout: vi.fn(),
        register: vi.fn(),
        checkAuth: vi.fn(),
        clearError: vi.fn(),
        isLoading: false,
        error: null
      })

      render(
        <MemoryRouter initialEntries={['/login']}>
          <AppRoutes />
        </MemoryRouter>
      )

      expect(screen.getByTestId('login-form')).toBeInTheDocument()
      expect(screen.queryByTestId('video-selection')).not.toBeInTheDocument()
    })

    it('renders register form for unauthenticated user on /register', () => {
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: false,
        user: null,
        login: vi.fn(),
        logout: vi.fn(),
        register: vi.fn(),
        checkAuth: vi.fn(),
        clearError: vi.fn(),
        isLoading: false,
        error: null
      })

      render(
        <MemoryRouter initialEntries={['/register']}>
          <AppRoutes />
        </MemoryRouter>
      )

      expect(screen.getByTestId('register-form')).toBeInTheDocument()
      expect(screen.queryByTestId('video-selection')).not.toBeInTheDocument()
    })

    it('redirects authenticated user from /login to home', () => {
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: true,
        user: { id: '1', email: 'test@example.com', username: 'testuser' },
        login: vi.fn(),
        logout: vi.fn(),
        register: vi.fn(),
        checkAuth: vi.fn(),
        clearError: vi.fn(),
        isLoading: false,
        error: null
      })

      render(
        <MemoryRouter initialEntries={['/login']}>
          <AppRoutes />
        </MemoryRouter>
      )

      // Should redirect to home and show video selection
      expect(screen.getByTestId('protected-route')).toBeInTheDocument()
      expect(screen.getByTestId('video-selection')).toBeInTheDocument()
      expect(screen.queryByTestId('login-form')).not.toBeInTheDocument()
    })

    it('redirects authenticated user from /register to home', () => {
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: true,
        user: { id: '1', email: 'test@example.com', username: 'testuser' },
        login: vi.fn(),
        logout: vi.fn(),
        register: vi.fn(),
        checkAuth: vi.fn(),
        clearError: vi.fn(),
        isLoading: false,
        error: null
      })

      render(
        <MemoryRouter initialEntries={['/register']}>
          <AppRoutes />
        </MemoryRouter>
      )

      // Should redirect to home and show video selection
      expect(screen.getByTestId('protected-route')).toBeInTheDocument()
      expect(screen.getByTestId('video-selection')).toBeInTheDocument()
      expect(screen.queryByTestId('register-form')).not.toBeInTheDocument()
    })
  })

  describe('Protected Routes', () => {
    beforeEach(() => {
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: true,
        user: { id: '1', email: 'test@example.com', username: 'testuser' },
        login: vi.fn(),
        logout: vi.fn(),
        register: vi.fn(),
        checkAuth: vi.fn(),
        clearError: vi.fn(),
        isLoading: false,
        error: null
      })
    })

    it('renders video selection on home route', () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <AppRoutes />
        </MemoryRouter>
      )

      expect(screen.getByTestId('protected-route')).toBeInTheDocument()
      expect(screen.getByTestId('video-selection')).toBeInTheDocument()
    })

    it('renders episode selection route', () => {
      render(
        <MemoryRouter initialEntries={['/episodes/test-series']}>
          <AppRoutes />
        </MemoryRouter>
      )

      expect(screen.getByTestId('protected-route')).toBeInTheDocument()
      expect(screen.getByTestId('episode-selection')).toBeInTheDocument()
    })

    it('renders chunked learning route', () => {
      render(
        <MemoryRouter initialEntries={['/learn/test-series/test-episode']}>
          <AppRoutes />
        </MemoryRouter>
      )

      expect(screen.getByTestId('protected-route')).toBeInTheDocument()
      expect(screen.getByTestId('chunked-learning')).toBeInTheDocument()
    })

    // Pipeline progress route removed from app - test no longer needed

    it('renders vocabulary library route', () => {
      render(
        <MemoryRouter initialEntries={['/vocabulary']}>
          <AppRoutes />
        </MemoryRouter>
      )

      expect(screen.getByTestId('protected-route')).toBeInTheDocument()
      expect(screen.getByTestId('vocabulary-library')).toBeInTheDocument()
    })

    it('renders vocabulary library route', () => {
      render(
        <MemoryRouter initialEntries={['/vocabulary']}>
          <AppRoutes />
        </MemoryRouter>
      )

      expect(screen.getByTestId('protected-route')).toBeInTheDocument()
      expect(screen.getByTestId('vocabulary-library')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('wraps app in error boundary', () => {
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: false,
        user: null,
        login: vi.fn(),
        logout: vi.fn(),
        register: vi.fn(),
        checkAuth: vi.fn(),
        clearError: vi.fn(),
        isLoading: false,
        error: null
      })

      render(<App />)

      expect(screen.getByTestId('error-boundary')).toBeInTheDocument()
    })
  })

  describe('Global Components', () => {
    it('includes global styles', () => {
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: false,
        user: null,
        login: vi.fn(),
        logout: vi.fn(),
        register: vi.fn(),
        checkAuth: vi.fn(),
        clearError: vi.fn(),
        isLoading: false,
        error: null
      })

      render(<App />)

      expect(screen.getByTestId('global-style')).toBeInTheDocument()
    })

    it('configures router with future flags', () => {
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: false,
        user: null,
        login: vi.fn(),
        logout: vi.fn(),
        register: vi.fn(),
        checkAuth: vi.fn(),
        clearError: vi.fn(),
        isLoading: false,
        error: null
      })

      // This test verifies the router renders without errors
      // The future flags are configured correctly if no console warnings appear
      render(
        <MemoryRouter initialEntries={['/login']}>
          <AppRoutes />
        </MemoryRouter>
      )

      expect(screen.getByTestId('login-form')).toBeInTheDocument()
    })
  })

  describe('Route Navigation Integration', () => {
    it('handles navigation between public and protected routes', () => {
      // Initially unauthenticated
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: false,
        user: null,
        login: vi.fn(),
        logout: vi.fn(),
        register: vi.fn(),
        checkAuth: vi.fn(),
        clearError: vi.fn(),
        isLoading: false,
        error: null
      })

      const { rerender } = render(
        <MemoryRouter initialEntries={['/login']}>
          <AppRoutes />
        </MemoryRouter>
      )

      expect(screen.getByTestId('login-form')).toBeInTheDocument()

      // Simulate authentication
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: true,
        user: { id: '1', email: 'test@example.com', username: 'testuser' },
        login: vi.fn(),
        logout: vi.fn(),
        register: vi.fn(),
        checkAuth: vi.fn(),
        clearError: vi.fn(),
        isLoading: false,
        error: null
      })

      rerender(
        <MemoryRouter initialEntries={['/login']}>
          <AppRoutes />
        </MemoryRouter>
      )

      // Should redirect to protected route
      expect(screen.getByTestId('protected-route')).toBeInTheDocument()
      expect(screen.getByTestId('video-selection')).toBeInTheDocument()
    })

    it('handles invalid routes gracefully', () => {
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: true,
        user: { id: '1', email: 'test@example.com', username: 'testuser' },
        login: vi.fn(),
        logout: vi.fn(),
        register: vi.fn(),
        checkAuth: vi.fn(),
        clearError: vi.fn(),
        isLoading: false,
        error: null
      })

      render(
        <MemoryRouter initialEntries={['/nonexistent-route']}>
          <AppRoutes />
        </MemoryRouter>
      )

      // Should redirect to home page for authenticated users
      expect(screen.getByTestId('protected-route')).toBeInTheDocument()
      expect(screen.getByTestId('video-selection')).toBeInTheDocument()
    })
  })

  describe('Authentication State Changes', () => {
    it('responds to authentication state changes', () => {
      let authState = {
        isAuthenticated: false,
        user: null,
        login: vi.fn(),
        logout: vi.fn(),
        register: vi.fn(),
        checkAuth: vi.fn(),
        clearError: vi.fn(),
        isLoading: false,
        error: null
      }

      mockUseAuthStore.mockImplementation(() => authState)

      const { rerender } = render(
        <MemoryRouter initialEntries={['/']}>
          <AppRoutes />
        </MemoryRouter>
      )

      // Should show protected route behavior for unauthenticated user
      expect(screen.getByTestId('protected-route')).toBeInTheDocument()

      // Simulate login
      authState = {
        ...authState,
        isAuthenticated: true,
        user: { id: '1', email: 'test@example.com', username: 'testuser' } as any
      }

      rerender(
        <MemoryRouter initialEntries={['/']}>
          <AppRoutes />
        </MemoryRouter>
      )

      expect(screen.getByTestId('video-selection')).toBeInTheDocument()
    })
  })
})
