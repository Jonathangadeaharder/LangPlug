import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App, { AppRoutes } from '../App'
import { useAuthStore } from '@/store/useAuthStore'

// Mock all the child components to focus on routing logic
vi.mock('@/components/auth/LoginForm', () => ({
  LoginForm: () => <div data-testid="login-form">Login Form</div>,
}))

vi.mock('@/components/auth/RegisterForm', () => ({
  RegisterForm: () => <div data-testid="register-form">Register Form</div>,
}))

vi.mock('@/components/VideoSelection', () => ({
  VideoSelection: () => <div data-testid="video-selection">Video Selection</div>,
}))

vi.mock('@/components/EpisodeSelection', () => ({
  EpisodeSelection: () => <div data-testid="episode-selection">Episode Selection</div>,
}))

vi.mock('@/components/LearningPlayer', () => ({
  LearningPlayer: () => <div data-testid="learning-player">Learning Player</div>,
}))

// PipelineProgress route removed - component no longer used

vi.mock('@/components/ChunkedLearningPage', () => ({
  ChunkedLearningPage: () => <div data-testid="chunked-learning">Chunked Learning</div>,
}))

vi.mock('@/components/VocabularyLibrary', () => ({
  VocabularyLibrary: () => <div data-testid="vocabulary-library">Vocabulary Library</div>,
}))

vi.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="protected-route">{children}</div>
  ),
}))

vi.mock('@/components/ErrorBoundary', () => ({
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="error-boundary">{children}</div>
  ),
}))

vi.mock('@/styles/GlobalStyles', () => ({
  GlobalStyle: () => <div data-testid="global-style" />,
}))

