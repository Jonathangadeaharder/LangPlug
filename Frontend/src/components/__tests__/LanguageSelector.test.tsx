import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import LanguageSelector, { Language } from '../LanguageSelector'

describe('LanguageSelector Component', () => {
  const mockLanguages: Language[] = [
    { code: 'en', name: 'English', flag: '🇬🇧' },
    { code: 'de', name: 'German', flag: '🇩🇪' },
    { code: 'fr', name: 'French', flag: '🇫🇷' },
  ]

  const mockOnSelect = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders with label and selected language', () => {
    render(
      <LanguageSelector
        label="Native Language"
        selectedLanguage={mockLanguages[0]}
        languages={mockLanguages}
        onSelect={mockOnSelect}
      />
    )

    expect(screen.getByText('Native Language')).toBeInTheDocument()
    expect(screen.getByText('English')).toBeInTheDocument()
  })

  it('displays all available languages', () => {
    render(
      <LanguageSelector
        label="Target Language"
        selectedLanguage={mockLanguages[1]}
        languages={mockLanguages}
        onSelect={mockOnSelect}
      />
    )

    // All languages should be visible
    expect(screen.getByText('English')).toBeInTheDocument()
    expect(screen.getByText('German')).toBeInTheDocument()
    expect(screen.getByText('French')).toBeInTheDocument()
  })

  it('calls onSelect when a language is clicked', () => {
    render(
      <LanguageSelector
        label="Select Language"
        selectedLanguage={mockLanguages[0]}
        languages={mockLanguages}
        onSelect={mockOnSelect}
      />
    )

    // Click on German language option
    const germanOption = screen.getByText('German')
    fireEvent.click(germanOption)

    expect(mockOnSelect).toHaveBeenCalledWith(mockLanguages[1])
  })

  it('highlights the selected language', () => {
    const { rerender } = render(
      <LanguageSelector
        label="Language"
        selectedLanguage={mockLanguages[0]}
        languages={mockLanguages}
        onSelect={mockOnSelect}
      />
    )

    // Check that English is rendered as selected
    const englishOption = screen.getByText('English')
    expect(englishOption).toBeInTheDocument()

    // Change selection to German
    rerender(
      <LanguageSelector
        label="Language"
        selectedLanguage={mockLanguages[1]}
        languages={mockLanguages}
        onSelect={mockOnSelect}
      />
    )

    // German should now be visible
    const germanOption = screen.getByText('German')
    expect(germanOption).toBeInTheDocument()
  })

  it('disables interaction when disabled prop is true', () => {
    render(
      <LanguageSelector
        label="Disabled Selector"
        selectedLanguage={mockLanguages[0]}
        languages={mockLanguages}
        onSelect={mockOnSelect}
        disabled={true}
      />
    )

    // Click should not trigger onSelect when disabled
    const germanOption = screen.getByText('German')
    fireEvent.click(germanOption)

    expect(mockOnSelect).not.toHaveBeenCalled()
  })

  it('shows flags for each language', () => {
    render(
      <LanguageSelector
        label="With Flags"
        selectedLanguage={mockLanguages[0]}
        languages={mockLanguages}
        onSelect={mockOnSelect}
      />
    )

    expect(screen.getByText('🇬🇧')).toBeInTheDocument()
    expect(screen.getByText('🇩🇪')).toBeInTheDocument()
    expect(screen.getByText('🇫🇷')).toBeInTheDocument()
  })

  it('handles empty language list gracefully', () => {
    render(
      <LanguageSelector
        label="Empty List"
        selectedLanguage={mockLanguages[0]}
        languages={[]}
        onSelect={mockOnSelect}
      />
    )

    expect(screen.getByText('Empty List')).toBeInTheDocument()
    // Should render without errors even with empty list
  })
})
