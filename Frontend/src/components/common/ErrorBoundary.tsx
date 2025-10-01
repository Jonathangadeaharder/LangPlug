/**
 * Enhanced Error Boundary with better error handling and fallback UI
 */
import React, { Component, ErrorInfo, ReactNode } from 'react'
import { logger } from '@/services/logger'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
  resetKeys?: Array<string | number>
  resetOnPropsChange?: boolean
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
  errorId: string | null
}

class ErrorBoundary extends Component<Props, State> {
  private resetTimeoutId: number | null = null

  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
    }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
      errorId: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const { onError } = this.props
    const errorId = this.state.errorId || 'unknown'

    // Log error details
    logger.error('ErrorBoundary', 'Caught an error', {
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      errorId,
    })

    this.setState({ errorInfo })

    // Call custom error handler
    if (onError) {
      onError(error, errorInfo)
    }

    // Report to error tracking service
    this.reportError(error, errorInfo, errorId)
  }

  componentDidUpdate(prevProps: Props) {
    const { resetKeys, resetOnPropsChange } = this.props
    const { hasError } = this.state

    if (hasError && resetOnPropsChange) {
      // Reset on any prop change
      if (prevProps !== this.props) {
        this.resetErrorBoundary()
      }
    } else if (hasError && resetKeys) {
      // Reset on specific key changes
      const prevResetKeys = prevProps.resetKeys || []
      const hasResetKeyChanged = resetKeys.some(
        (key, index) => key !== prevResetKeys[index]
      )

      if (hasResetKeyChanged) {
        this.resetErrorBoundary()
      }
    }
  }

  resetErrorBoundary = () => {
    if (this.resetTimeoutId) {
      window.clearTimeout(this.resetTimeoutId)
    }

    this.resetTimeoutId = window.setTimeout(() => {
      this.setState({
        hasError: false,
        error: null,
        errorInfo: null,
        errorId: null,
      })
    }, 100)
  }

  reportError = (error: Error, errorInfo: ErrorInfo, errorId: string) => {
    // Here you could send error reports to services like Sentry, LogRocket, etc.
    if (import.meta.env.PROD) {
      try {
        // Example: Send to error reporting service
        console.error('Error reported:', {
          errorId,
          message: error.message,
          stack: error.stack,
          componentStack: errorInfo.componentStack,
          url: window.location.href,
          userAgent: navigator.userAgent,
          timestamp: new Date().toISOString(),
        })
      } catch (reportingError) {
        console.error('Failed to report error:', reportingError)
      }
    }
  }

  render() {
    const { hasError, error, errorInfo, errorId } = this.state
    const { children, fallback } = this.props

    if (hasError) {
      if (fallback) {
        return fallback
      }

      return (
        <ErrorFallback
          error={error}
          errorInfo={errorInfo}
          errorId={errorId}
          onReset={this.resetErrorBoundary}
        />
      )
    }

    return children
  }
}

interface ErrorFallbackProps {
  error: Error | null
  errorInfo: ErrorInfo | null
  errorId: string | null
  onReset: () => void
}

const ErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  errorInfo,
  errorId,
  onReset,
}) => {
  const handleReload = () => {
    window.location.reload()
  }

  const copyErrorDetails = () => {
    const errorDetails = {
      errorId,
      message: error?.message,
      stack: error?.stack,
      componentStack: errorInfo?.componentStack,
      url: window.location.href,
      timestamp: new Date().toISOString(),
    }

    navigator.clipboard.writeText(JSON.stringify(errorDetails, null, 2))
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 text-red-500">
            <svg
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              className="w-full h-full"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.268 18.5c-.77.833.192 2.5 1.732 2.5z"
              />
            </svg>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Something went wrong
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            An unexpected error occurred while loading this page.
          </p>
        </div>

        <div className="mt-8 space-y-4">
          <button
            onClick={onReset}
            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Try Again
          </button>

          <button
            onClick={handleReload}
            className="group relative w-full flex justify-center py-2 px-4 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Reload Page
          </button>

          {import.meta.env.DEV && (
            <details className="mt-4">
              <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-800">
                Error Details (Development)
              </summary>
              <div className="mt-2 p-4 bg-gray-100 rounded-md">
                <p className="text-xs text-gray-800">
                  <strong>Error ID:</strong> {errorId}
                </p>
                {error && (
                  <div className="mt-2">
                    <p className="text-xs text-red-600">
                      <strong>Message:</strong> {error.message}
                    </p>
                    {error.stack && (
                      <pre className="mt-2 text-xs text-gray-600 overflow-auto">
                        {error.stack}
                      </pre>
                    )}
                  </div>
                )}
                <button
                  onClick={copyErrorDetails}
                  className="mt-2 text-xs text-blue-600 hover:text-blue-800"
                >
                  Copy Error Details
                </button>
              </div>
            </details>
          )}
        </div>
      </div>
    </div>
  )
}

export default ErrorBoundary

// Higher-order component for wrapping components with error boundary
export function withErrorBoundary<T extends object>(
  Component: React.ComponentType<T>,
  errorBoundaryProps?: Omit<Props, 'children'>
) {
  const WrappedComponent = (props: T) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  )

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`

  return WrappedComponent
}

// Hook for handling errors in functional components
export function useErrorHandler() {
  const handleError = React.useCallback((error: Error, errorInfo?: any) => {
    logger.error('useErrorHandler', 'Handled error', {
      error: error.message,
      stack: error.stack,
      errorInfo,
    })

    // You could also throw the error to trigger the error boundary
    // throw error
  }, [])

  return handleError
}
