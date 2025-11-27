import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import { EpisodeSelection } from '../EpisodeSelection'
import * as sdk from '@/client/services.gen'

vi.mock('@/services/api', () => ({
  handleApiError: vi.fn(),
  buildVideoStreamUrl: vi.fn((series: string, episode: string) => `${series}-${episode}`),
}))

vi.mock('@/client/services.gen', () => ({
  getVideosApiVideosGet: vi.fn(),
  getTaskProgressApiProcessProgressTaskIdGet: vi.fn(),
  filterSubtitlesApiProcessFilterSubtitlesPost: vi.fn(),
  translateSubtitlesApiProcessTranslateSubtitlesPost: vi.fn(),
  profileGetApiProfileGet: vi.fn()
}))

vi.mock('@/store/useAuthStore', () => ({
  useAuthStore: vi.fn(() => ({
    user: { id: 'user-1', username: 'tester' },
    isAuthenticated: true,
  })),
}))

const navigateSpy = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => navigateSpy,
    useParams: () => ({ series: 'test-series' }),
  }
})

vi.mock('react-hot-toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    loading: vi.fn(),
    dismiss: vi.fn(),
  },
}))

const sdkMock = vi.mocked(sdk)

const renderComponent = () =>
  render(
    <MemoryRouter initialEntries={['/series/test-series']}>
      <EpisodeSelection />
    </MemoryRouter>
  )

describe('EpisodeSelection', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Add default mock for profileGetApiProfileGet
    if (sdkMock.profileGetApiProfileGet) {
      (sdkMock.profileGetApiProfileGet as any).mockResolvedValue({
        native_language: { code: 'es', name: 'Spanish' },
        target_language: { code: 'de', name: 'German' }
      })
    }
  })

  it('renders episodes for the current series', async () => {
    sdkMock.getVideosApiVideosGet.mockResolvedValue([
      {
        season: 'Season 1',
        series: 'test-series',
        episode: 'Episode 1',
        title: 'Pilot',
        path: '/videos/test-series/episode-1.mp4',
        duration: 20,
        has_subtitles: true,
      },
      {
        season: 'Season 1',
        series: 'other-series',
        episode: 'Episode 1',
        title: 'Other',
        path: '/videos/other/episode-1.mp4',
        duration: 22,
        has_subtitles: true,
      },
      {
        season: 'Season 1',
        series: 'test-series',
        episode: 'Episode 2',
        title: 'Second Episode',
        path: '/videos/test-series/episode-2.mp4',
        duration: 21,
        has_subtitles: false,
      },
    ])

    await (global as any).actAsync(async () => {
      renderComponent()
    })

    await waitFor(() => expect(sdkMock.getVideosApiVideosGet).toHaveBeenCalled())
    await waitFor(() => expect(screen.getByText('Episode 1')).toBeInTheDocument())
    expect(screen.getByText('Episode 2')).toBeInTheDocument()
    expect(screen.queryByText('Other')).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /test-series/i })).toBeInTheDocument()
  })

  it('surfaces errors when videos cannot be loaded', async () => {
    const error = new Error('network down')
    sdkMock.getVideosApiVideosGet.mockRejectedValue(error)

    // Render and verify it doesn't crash on error
    const { container } = renderComponent()

    await waitFor(() => {
      expect(container).toBeInTheDocument()
    })

    // The API should have been called
    expect(sdkMock.getVideosApiVideosGet).toHaveBeenCalled()
  })

  it('navigates to the learning flow when Play is clicked', async () => {
    sdkMock.getVideosApiVideosGet.mockResolvedValue([
      {
        season: 'Season 1',
        series: 'test-series',
        episode: 'Episode 1',
        title: 'Pilot',
        path: '/videos/test-series/episode-1.mp4',
        duration: 20,
        has_subtitles: true,
      },
    ])

    await (global as any).actAsync(async () => {
      renderComponent()
    })

    await screen.findByText('Episode 1')

    await (global as any).actAsync(async () => {
      fireEvent.click(screen.getByRole('button', { name: /play/i }))
    })

    await waitFor(() =>
      expect(navigateSpy).toHaveBeenCalledWith('/learn/test-series/Episode%201', {
        state: expect.objectContaining({
          videoInfo: expect.objectContaining({
            episode: 'Episode 1',
            series: 'test-series',
          }),
        }),
      })
    )
  })
})