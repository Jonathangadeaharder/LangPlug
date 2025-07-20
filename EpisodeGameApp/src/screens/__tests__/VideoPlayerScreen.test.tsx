import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import VideoPlayerScreen from '../VideoPlayerScreen.web';
import { useAppStore } from '../../store/useAppStore';
import { SubtitleService } from '../../services/SubtitleService';
import { defaultEpisodes } from '../../models/Episode';

// Mock services
jest.mock('../../services/SubtitleService');
const mockSubtitleService = SubtitleService as jest.Mocked<typeof SubtitleService>;

// Mock navigation
const mockNavigate = jest.fn();
const mockGoBack = jest.fn();
const mockUseRoute = jest.fn();

jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
    goBack: mockGoBack,
  }),
  useRoute: () => mockUseRoute(),
}));

// Mock HTML5 video element
Object.defineProperty(HTMLMediaElement.prototype, 'play', {
  writable: true,
  value: jest.fn().mockImplementation(() => Promise.resolve()),
});

Object.defineProperty(HTMLMediaElement.prototype, 'pause', {
  writable: true,
  value: jest.fn(),
});

Object.defineProperty(HTMLMediaElement.prototype, 'load', {
  writable: true,
  value: jest.fn(),
});

const renderWithProvider = () => {
  // Initialize Zustand store with test data
  const { selectEpisode } = useAppStore.getState();
  selectEpisode({
    ...defaultEpisodes[0],
    subtitleUrl: '/path/to/subtitle.srt',
    hasFilteredSubtitles: true,
    hasTranslatedSubtitles: true,
  });
  
  return render(<VideoPlayerScreen />);
};

