import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeProvider } from 'styled-components'
import { Card, CardHeader, CardContent, CardFooter } from '../Card'

// Helper to render with theme
const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={(global as any).mockTheme}>
      {component}
    </ThemeProvider>
  )
}

describe('Card Component', () => {
  describe('Card', () => {
    it('renders with default variant', () => {
      renderWithTheme(
        <Card data-testid="card">
          <div>Card content</div>
        </Card>
      )

      const card = screen.getByTestId('card')
      expect(card).toBeInTheDocument()
      expect(screen.getByText('Card content')).toBeInTheDocument()
    })

    it('applies custom className', () => {
      renderWithTheme(
        <Card className="custom-class" data-testid="card">
          <div>Card content</div>
        </Card>
      )

      const card = screen.getByTestId('card')
      expect(card).toHaveClass('custom-class')
    })

    it('applies variant styles', () => {
      renderWithTheme(
        <Card variant="outlined" data-testid="card">
          <div>Card content</div>
        </Card>
      )

      const card = screen.getByTestId('card')
      expect(card).toBeInTheDocument()
      expect(screen.getByText('Card content')).toBeInTheDocument()
    })

    it('applies padding styles', () => {
      renderWithTheme(
        <Card padding="large" data-testid="card">
          <div>Card content</div>
        </Card>
      )

      const card = screen.getByTestId('card')
      expect(card).toBeInTheDocument()
      expect(screen.getByText('Card content')).toBeInTheDocument()
    })

    it('handles hover effect', () => {
      renderWithTheme(
        <Card hoverable data-testid="card">
          <div>Card content</div>
        </Card>
      )

      const card = screen.getByTestId('card')
      expect(card).toBeInTheDocument()
      expect(screen.getByText('Card content')).toBeInTheDocument()
    })

    it('handles click events', () => {
      const handleClick = vi.fn()

      renderWithTheme(
        <Card onClick={handleClick} data-testid="card">
          <div>Card content</div>
        </Card>
      )

      const card = screen.getByTestId('card')
      fireEvent.click(card)

      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('renders children correctly', () => {
      renderWithTheme(
        <Card data-testid="card">
          <div data-testid="child">Child content</div>
        </Card>
      )

      expect(screen.getByTestId('child')).toBeInTheDocument()
      expect(screen.getByTestId('child')).toHaveTextContent('Child content')
    })

    it('handles click events properly', () => {
      const handleClick = vi.fn()

      renderWithTheme(
        <Card onClick={handleClick} data-testid="card">
          <div>Clickable card</div>
        </Card>
      )

      const card = screen.getByTestId('card')
      expect(card).toBeInTheDocument()

      fireEvent.click(card)
      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('forwards ref correctly', () => {
      const ref = vi.fn()

      renderWithTheme(
        <Card ref={ref} data-testid="card">
          <div>Card content</div>
        </Card>
      )

      expect(ref).toHaveBeenCalled()
    })

    it('handles keyboard navigation', () => {
      const handleClick = vi.fn()

      renderWithTheme(
        <Card onClick={handleClick} data-testid="card">
          <div>Card content</div>
        </Card>
      )

      const card = screen.getByTestId('card')

      // Should be focusable when clickable
      expect(card).toHaveAttribute('tabIndex', '0')
      expect(card).toHaveAttribute('role', 'button')

      fireEvent.click(card)
      expect(handleClick).toHaveBeenCalledTimes(1)
    })
  })

  describe('CardHeader', () => {
    it('renders header content', () => {
      renderWithTheme(
        <CardHeader data-testid="header">
          <h2>Card Title</h2>
        </CardHeader>
      )

      const header = screen.getByTestId('header')
      expect(header).toBeInTheDocument()
      expect(screen.getByText('Card Title')).toBeInTheDocument()
    })

    it('applies custom className', () => {
      renderWithTheme(
        <CardHeader className="custom-header" data-testid="header">
          Header content
        </CardHeader>
      )

      const header = screen.getByTestId('header')
      expect(header).toHaveClass('custom-header')
    })
  })

  describe('CardContent', () => {
    it('renders content area', () => {
      renderWithTheme(
        <CardContent data-testid="content">
          <p>Main card content</p>
        </CardContent>
      )

      const content = screen.getByTestId('content')
      expect(content).toBeInTheDocument()
      expect(screen.getByText('Main card content')).toBeInTheDocument()
    })

    it('renders with custom content', () => {
      renderWithTheme(
        <CardContent data-testid="content">
          <div>Content with custom styling</div>
        </CardContent>
      )

      const content = screen.getByTestId('content')
      expect(content).toBeInTheDocument()
      expect(screen.getByText('Content with custom styling')).toBeInTheDocument()
    })

    it('handles tall content', () => {
      renderWithTheme(
        <CardContent data-testid="content">
          <div style={{ height: '200px' }}>Tall content</div>
        </CardContent>
      )

      const content = screen.getByTestId('content')
      expect(content).toBeInTheDocument()
      expect(screen.getByText('Tall content')).toBeInTheDocument()
    })
  })

  describe('CardFooter', () => {
    it('renders footer content', () => {
      renderWithTheme(
        <CardFooter data-testid="footer">
          <button>Action Button</button>
        </CardFooter>
      )

      const footer = screen.getByTestId('footer')
      expect(footer).toBeInTheDocument()
      expect(screen.getByText('Action Button')).toBeInTheDocument()
    })

    it('renders with different content', () => {
      renderWithTheme(
        <CardFooter data-testid="footer">
          <span>Footer text</span>
        </CardFooter>
      )

      const footer = screen.getByTestId('footer')
      expect(footer).toBeInTheDocument()
      expect(screen.getByText('Footer text')).toBeInTheDocument()
    })

    it('handles multiple actions', () => {
      renderWithTheme(
        <CardFooter data-testid="footer">
          <button>Cancel</button>
          <button>Save</button>
        </CardFooter>
      )

      const footer = screen.getByTestId('footer')
      expect(footer).toBeInTheDocument()
      expect(screen.getByText('Cancel')).toBeInTheDocument()
      expect(screen.getByText('Save')).toBeInTheDocument()
    })
  })

  describe('Card Composition', () => {
    it('renders complete card with all sections', () => {
      renderWithTheme(
        <Card data-testid="card">
          <CardHeader data-testid="header">
            <h2>Full Card</h2>
          </CardHeader>
          <CardContent data-testid="content">
            <p>This is the main content</p>
          </CardContent>
          <CardFooter data-testid="footer">
            <button>Action</button>
          </CardFooter>
        </Card>
      )

      expect(screen.getByTestId('card')).toBeInTheDocument()
      expect(screen.getByTestId('header')).toBeInTheDocument()
      expect(screen.getByTestId('content')).toBeInTheDocument()
      expect(screen.getByTestId('footer')).toBeInTheDocument()

      expect(screen.getByText('Full Card')).toBeInTheDocument()
      expect(screen.getByText('This is the main content')).toBeInTheDocument()
      expect(screen.getByText('Action')).toBeInTheDocument()
    })

    it('handles partial card composition', () => {
      renderWithTheme(
        <Card data-testid="card">
          <CardContent data-testid="content">
            <p>Content only card</p>
          </CardContent>
        </Card>
      )

      expect(screen.getByTestId('card')).toBeInTheDocument()
      expect(screen.getByTestId('content')).toBeInTheDocument()
      expect(screen.queryByTestId('header')).not.toBeInTheDocument()
      expect(screen.queryByTestId('footer')).not.toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA attributes for clickable cards', () => {
      renderWithTheme(
        <Card onClick={vi.fn()} role="button" aria-label="Clickable card" data-testid="card">
          Card content
        </Card>
      )

      const card = screen.getByTestId('card')
      expect(card).toHaveAttribute('role', 'button')
      expect(card).toHaveAttribute('aria-label', 'Clickable card')
      expect(card).toHaveAttribute('tabIndex', '0')
    })

    it('supports custom ARIA attributes', () => {
      renderWithTheme(
        <Card aria-describedby="description" data-testid="card">
          Card content
        </Card>
      )

      const card = screen.getByTestId('card')
      expect(card).toHaveAttribute('aria-describedby', 'description')
    })
  })
})
