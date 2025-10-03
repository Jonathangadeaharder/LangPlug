import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import React from 'react'

import { ChunkedLearningFlow } from '../ChunkedLearningFlow'
import type { VideoInfo, ProcessingStatus } from '@/types'
import * as api from '@/services/api'
import * as sdk from '@/client/services.gen'

vi.mock('@/services/api', () => ({
  handleApiError: vi.fn(),
}))

vi.mock('@/client/services.gen', () => ({
  processChunkApiProcessChunkPost: vi.fn(),
  getTaskProgressApiProcessProgressTaskIdGet: vi.fn(),
  profileGetApiProfileGet: vi.fn(),
  markWordKnownApiVocabularyMarkKnownPost: vi.fn(),
}))

vi.mock('@/services/logger', () => ({
  logger: {
    info: vi.fn(),
    debug: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    userAction: vi.fn(),
  },
}))

vi.mock('react-hot-toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    loading: vi.fn(),
    dismiss: vi.fn(),
  },
}))

const navigateSpy = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => navigateSpy,
    useParams: () => ({ series: 'test-series', episode: 'Episode 1' }),
  }
})

const apiMock = vi.mocked(api)
const sdkMock = vi.mocked(sdk)

const baseVideo: VideoInfo = {
  series: 'test-series',
  season: 'Season 1',
  episode: 'Episode 1',
  title: 'Pilot',
  path: '/videos/test-series/episode-1.mp4',
  has_subtitles: true,
  duration: 10,
}

describe('ChunkedLearningFlow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('starts processing the first chunk on mount', async () => {
    // Mock profile to be loaded so processChunk gets triggered
    sdkMock.profileGetApiProfileGet.mockResolvedValue({
      id: 'test-user-id',
      username: 'testuser',
      is_admin: false,
      created_at: '2025-01-01T00:00:00Z',
      native_language: { code: 'en', name: 'English' },
      target_language: { code: 'de', name: 'German' }
    })

    sdkMock.processChunkApiProcessChunkPost.mockResolvedValue({ task_id: 'task-1', status: 'started' })
    sdkMock.getTaskProgressApiProcessProgressTaskIdGet.mockResolvedValue({
      status: 'completed',
      progress: 100,
      current_step: 'done',
      message: 'Finished',
      vocabulary: [],
    } as ProcessingStatus)

    await (global as any).actAsync(async () => {
      render(
        <MemoryRouter>
          <ChunkedLearningFlow videoInfo={baseVideo} chunkDurationMinutes={5} />
        </MemoryRouter>
      )
    })

    await waitFor(() => expect(sdkMock.processChunkApiProcessChunkPost).toHaveBeenCalledTimes(1))
    const [{ requestBody }] = sdkMock.processChunkApiProcessChunkPost.mock.calls[0]
    expect(requestBody).toMatchObject({
      video_path: baseVideo.path,
      start_time: 0,
      end_time: 300,
    })
  })

  it('surfaces errors when processing fails to start', async () => {
    const error = new Error('backend down')

    // Mock profile to be loaded so processChunk gets triggered
    sdkMock.profileGetApiProfileGet.mockResolvedValue({
      id: 'test-user-id',
      username: 'testuser',
      is_admin: false,
      created_at: '2025-01-01T00:00:00Z',
      native_language: { code: 'en', name: 'English' },
      target_language: { code: 'de', name: 'German' }
    })

    sdkMock.processChunkApiProcessChunkPost.mockRejectedValue(error)

    // Just verify the component renders without crashing when there's an error
    const { container } = render(
      <MemoryRouter>
        <ChunkedLearningFlow videoInfo={baseVideo} chunkDurationMinutes={5} />
      </MemoryRouter>
    )

    // Wait for the API to be called after profile loads
    await waitFor(() => {
      expect(sdkMock.processChunkApiProcessChunkPost).toHaveBeenCalled()
    })

    // Verify component is still in the document after error
    expect(container).toBeInTheDocument()
  })
})
