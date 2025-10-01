import React, { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { GlobalStyle } from '@/styles/GlobalStyles'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { LoginForm } from '@/components/auth/LoginForm'
import { RegisterForm } from '@/components/auth/RegisterForm'
import { VideoSelection } from '@/components/VideoSelection'
import { EpisodeSelection } from '@/components/EpisodeSelection'
import { ChunkedLearningPage } from '@/components/ChunkedLearningPage'
import { VocabularyLibrary } from '@/components/VocabularyLibrary'
import ProfileScreen from '@/screens/ProfileScreen'
import { useAuthStore } from '@/store/useAuthStore'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { setupAuthInterceptors } from '@/services/auth-interceptor'

// Exported for testing - this is the routing logic without the Router wrapper
export const AppRoutes: React.FC = () => {
  const { isAuthenticated } = useAuthStore()

  return (
    <Routes>
      {/* Public routes */}
      <Route
        path="/login"
        element={
          isAuthenticated ? <Navigate to="/" replace /> : <LoginForm />
        }
      />
      <Route
        path="/register"
        element={
          isAuthenticated ? <Navigate to="/" replace /> : <RegisterForm />
        }
      />

      {/* Protected routes */}
      <Route
        path="/"
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
      <Route
        path="*"
        element={
          <Navigate to={isAuthenticated ? "/" : "/login"} replace />
        }
      />
    </Routes>
  )
}

const App: React.FC = () => {
  useEffect(() => {
    // Initialize auth interceptors on app mount
    setupAuthInterceptors()
  }, [])

  return (
    <ErrorBoundary>
      <GlobalStyle />
      <Router
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true
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
            fontFamily: 'Helvetica Neue, Arial, sans-serif'
          },
          success: {
            iconTheme: {
              primary: '#46d369',
              secondary: '#fff'
            }
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff'
            }
          }
        }}
      />
    </ErrorBoundary>
  )
}

export default App
