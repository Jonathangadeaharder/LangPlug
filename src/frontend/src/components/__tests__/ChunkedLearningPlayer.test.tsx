import { describe, test, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import React from 'react'
import { ChunkedLearningPlayer } from '../ChunkedLearningPlayer'

// Mock react-player since it requires browser APIs
vi.mock('react-player', () => {
  const MockPlayer = React.forwardRef<any>((props, ref) => {
    React.useImperativeHandle(ref, () => ({
      seekTo: vi.fn(),
      getCurrentTime: vi.fn(() => 0),
      getDuration: vi.fn(() => 100),
    }))

    return <div data-testid="mock-react-player">Mock Player</div>
  })
  MockPlayer.displayName = 'MockPlayer'

  return {
    default: MockPlayer,
  }
})

// Mock the video helper
vi.mock('@/services/api', () => ({
  buildVideoStreamUrl: vi.fn(
    (series: string, episode: string) => `http://localhost:8000/api/videos/${series}/${episode}`
  ),
}))

// Mock logger
vi.mock('@/services/logger', () => ({
  logger: {
    info: vi.fn(),
    error: vi.fn(),
    warn: vi.fn(),
    debug: vi.fn(),
  },
}))

const createProps = (
  overrides: Partial<React.ComponentProps<typeof ChunkedLearningPlayer>> = {}
) => ({
  videoPath: 'Superstore/Episode 1.mp4',
  series: 'Superstore',
  episode: 'Episode 1',
  subtitlePath: 'Superstore/Episode 1_chunk_0_300.srt',
  translationPath: 'Superstore/Episode 1_chunk_0_300_translation.srt',
  startTime: 0,
  endTime: 300,
  onComplete: vi.fn(),
  onSkipChunk: vi.fn(),
  onBack: vi.fn(),
  learnedWords: ['test'],
  chunkInfo: {
    current: 1,
    total: 3,
    duration: '5:00',
  },
  ...overrides,
})

describe('ChunkedLearningPlayer', () => {
  test('renders without crashing', () => {
    render(<ChunkedLearningPlayer {...createProps()} />)
    expect(screen.getByTestId('mock-react-player')).toBeInTheDocument()
  })

  test('displays chunk information', () => {
    render(<ChunkedLearningPlayer {...createProps()} />)
    // Use getAllByText because "Chunk 1/3" appears in both desktop and mobile views (via styled components)
    const chunkInfoElements = screen.getAllByText((content, element) => {
      return element?.textContent === 'Chunk 1/3'
    })
    expect(chunkInfoElements.length).toBeGreaterThan(0)
    expect(chunkInfoElements[0]).toBeInTheDocument()
  })

  test('displays learned words count', () => {
    render(<ChunkedLearningPlayer {...createProps()} />)
    const learnedElements = screen.getAllByText('1 learned')
    expect(learnedElements.length).toBeGreaterThan(0)
    expect(learnedElements[0]).toBeInTheDocument()
  })

  test('invokes onBack when back button is clicked', () => {
    const onBack = vi.fn()
    render(<ChunkedLearningPlayer {...createProps({ onBack })} />)
    fireEvent.click(screen.getByRole('button', { name: /back to episodes/i }))
    expect(onBack).toHaveBeenCalled()
  })

  test('invokes onSkipChunk when next button is clicked', () => {
    const onSkipChunk = vi.fn()
    render(<ChunkedLearningPlayer {...createProps({ onSkipChunk })} />)
    const skipButtons = screen.getAllByRole('button', { name: /skip/i })
    fireEvent.click(skipButtons[0])
    expect(onSkipChunk).toHaveBeenCalled()
  })
})
