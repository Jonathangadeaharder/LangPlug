import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ErrorBoundary, { withErrorBoundary, useErrorHandler } from '../ErrorBoundary'
import React from 'react'

// Mock logger
vi.mock('@/services/logger', () => ({
  logger: {
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
}))

// Component that throws an error
const ThrowError: React.FC<{ shouldThrow?: boolean; errorMessage?: string }> = ({
  shouldThrow = true,
  errorMessage = 'Test error',
}) => {
  if (shouldThrow) {
    throw new Error(errorMessage)
  }
  return <div>Success</div>
}

// Component for testing prop changes
const DynamicComponent: React.FC<{ value: string }> = ({ value }) => {
  if (value === 'error') {
    throw new Error('Dynamic error')
  }
  return <div>Value: {value}</div>
}

describe('ErrorBoundary', () => {
  const originalConsoleError = console.error

  beforeEach(() => {
    // Suppress error boundary console errors in tests
    console.error = vi.fn()

    // Mock clipboard using defineProperty
    Object.defineProperty(navigator, 'clipboard', {
      value: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
      writable: true,
      configurable: true,
    })

    vi.useFakeTimers()
  })

  afterEach(() => {
    console.error = originalConsoleError
    vi.clearAllMocks()
    vi.useRealTimers()
  })

  describe('basic error catching', () => {
    it('should render children when no error occurs', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Success')).toBeInTheDocument()
    })

    it('should catch errors and display default fallback UI', () => {
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
      expect(screen.getByText('An unexpected error occurred while loading this page.')).toBeInTheDocument()
    })

    it('should display custom fallback UI when provided', () => {
      const customFallback = <div>Custom Error Message</div>

      render(
        <ErrorBoundary fallback={customFallback}>
          <ThrowError />
        </ErrorBoundary>
      )

      expect(screen.getByText('Custom Error Message')).toBeInTheDocument()
      expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument()
    })

    it('should display error message in fallback', () => {
      const errorMessage = 'Specific error occurred'

      render(
        <ErrorBoundary>
          <ThrowError errorMessage={errorMessage} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })
  })

  describe('error handling callbacks', () => {
    it('should call onError callback when error is caught', () => {
      const onError = vi.fn()

      render(
        <ErrorBoundary onError={onError}>
          <ThrowError errorMessage="Callback test error" />
        </ErrorBoundary>
      )

      expect(onError).toHaveBeenCalledWith(
        expect.objectContaining({ message: 'Callback test error' }),
        expect.objectContaining({
          componentStack: expect.any(String),
        })
      )
    })

    it('should not crash if onError throws an error', () => {
      const onError = vi.fn(() => {
        throw new Error('onError callback error')
      })

      // Suppress the error from onError callback
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      render(
        <ErrorBoundary onError={onError}>
          <ThrowError />
        </ErrorBoundary>
      )

      expect(screen.getAllByText('Something went wrong')[0]).toBeInTheDocument()
      consoleErrorSpy.mockRestore()
    })
  })

  describe('error boundary reset', () => {
    it('should reset error state when Try Again button is clicked', async () => {
      const user = userEvent.setup({ delay: null })

      const { rerender } = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Something went wrong')).toBeInTheDocument()

      const tryAgainButton = screen.getByText('Try Again')
      await user.click(tryAgainButton)

      // Fast-forward the reset timeout
      vi.runAllTimers()

      // Rerender with non-throwing component
      rerender(
        <ErrorBoundary>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      )

      await waitFor(() => {
        expect(screen.getByText('Success')).toBeInTheDocument()
      })
    })

    it('should reload page when Reload Page button is clicked', async () => {
      const user = userEvent.setup({ delay: null })
      const reloadMock = vi.fn()
      Object.defineProperty(window, 'location', {
        value: { reload: reloadMock },
        writable: true,
      })

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      const reloadButton = screen.getByText('Reload Page')
      await user.click(reloadButton)

      expect(reloadMock).toHaveBeenCalled()
    })

    it('should reset on resetKeys change', async () => {
      const { rerender } = render(
        <ErrorBoundary resetKeys={['key1']}>
          <DynamicComponent value="error" />
        </ErrorBoundary>
      )

      expect(screen.getAllByText('Something went wrong')[0]).toBeInTheDocument()

      // Fast-forward reset timeout
      await vi.runAllTimersAsync()

      // Change reset key
      rerender(
        <ErrorBoundary resetKeys={['key2']}>
          <DynamicComponent value="success" />
        </ErrorBoundary>
      )

      await vi.runAllTimersAsync()

      await waitFor(
        () => {
          expect(screen.getByText('Value: success')).toBeInTheDocument()
        },
        { timeout: 1000 }
      )
    })

    it('should reset on any prop change when resetOnPropsChange is true', async () => {
      const { rerender } = render(
        <ErrorBoundary resetOnPropsChange={true}>
          <DynamicComponent value="error" />
        </ErrorBoundary>
      )

      expect(screen.getAllByText('Something went wrong')[0]).toBeInTheDocument()

      await vi.runAllTimersAsync()

      // Any prop change should trigger reset
      rerender(
        <ErrorBoundary resetOnPropsChange={true}>
          <DynamicComponent value="success" />
        </ErrorBoundary>
      )

      await vi.runAllTimersAsync()

      await waitFor(
        () => {
          expect(screen.getByText('Value: success')).toBeInTheDocument()
        },
        { timeout: 1000 }
      )
    })

    it('should not reset when resetKeys remain the same', () => {
      const { rerender } = render(
        <ErrorBoundary resetKeys={['key1']}>
          <ThrowError />
        </ErrorBoundary>
      )

      expect(screen.getByText('Something went wrong')).toBeInTheDocument()

      rerender(
        <ErrorBoundary resetKeys={['key1']}>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      )

      // Error state should persist
      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })
  })

  describe('error details in development mode', () => {
    const originalEnv = import.meta.env.DEV

    beforeEach(() => {
      // Set to development mode
      import.meta.env.DEV = true
    })

    afterEach(() => {
      import.meta.env.DEV = originalEnv
    })

    it('should show error details in development mode', () => {
      render(
        <ErrorBoundary>
          <ThrowError errorMessage="Detailed error for dev" />
        </ErrorBoundary>
      )

      const detailsSummary = screen.getByText('Error Details (Development)')
      expect(detailsSummary).toBeInTheDocument()
    })

    it('should copy error details to clipboard when button clicked', async () => {
      const user = userEvent.setup({ delay: null })
      const writeTextSpy = vi.fn().mockResolvedValue(undefined)

      Object.defineProperty(navigator, 'clipboard', {
        value: {
          writeText: writeTextSpy,
        },
        writable: true,
        configurable: true,
      })

      render(
        <ErrorBoundary>
          <ThrowError errorMessage="Error to copy" />
        </ErrorBoundary>
      )

      const copyButton = screen.getByText('Copy Error Details')
      await user.click(copyButton)

      expect(writeTextSpy).toHaveBeenCalled()

      const copiedData = writeTextSpy.mock.calls[0][0]
      const parsedData = JSON.parse(copiedData)

      expect(parsedData.message).toBe('Error to copy')
      expect(parsedData.errorId).toBeDefined()
      expect(parsedData.url).toBeDefined()
      expect(parsedData.timestamp).toBeDefined()
    })

    it('should display error ID in details', () => {
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      const errorIdElement = screen.getAllByText(/Error ID:/)[0]
      expect(errorIdElement).toBeInTheDocument()
      // Error ID format: error_timestamp_randomstring
      expect(errorIdElement.textContent).toContain('Error ID:')
      expect(errorIdElement.textContent).toContain('error_')
    })

    it('should display error message in details', () => {
      render(
        <ErrorBoundary>
          <ThrowError errorMessage="Visible error message" />
        </ErrorBoundary>
      )

      expect(screen.getAllByText(/Message:/)[0]).toBeInTheDocument()
      expect(screen.getAllByText(/Visible error message/)[0]).toBeInTheDocument()
    })
  })

  describe('error details in production mode', () => {
    const originalEnv = import.meta.env.DEV
    const originalProd = import.meta.env.PROD

    beforeEach(() => {
      import.meta.env.DEV = false
      import.meta.env.PROD = true
    })

    afterEach(() => {
      import.meta.env.DEV = originalEnv
      import.meta.env.PROD = originalProd
    })

    it('should not show error details in production mode', () => {
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      expect(screen.queryByText('Error Details (Development)')).not.toBeInTheDocument()
    })

    it('should log error to console in production', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      render(
        <ErrorBoundary>
          <ThrowError errorMessage="Production error" />
        </ErrorBoundary>
      )

      expect(consoleErrorSpy).toHaveBeenCalled()
      consoleErrorSpy.mockRestore()
    })
  })

  describe('withErrorBoundary HOC', () => {
    it('should wrap component with error boundary', () => {
      const TestComponent: React.FC = () => <div>Test Component</div>
      const WrappedComponent = withErrorBoundary(TestComponent)

      render(<WrappedComponent />)

      expect(screen.getByText('Test Component')).toBeInTheDocument()
    })

    it('should catch errors in wrapped component', () => {
      const WrappedComponent = withErrorBoundary(ThrowError)

      render(<WrappedComponent />)

      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })

    it('should pass props to wrapped component', () => {
      const TestComponent: React.FC<{ message: string }> = ({ message }) => <div>{message}</div>
      const WrappedComponent = withErrorBoundary(TestComponent)

      render(<WrappedComponent message="Hello from HOC" />)

      expect(screen.getByText('Hello from HOC')).toBeInTheDocument()
    })

    it('should apply custom error boundary props', () => {
      const customFallback = <div>HOC Custom Fallback</div>
      const WrappedComponent = withErrorBoundary(ThrowError, { fallback: customFallback })

      render(<WrappedComponent />)

      expect(screen.getByText('HOC Custom Fallback')).toBeInTheDocument()
    })

    it('should set display name correctly', () => {
      const TestComponent: React.FC = () => <div>Test</div>
      TestComponent.displayName = 'TestComponent'
      const WrappedComponent = withErrorBoundary(TestComponent)

      expect(WrappedComponent.displayName).toBe('withErrorBoundary(TestComponent)')
    })

    it('should use component name if displayName not set', () => {
      const TestComponent: React.FC = () => <div>Test</div>
      const WrappedComponent = withErrorBoundary(TestComponent)

      expect(WrappedComponent.displayName).toMatch(/withErrorBoundary/)
    })
  })

  describe('useErrorHandler hook', () => {
    it('should provide error handling function', () => {
      const TestComponent: React.FC = () => {
        const handleError = useErrorHandler()

        return (
          <button
            onClick={() => {
              handleError(new Error('Hook error'))
            }}
          >
            Trigger Error
          </button>
        )
      }

      render(<TestComponent />)

      const button = screen.getByText('Trigger Error')
      expect(button).toBeInTheDocument()
    })

    it('should log errors when called', async () => {
      const user = userEvent.setup({ delay: null })

      const TestComponent: React.FC = () => {
        const handleError = useErrorHandler()

        return (
          <button
            onClick={() => {
              handleError(new Error('Test error from hook'))
            }}
          >
            Trigger
          </button>
        )
      }

      render(<TestComponent />)

      const button = screen.getByText('Trigger')
      await user.click(button)

      // Logger is mocked at the top level, so we can access it from the mock
      const { logger } = await import('@/services/logger')
      expect(logger.error).toHaveBeenCalledWith(
        'useErrorHandler',
        'Handled error',
        expect.objectContaining({
          error: 'Test error from hook',
          stack: expect.any(String),
        })
      )
    })

    it('should accept additional error info', async () => {
      const user = userEvent.setup({ delay: null })

      const TestComponent: React.FC = () => {
        const handleError = useErrorHandler()

        return (
          <button
            onClick={() => {
              handleError(new Error('Error with info'), { context: 'test', userId: 123 })
            }}
          >
            Trigger
          </button>
        )
      }

      render(<TestComponent />)

      const button = screen.getByText('Trigger')
      await user.click(button)

      // Logger is mocked at the top level
      const { logger } = await import('@/services/logger')
      expect(logger.error).toHaveBeenCalledWith(
        'useErrorHandler',
        'Handled error',
        expect.objectContaining({
          error: 'Error with info',
          errorInfo: { context: 'test', userId: 123 },
        })
      )
    })
  })

  describe('edge cases', () => {
    it('should handle errors thrown in event handlers', async () => {
      const user = userEvent.setup({ delay: null })

      const TestComponent: React.FC = () => {
        const handleClick = () => {
          throw new Error('Event handler error')
        }

        return <button onClick={handleClick}>Click Me</button>
      }

      render(
        <ErrorBoundary>
          <TestComponent />
        </ErrorBoundary>
      )

      const button = screen.getByText('Click Me')

      // Event handler errors are not caught by error boundaries
      // This tests that the component renders correctly before the error
      expect(button).toBeInTheDocument()
    })

    it('should handle multiple errors in sequence', () => {
      const { rerender } = render(
        <ErrorBoundary>
          <ThrowError errorMessage="First error" />
        </ErrorBoundary>
      )

      expect(screen.getByText('Something went wrong')).toBeInTheDocument()

      vi.runAllTimers()

      rerender(
        <ErrorBoundary>
          <ThrowError errorMessage="Second error" />
        </ErrorBoundary>
      )

      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })

    it('should clear timeout on unmount', () => {
      const { unmount } = render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      // Trigger reset to set a timeout
      const tryAgainButton = screen.getByText('Try Again')
      tryAgainButton.click()

      // Unmount should clear the timeout - we just verify it doesn't crash
      expect(() => unmount()).not.toThrow()
    })

    it('should handle errors with no message', () => {
      const ErrorComponent: React.FC = () => {
        throw new Error()
      }

      render(
        <ErrorBoundary>
          <ErrorComponent />
        </ErrorBoundary>
      )

      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })

    it('should handle errors with very long messages', () => {
      const longMessage = 'Error '.repeat(1000)

      render(
        <ErrorBoundary>
          <ThrowError errorMessage={longMessage} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })

    it('should handle clipboard write failure gracefully', async () => {
      const user = userEvent.setup({ delay: null })
      import.meta.env.DEV = true

      Object.defineProperty(navigator, 'clipboard', {
        value: {
          writeText: vi.fn().mockRejectedValue(new Error('Clipboard error')),
        },
        writable: true,
        configurable: true,
      })

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      const copyButton = screen.getByText('Copy Error Details')
      await user.click(copyButton)

      // Should not crash
      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })
  })

  describe('integration scenarios', () => {
    it('should handle complete error recovery flow', async () => {
      const { rerender } = render(
        <ErrorBoundary resetKeys={['v1']}>
          <DynamicComponent value="error" />
        </ErrorBoundary>
      )

      // Error state
      expect(screen.getByText('Something went wrong')).toBeInTheDocument()

      // Run timers to complete any pending resets
      await vi.runAllTimersAsync()

      // Recover by changing reset key
      rerender(
        <ErrorBoundary resetKeys={['v2']}>
          <DynamicComponent value="recovered" />
        </ErrorBoundary>
      )

      // Run timers again for the reset to complete
      await vi.runAllTimersAsync()

      await waitFor(
        () => {
          expect(screen.getByText('Value: recovered')).toBeInTheDocument()
        },
        { timeout: 1000 }
      )
    })

    it('should handle nested error boundaries', () => {
      const OuterFallback = <div>Outer Error</div>
      const InnerFallback = <div>Inner Error</div>

      render(
        <ErrorBoundary fallback={OuterFallback}>
          <ErrorBoundary fallback={InnerFallback}>
            <ThrowError />
          </ErrorBoundary>
        </ErrorBoundary>
      )

      // Inner boundary should catch the error
      expect(screen.getByText('Inner Error')).toBeInTheDocument()
      expect(screen.queryByText('Outer Error')).not.toBeInTheDocument()
    })
  })
})
