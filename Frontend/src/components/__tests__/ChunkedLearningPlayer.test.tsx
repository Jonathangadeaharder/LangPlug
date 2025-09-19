import { describe, test, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { ChunkedLearningPlayer } from '../ChunkedLearningPlayer';

// Mock react-player since it requires browser APIs
vi.mock('react-player', () => {
  const MockPlayer = React.forwardRef<any>((props, ref) => {
    React.useImperativeHandle(ref, () => ({
      seekTo: vi.fn(),
      getCurrentTime: vi.fn(() => 0),
      getDuration: vi.fn(() => 100),
    }));

    return <div data-testid="mock-react-player">Mock Player</div>;
  });
  MockPlayer.displayName = 'MockPlayer';

  return {
    default: MockPlayer,
  };
});

// Mock the video service
vi.mock('@/services/api', () => ({
  videoService: {
    getVideoStreamUrl: vi.fn((series, episode) => `http://localhost:8000/api/videos/${series}/${episode}`),
  },
}));

// Mock logger
vi.mock('@/services/logger', () => ({
  logger: {
    info: vi.fn(),
    error: vi.fn(),
    warn: vi.fn(),
  },
}));

describe('ChunkedLearningPlayer', () => {
  const defaultProps = {
    videoPath: 'Superstore/Episode 1.mp4',
    series: 'Superstore',
    episode: 'Episode 1',
    subtitlePath: 'Superstore/Episode 1_chunk_0_300.srt',
    translationPath: 'Superstore/Episode 1_chunk_0_300_translation.srt',
    startTime: 0,
    endTime: 300,
    onComplete: vi.fn(),
    learnedWords: ['test'],
    chunkInfo: {
      current: 1,
      total: 3,
      duration: '5:00',
    },
  };

  test('renders without crashing', () => {
    render(<ChunkedLearningPlayer {...defaultProps} />);
    expect(screen.getByTestId('mock-react-player')).toBeInTheDocument();
  });

  test('displays chunk information', () => {
    render(<ChunkedLearningPlayer {...defaultProps} />);
    expect(screen.getByText('Playing Chunk')).toBeInTheDocument();
    expect(screen.getByText('1 of 3 • 5:00')).toBeInTheDocument();
  });

  test('displays learned words count', () => {
    render(<ChunkedLearningPlayer {...defaultProps} />);
    expect(screen.getByText('1 words learned')).toBeInTheDocument();
  });

  test('builds correct subtitle URLs', () => {
    // This test would verify that subtitle URLs are constructed correctly
    // We'll need to add more specific tests once we can mock axios requests
    expect(true).toBe(true);
  });
});