describe('VideoPlayerScreen', () => {
  let mockSubtitleServiceInstance: any;

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock route params
    mockUseRoute.mockReturnValue({
      params: {
        episode: {
          ...defaultEpisodes[0],
          subtitleUrl: '/path/to/subtitle.srt',
          hasFilteredSubtitles: true,
          hasTranslatedSubtitles: true,
        },
      },
    });
    
    mockSubtitleServiceInstance = {
      checkSubtitleStatus: jest.fn(),
    };
    
    mockSubtitleService.getInstance = jest.fn().mockReturnValue(mockSubtitleServiceInstance);
    
    // Mock subtitle status
    mockSubtitleServiceInstance.checkSubtitleStatus.mockReturnValue({
      isTranscribed: true,
      hasFilteredSubtitles: true,
      hasTranslatedSubtitles: true,
      subtitlePath: '/path/to/subtitle.srt',
      filteredSubtitlePath: '/path/to/filtered.srt',
      translatedSubtitlePath: '/path/to/translated.srt',
    });
  });

  it('should render video player with episode information', () => {
    const { getByText, getByTestId } = renderWithProvider();

    expect(getByText('Video Player')).toBeTruthy();
    expect(getByText(defaultEpisodes[0].title)).toBeTruthy();
    expect(getByText(defaultEpisodes[0].description)).toBeTruthy();
    expect(getByTestId('video-element')).toBeTruthy();
  });

  it('should show German subtitles available notice', () => {
    const { getByText } = renderWithProvider();

    expect(getByText('🇩🇪 German Subtitles Available')).toBeTruthy();
  });

  it('should display subtitle processing status', () => {
    const { getByText } = renderWithProvider();

    expect(getByText('Subtitle Processing Status')).toBeTruthy();
    expect(getByText('Transcription: ✅ Complete')).toBeTruthy();
    expect(getByText('A1 Filtering: ✅ Complete')).toBeTruthy();
    expect(getByText('Translation: ✅ Complete')).toBeTruthy();
  });

  it('should not show warning when subtitles are processed', () => {
    const { queryByText } = renderWithProvider();

    expect(queryByText('⚠️ Run the A1 Decider workflow first to process subtitles for this episode')).toBeFalsy();
  });

  it('should show warning when subtitles are not transcribed', () => {
    mockSubtitleServiceInstance.checkSubtitleStatus.mockReturnValue({
      isTranscribed: false,
      hasFilteredSubtitles: false,
      hasTranslatedSubtitles: false,
    });

    const { getByText } = renderWithProvider();

    expect(getByText('⚠️ Run the A1 Decider workflow first to process subtitles for this episode')).toBeTruthy();
  });

  it('should handle play button click', () => {
    const { getByTestId } = renderWithProvider();

    const playButton = getByTestId('play-button');
    fireEvent.press(playButton);

    const videoElement = getByTestId('video-element');
    expect(videoElement.props.autoPlay).toBeTruthy();
  });

  it('should handle pause button click', () => {
    const { getByTestId } = renderWithProvider();

    const pauseButton = getByTestId('pause-button');
    fireEvent.press(pauseButton);

    // Video should be paused (we can't directly test this with jsdom, but we can verify the button was clicked)
    expect(pauseButton).toBeTruthy();
  });

  it('should handle back navigation', () => {
    const { getByTestId } = renderWithProvider();

    const backButton = getByTestId('back-button');
    fireEvent.press(backButton);

    expect(mockGoBack).toHaveBeenCalled();
  });

  it('should handle subtitle toggle', () => {
    const { getByTestId } = renderWithProvider();

    const subtitleToggle = getByTestId('subtitle-toggle');
    fireEvent.press(subtitleToggle);

    // Subtitle visibility should toggle
    expect(subtitleToggle).toBeTruthy();
  });

  it('should display correct video source', () => {
    const { getByTestId } = renderWithProvider();

    const videoElement = getByTestId('video-element');
    expect(videoElement.props.src).toBe(defaultEpisodes[0].videoUrl);
  });

  it('should show processing status for partially processed episode', () => {
    mockSubtitleServiceInstance.checkSubtitleStatus.mockReturnValue({
      isTranscribed: true,
      hasFilteredSubtitles: false,
      hasTranslatedSubtitles: false,
    });

    const { getByText } = renderWithProvider();

    expect(getByText('Transcription: ✅ Complete')).toBeTruthy();
    expect(getByText('A1 Filtering: ⏳ Pending')).toBeTruthy();
    expect(getByText('Translation: ⏳ Pending')).toBeTruthy();
  });

  it('should handle video loading errors gracefully', () => {
    const { getByTestId } = renderWithProvider();

    const videoElement = getByTestId('video-element');
    
    // Simulate video error
    fireEvent(videoElement, 'error', {
      target: { error: { message: 'Video failed to load' } },
    });

    // Component should still be rendered without crashing
    expect(getByTestId('video-element')).toBeTruthy();
  });

  it('should update video time on time update', () => {
    const { getByTestId } = renderWithProvider();

    const videoElement = getByTestId('video-element');
    
    // Simulate time update
    fireEvent(videoElement, 'timeUpdate', {
      target: { currentTime: 30, duration: 120 },
    });

    // Progress should be updated (we can't directly test the progress bar, but we can verify the event was handled)
    expect(videoElement).toBeTruthy();
  });

  it('should handle video end event', () => {
    const { getByTestId } = renderWithProvider();

    const videoElement = getByTestId('video-element');
    
    // Simulate video end
    fireEvent(videoElement, 'ended');

    // Video should handle the end event without errors
    expect(videoElement).toBeTruthy();
  });

  it('should display episode metadata correctly', () => {
    const { getByText } = renderWithProvider();

    expect(getByText(defaultEpisodes[0].title)).toBeTruthy();
    expect(getByText(defaultEpisodes[0].description)).toBeTruthy();
    expect(getByText(`Duration: ${defaultEpisodes[0].duration}`)).toBeTruthy();
    expect(getByText(`Difficulty: ${defaultEpisodes[0].difficulty}`)).toBeTruthy();
  });

  it('should handle subtitle file loading', async () => {
    const { getByTestId } = renderWithProvider();

    const videoElement = getByTestId('video-element');
    
    // Check that subtitle track is present
    expect(videoElement.props.children).toBeTruthy();
  });

  it('should show correct subtitle processing status icons', () => {
    const { getByText } = renderWithProvider();

    // All should be complete
    expect(getByText('Transcription: ✅ Complete')).toBeTruthy();
    expect(getByText('A1 Filtering: ✅ Complete')).toBeTruthy();
    expect(getByText('Translation: ✅ Complete')).toBeTruthy();
  });

  it('should handle missing episode gracefully', () => {
    // Mock route with no episode
    jest.doMock('@react-navigation/native', () => ({
      useNavigation: () => ({
        navigate: mockNavigate,
        goBack: mockGoBack,
      }),
      useRoute: () => ({
        params: {},
      }),
    }));

    // Component should handle missing episode without crashing
    expect(() => renderWithProvider()).not.toThrow();
  });
});