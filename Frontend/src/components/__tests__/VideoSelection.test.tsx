import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { VideoSelection } from '../VideoSelection';
import * as api from '@/services/api';
import { assertLoadingState, assertNavigationCalled, assertErrorMessage } from '@/test/assertion-helpers';

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const mockVideos = [
  {
    series: 'Superstore',
    season: '01',
    episode: '01',
    title: 'Pilot',
    path: '/videos/superstore/s01e01.mp4',
    has_subtitles: true,
    duration: 1800,
  },
  {
    series: 'Superstore',
    season: '01',
    episode: '02',
    title: 'Magazine Profile',
    path: '/videos/superstore/s01e02.mp4',
    has_subtitles: false,
    duration: 1850,
  },
];

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true
      }}
    >
      {component}
    </BrowserRouter>
  );
};

describe('VideoSelection Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(api.videoService, 'getVideos').mockResolvedValue(mockVideos as any);
  });

  it('WhenComponentRendered_ThenDisplaysHeroTitle', async () => {
    await act(async () => {
      renderWithRouter(<VideoSelection />);
    });
    expect(screen.getByText(/learn german through tv shows/i)).toBeInTheDocument();
  });

  it('WhenComponentMounts_ThenShowsLoadingState', () => {
    renderWithRouter(<VideoSelection />);
    assertLoadingState();
  });

  it('WhenDataLoaded_ThenDisplaysSeries', async () => {
    await act(async () => {
      renderWithRouter(<VideoSelection />);
    });

    await waitFor(() => {
      expect(screen.getByText('Superstore')).toBeInTheDocument();
    });
  });

  it('WhenSeriesClicked_ThenNavigatesToEpisodes', async () => {
    await act(async () => {
      renderWithRouter(<VideoSelection />);
    });

    await waitFor(() => {
      expect(screen.getByText('Superstore')).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByText('Superstore'));
    });
    assertNavigationCalled(mockNavigate, '/episodes/Superstore');
  });

  it('WhenApiErrorOccurs_ThenHandlesErrorGracefully', async () => {
    vi.spyOn(api.videoService, 'getVideos').mockRejectedValue(new Error('API Error'));
    // Mock handleApiError to prevent it from throwing in tests
    vi.spyOn(api, 'handleApiError').mockImplementation(() => {});

    await act(async () => {
      renderWithRouter(<VideoSelection />);
    });

    await waitFor(() => {
      // Should not be in loading state after error
      expect(document.querySelector('.loading-spinner')).toBeNull();
      // Should show error message
      expect(screen.getByText('Failed to load videos')).toBeInTheDocument();
    }, { timeout: 5000 });
  });
});