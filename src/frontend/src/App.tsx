import React, { useEffect, lazy, Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { Toaster } from 'react-hot-toast'
import { ThemeProvider } from 'styled-components'
import { GlobalStyle } from '@/styles/GlobalStyles'
import { lightTheme } from '@/styles/theme'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { useAuthStore } from '@/store/useAuthStore'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { Loading } from '@/components/ui/Loading'
import { BackendReadinessCheck } from '@/components/BackendReadinessCheck'
import { setupAuthInterceptors } from '@/services/auth-interceptor'
import { queryClient } from '@/lib/queryClient'

// Lazy load route components for code splitting
const LandingPage = lazy(() =>
  import('@/components/LandingPage').then(m => ({ default: m.LandingPage }))
)
const LoginForm = lazy(() =>
  import('@/components/auth/LoginForm').then(m => ({ default: m.LoginForm }))
)
const RegisterForm = lazy(() =>
  import('@/components/auth/RegisterForm').then(m => ({ default: m.RegisterForm }))
)
const VideoSelection = lazy(() =>
  import('@/components/VideoSelection').then(m => ({ default: m.VideoSelection }))
)
const EpisodeSelection = lazy(() =>
  import('@/components/EpisodeSelection').then(m => ({ default: m.EpisodeSelection }))
)
const ChunkedLearningPage = lazy(() =>
  import('@/components/ChunkedLearningPage').then(m => ({ default: m.ChunkedLearningPage }))
)
const VocabularyLibrary = lazy(() =>
  import('@/components/VocabularyLibrary').then(m => ({ default: m.VocabularyLibrary }))
)
const ProfileScreen = lazy(() => import('@/screens/ProfileScreen'))

// Exported for testing - this is the routing logic without the Router wrapper
export const AppRoutes: React.FC = () => {
  const { isAuthenticated } = useAuthStore()

  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        {/* Public routes */}
        <Route
          path="/"
          element={isAuthenticated ? <Navigate to="/videos" replace /> : <LandingPage />}
        />
        <Route
          path="/login"
          element={isAuthenticated ? <Navigate to="/videos" replace /> : <LoginForm />}
        />
        <Route
          path="/register"
          element={isAuthenticated ? <Navigate to="/videos" replace /> : <RegisterForm />}
        />

        {/* Protected routes */}
        <Route
          path="/videos"
          element={
            <ProtectedRoute>
              <VideoSelection />
            </ProtectedRoute>
          }
        />

        <Route
          path="/episodes/:series"
          element={
            <ProtectedRoute>
              <EpisodeSelection />
            </ProtectedRoute>
          }
        />

        <Route
          path="/learn/:series/:episode"
          element={
            <ProtectedRoute>
              <ChunkedLearningPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/vocabulary"
          element={
            <ProtectedRoute>
              <VocabularyLibrary />
            </ProtectedRoute>
          }
        />

        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <ProfileScreen />
            </ProtectedRoute>
          }
        />

        {/* Fallback route */}
        <Route path="*" element={<Navigate to={isAuthenticated ? '/videos' : '/'} replace />} />
      </Routes>
    </Suspense>
  )
}

const App: React.FC = () => {
  useEffect(() => {
    // Initialize auth interceptors on app mount
    setupAuthInterceptors()
  }, [])

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={lightTheme}>
          <GlobalStyle />
          <BackendReadinessCheck>
            <Router
              future={{
                v7_startTransition: true,
                v7_relativeSplatPath: true,
              }}
            >
              <AppRoutes />
            </Router>

            <Toaster
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#363636',
                  color: '#fff',
                  fontFamily: 'Helvetica Neue, Arial, sans-serif',
                },
                success: {
                  iconTheme: {
                    primary: '#46d369',
                    secondary: '#fff',
                  },
                },
                error: {
                  iconTheme: {
                    primary: '#ef4444',
                    secondary: '#fff',
                  },
                },
              }}
            />
          </BackendReadinessCheck>
        </ThemeProvider>
        {/* React Query Devtools - only in development */}
        {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

export default App