vi.mock('@/components/ui/Loading', () => ({
  Loading: () => <div data-testid="loading">Loading...</div>,
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
      error: null,
    })
  })

  describe('Authentication Routing', () => {
    it('renders login form for unauthenticated user on /login', async () => {
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: false,
        user: null,
        login: vi.fn(),
        logout: vi.fn(),
        register: vi.fn(),
        checkAuth: vi.fn(),
        clearError: vi.fn(),
        isLoading: false,
        error: null,
      })

      await act(async () => {
        render(
          <MemoryRouter initialEntries={['/login']}>
            <AppRoutes />
          </MemoryRouter>
        )
      })

      await waitFor(() => {
        expect(screen.getByTestId('login-form')).toBeInTheDocument()
      })
      expect(screen.queryByTestId('video-selection')).not.toBeInTheDocument()
    })

    it('renders register form for unauthenticated user on /register', async () => {
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: false,
        user: null,
        login: vi.fn(),
        logout: vi.fn(),
        register: vi.fn(),
        checkAuth: vi.fn(),
        clearError: vi.fn(),
        isLoading: false,
        error: null,
      })

      await act(async () => {
        render(
          <MemoryRouter initialEntries={['/register']}>
            <AppRoutes />
          </MemoryRouter>
        )
      })

      await waitFor(() => {
        expect(screen.getByTestId('register-form')).toBeInTheDocument()
      })
      expect(screen.queryByTestId('video-selection')).not.toBeInTheDocument()
    })

    it('redirects authenticated user from /login to home', async () => {
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: true,
        user: { id: '1', email: 'test@example.com', username: 'testuser' },
        login: vi.fn(),
        logout: vi.fn(),
        register: vi.fn(),
        checkAuth: vi.fn(),
        clearError: vi.fn(),
        isLoading: false,
        error: null,
      })

      await act(async () => {
        render(
          <MemoryRouter initialEntries={['/login']}>
            <AppRoutes />
          </MemoryRouter>
        )
      })

      // Should redirect to home and show video selection
      await waitFor(() => {
        expect(screen.getByTestId('protected-route')).toBeInTheDocument()
      })
      expect(screen.getByTestId('video-selection')).toBeInTheDocument()
      expect(screen.queryByTestId('login-form')).not.toBeInTheDocument()
    })

    it('redirects authenticated user from /register to home', async () => {
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: true,
        user: { id: '1', email: 'test@example.com', username: 'testuser' },
        login: vi.fn(),
        logout: vi.fn(),
        register: vi.fn(),
        checkAuth: vi.fn(),
        clearError: vi.fn(),
        isLoading: false,
        error: null,
      })

      await act(async () => {
        render(
          <MemoryRouter initialEntries={['/register']}>
            <AppRoutes />
          </MemoryRouter>
        )
      })

      // Should redirect to home and show video selection
      await waitFor(() => {
        expect(screen.getByTestId('protected-route')).toBeInTheDocument()
      })
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
        error: null,
      })
    })

    it('renders video selection on home route', async () => {
      await act(async () => {
        render(
          <MemoryRouter initialEntries={['/']}>
            <AppRoutes />
          </MemoryRouter>
        )
      })

      await waitFor(() => {
        expect(screen.getByTestId('protected-route')).toBeInTheDocument()
      })
      expect(screen.getByTestId('video-selection')).toBeInTheDocument()
    })

    it('renders episode selection route', async () => {
      await act(async () => {
        render(
          <MemoryRouter initialEntries={['/episodes/test-series']}>
            <AppRoutes />
          </MemoryRouter>
        )
      })

      await waitFor(() => {
        expect(screen.getByTestId('protected-route')).toBeInTheDocument()
      })
      expect(screen.getByTestId('episode-selection')).toBeInTheDocument()
    })

    it('renders chunked learning route', async () => {
      await act(async () => {
        render(
          <MemoryRouter initialEntries={['/learn/test-series/test-episode']}>
            <AppRoutes />
          </MemoryRouter>
        )
      })

      await waitFor(() => {
        expect(screen.getByTestId('protected-route')).toBeInTheDocument()
      })
      expect(screen.getByTestId('chunked-learning')).toBeInTheDocument()
    })

    it('renders vocabulary library route', async () => {
      await act(async () => {
        render(
          <MemoryRouter initialEntries={['/vocabulary']}>
            <AppRoutes />
          </MemoryRouter>
        )
      })

      await waitFor(() => {
        expect(screen.getByTestId('protected-route')).toBeInTheDocument()
      })
      expect(screen.getByTestId('vocabulary-library')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('wraps app in error boundary', async () => {
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: false,
        user: null,
        login: vi.fn(),
        logout: vi.fn(),
        register: vi.fn(),
        checkAuth: vi.fn(),
        clearError: vi.fn(),
        isLoading: false,
        error: null,
      })

      await act(async () => {
        render(<App />)
      })

      await waitFor(() => {
        expect(screen.getByTestId('error-boundary')).toBeInTheDocument()
      })
    })
  })

  describe('Global Components', () => {
    it('includes global styles', async () => {
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: false,
        user: null,
        login: vi.fn(),
        logout: vi.fn(),
        register: vi.fn(),
        checkAuth: vi.fn(),
        clearError: vi.fn(),
        isLoading: false,
        error: null,
      })

      await act(async () => {
        render(<App />)
      })

      await waitFor(() => {
        expect(screen.getByTestId('global-style')).toBeInTheDocument()
      })
    })

    it('configures router with future flags', async () => {
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: false,
        user: null,
        login: vi.fn(),
        logout: vi.fn(),
        register: vi.fn(),
        checkAuth: vi.fn(),
        clearError: vi.fn(),
        isLoading: false,
        error: null,
      })

      await act(async () => {
        render(
          <MemoryRouter initialEntries={['/login']}>
            <AppRoutes />
          </MemoryRouter>
        )
      })

      await waitFor(() => {
        expect(screen.getByTestId('login-form')).toBeInTheDocument()
      })
    })
  })

  describe('Route Navigation Integration', () => {
    it('handles navigation between public and protected routes', async () => {
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
        error: null,
      })

      const { rerender } = render(
        <MemoryRouter initialEntries={['/login']}>
          <AppRoutes />
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByTestId('login-form')).toBeInTheDocument()
      })

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
        error: null,
      })

      await act(async () => {
        rerender(
          <MemoryRouter initialEntries={['/login']}>
            <AppRoutes />
          </MemoryRouter>
        )
      })

      // Should redirect to protected route
      await waitFor(() => {
        expect(screen.getByTestId('protected-route')).toBeInTheDocument()
      })
      expect(screen.getByTestId('video-selection')).toBeInTheDocument()
    })

    it('handles invalid routes gracefully', async () => {
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: true,
        user: { id: '1', email: 'test@example.com', username: 'testuser' },
        login: vi.fn(),
        logout: vi.fn(),
        register: vi.fn(),
        checkAuth: vi.fn(),
        clearError: vi.fn(),
        isLoading: false,
        error: null,
      })

      await act(async () => {
        render(
          <MemoryRouter initialEntries={['/nonexistent-route']}>
            <AppRoutes />
          </MemoryRouter>
        )
      })

      // Should redirect to home page for authenticated users
      await waitFor(() => {
        expect(screen.getByTestId('protected-route')).toBeInTheDocument()
      })
      expect(screen.getByTestId('video-selection')).toBeInTheDocument()
    })
  })
})