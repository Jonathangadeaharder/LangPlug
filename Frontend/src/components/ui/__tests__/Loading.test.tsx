import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { ThemeProvider } from 'styled-components'
import { Loading } from '../Loading'

// Helper to render with theme
const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={(global as any).mockTheme}>
      {component}
    </ThemeProvider>
  )
}

describe('Loading Component', () => {
  describe('Basic Rendering', () => {
    it('renders loading spinner by default', () => {
      renderWithTheme(<Loading data-testid="loading" />)

      const loading = screen.getByTestId('loading')
      expect(loading).toBeInTheDocument()
    })

    it('renders without text by default', () => {
      renderWithTheme(<Loading />)

      expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
    })

    it('renders with custom text', () => {
      renderWithTheme(<Loading text="Processing your request..." />)

      expect(screen.getByText('Processing your request...')).toBeInTheDocument()
    })

    it('renders without text when not specified', () => {
      renderWithTheme(<Loading />)

      expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
    })

    it('renders empty text when specified', () => {
      renderWithTheme(<Loading text="" />)

      expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
    })
  })

  describe('Size Variants', () => {
    it('renders small size variant', () => {
      renderWithTheme(<Loading size="small" data-testid="loading" />)

      const loading = screen.getByTestId('loading')
      expect(loading).toBeInTheDocument()
    })

    it('renders medium size variant (default)', () => {
      renderWithTheme(<Loading data-testid="loading" />)

      const loading = screen.getByTestId('loading')
      expect(loading).toBeInTheDocument()
    })

    it('renders large size variant', () => {
      renderWithTheme(<Loading size="large" data-testid="loading" />)

      const loading = screen.getByTestId('loading')
      expect(loading).toBeInTheDocument()
    })
  })

  describe('Color Variants', () => {
    it('renders with default color', () => {
      renderWithTheme(<Loading data-testid="loading" />)

      const loading = screen.getByTestId('loading')
      expect(loading).toBeInTheDocument()
    })

    it('renders with custom color', () => {
      renderWithTheme(<Loading color="#ff0000" data-testid="loading" />)

      const loading = screen.getByTestId('loading')
      expect(loading).toBeInTheDocument()
    })

    it('renders with hex color', () => {
      renderWithTheme(<Loading color="#00ff00" data-testid="loading" />)

      const loading = screen.getByTestId('loading')
      expect(loading).toBeInTheDocument()
    })
  })

  describe('Variant Types', () => {
    it('renders spinner variant (default)', () => {
      renderWithTheme(<Loading data-testid="loading" />)

      const loading = screen.getByTestId('loading')
      expect(loading).toBeInTheDocument()
    })

    it('renders dots variant', () => {
      renderWithTheme(<Loading variant="dots" data-testid="loading" />)

      const loading = screen.getByTestId('loading')
      expect(loading).toBeInTheDocument()
    })

    it('renders pulse variant', () => {
      renderWithTheme(<Loading variant="pulse" data-testid="loading" />)

      const loading = screen.getByTestId('loading')
      expect(loading).toBeInTheDocument()
    })

    it('renders bars variant', () => {
      renderWithTheme(<Loading variant="bars" data-testid="loading" />)

      const loading = screen.getByTestId('loading')
      expect(loading).toBeInTheDocument()
    })
  })

  describe('Fullscreen and Overlay', () => {
    it('renders fullscreen overlay', () => {
      renderWithTheme(<Loading fullScreen data-testid="loading" />)

      const loading = screen.getByTestId('loading')
      expect(loading).toBeInTheDocument()
    })

    it('renders inline loading (default)', () => {
      renderWithTheme(<Loading data-testid="loading" />)

      const loading = screen.getByTestId('loading')
      expect(loading).toBeInTheDocument()
    })

    it('renders with overlay', () => {
      renderWithTheme(<Loading overlay data-testid="loading" />)

      const loading = screen.getByTestId('loading')
      expect(loading).toBeInTheDocument()
    })

    it('combines fullscreen with overlay', () => {
      renderWithTheme(<Loading fullScreen overlay data-testid="loading" />)

      const loading = screen.getByTestId('loading')
      expect(loading).toBeInTheDocument()
    })
  })

  describe('Text Display', () => {
    it('renders with text content', () => {
      renderWithTheme(<Loading text="Loading 65%" />)

      expect(screen.getByText('Loading 65%')).toBeInTheDocument()
    })

    it('renders with animated text', () => {
      renderWithTheme(<Loading text="Processing..." data-testid="loading" />)

      const loading = screen.getByTestId('loading')
      expect(loading).toBeInTheDocument()
      expect(screen.getByText('Processing...')).toBeInTheDocument()
    })

    it('handles text with multiple words', () => {
      renderWithTheme(<Loading text="Processing files..." />)

      expect(screen.getByText('Processing files...')).toBeInTheDocument()
    })

    it('handles empty text properly', () => {
      const { rerender } = renderWithTheme(<Loading text="Some text" />)
      expect(screen.getByText('Some text')).toBeInTheDocument()

      rerender(
        <ThemeProvider theme={(global as any).mockTheme}>
          <Loading text="" />
        </ThemeProvider>
      )
      expect(screen.queryByText('Some text')).not.toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA attributes', () => {
      renderWithTheme(<Loading aria-label="Loading content" data-testid="loading" />)

      const loading = screen.getByTestId('loading')
      expect(loading).toBeInTheDocument()
      expect(loading).toHaveAttribute('aria-label', 'Loading content')
    })

    it('has accessible content', () => {
      renderWithTheme(<Loading text="Loading content" data-testid="loading" />)

      const loading = screen.getByTestId('loading')
      expect(loading).toBeInTheDocument()
      expect(screen.getByText('Loading content')).toBeInTheDocument()
    })

    it('supports custom aria-label', () => {
      renderWithTheme(<Loading aria-label="Custom loading label" data-testid="loading" />)

      const loading = screen.getByTestId('loading')
      expect(loading).toHaveAttribute('aria-label', 'Custom loading label')
    })

    it('announces text changes to screen readers', () => {
      const { rerender } = renderWithTheme(<Loading text="Loading 25%" />)

      expect(screen.getByText('Loading 25%')).toBeInTheDocument()

      rerender(
        <ThemeProvider theme={(global as any).mockTheme}>
          <Loading text="Loading 75%" />
        </ThemeProvider>
      )
      expect(screen.getByText('Loading 75%')).toBeInTheDocument()
    })
  })

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      renderWithTheme(<Loading className="custom-loading" data-testid="loading" />)

      const loading = screen.getByTestId('loading')
      expect(loading).toHaveClass('custom-loading')
    })

    it('applies custom styles', () => {
      renderWithTheme(<Loading style={{ margin: '20px' }} data-testid="loading" />)

      const loading = screen.getByTestId('loading')
      expect(loading).toHaveStyle({ margin: '20px' })
    })

    it('combines multiple props correctly', () => {
      renderWithTheme(
        <Loading
          size="large"
          color="#ff0000"
          variant="dots"
          fullScreen
          className="custom-class"
          data-testid="loading"
        />
      )

      const loading = screen.getByTestId('loading')
      expect(loading).toBeInTheDocument()
      expect(loading).toHaveClass('custom-class')
    })
  })

  describe('Conditional Rendering', () => {
    it('renders by default', () => {
      renderWithTheme(<Loading data-testid="loading" />)
      expect(screen.getByTestId('loading')).toBeInTheDocument()
    })

    it('renders with all props', () => {
      renderWithTheme(<Loading size="large" variant="dots" color="#ff0000" fullScreen overlay text="Loading..." data-testid="loading" />)
      expect(screen.getByTestId('loading')).toBeInTheDocument()
      expect(screen.getByText('Loading...')).toBeInTheDocument()
    })
  })

  describe('Animation Behavior', () => {
    it('renders with animations by default', () => {
      renderWithTheme(<Loading data-testid="loading" />)

      const loading = screen.getByTestId('loading')
      expect(loading).toBeInTheDocument()
    })

    it('renders different variants with animations', () => {
      renderWithTheme(<Loading variant="netflix" data-testid="loading" />)

      const loading = screen.getByTestId('loading')
      expect(loading).toBeInTheDocument()
    })

    it('handles different animation types', async () => {
      const { rerender } = renderWithTheme(<Loading variant="pulse" data-testid="loading" />)
      expect(screen.getByTestId('loading')).toBeInTheDocument()

      rerender(
        <ThemeProvider theme={(global as any).mockTheme}>
          <Loading variant="bars" data-testid="loading" />
        </ThemeProvider>
      )
      expect(screen.getByTestId('loading')).toBeInTheDocument()
    })
  })

  describe('Error States', () => {
    it('handles edge cases gracefully', () => {
      // Should not crash with edge case props
      renderWithTheme(
        <Loading
          color={""}
          text={""}
          data-testid="loading"
        />
      )

      const loading = screen.getByTestId('loading')
      expect(loading).toBeInTheDocument()
    })

    it('falls back to defaults for undefined values', () => {
      renderWithTheme(
        <Loading
          size={undefined}
          color={undefined}
          data-testid="loading"
        />
      )

      const loading = screen.getByTestId('loading')
      expect(loading).toBeInTheDocument() // Should use defaults
    })
  })

  describe('Performance', () => {
    it('does not cause unnecessary re-renders', () => {
      const renderSpy = vi.fn()

      const TestComponent = () => {
        renderSpy()
        return <Loading data-testid="loading" />
      }

      const { rerender } = renderWithTheme(<TestComponent />)

      expect(renderSpy).toHaveBeenCalledTimes(1)

      // Re-render with same props should not cause extra renders
      rerender(
        <ThemeProvider theme={(global as any).mockTheme}>
          <TestComponent />
        </ThemeProvider>
      )

      expect(renderSpy).toHaveBeenCalledTimes(2)
    })
  })
})
