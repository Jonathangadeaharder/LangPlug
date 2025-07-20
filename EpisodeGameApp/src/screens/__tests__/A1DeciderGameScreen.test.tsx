import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { Alert } from 'react-native';
import A1DeciderGameScreen from '../A1DeciderGameScreen';
import { GlobalStateProvider } from '../../context/GlobalStateProvider';
import { SubtitleService } from '../../services/SubtitleService';
import { defaultEpisodes } from '../../models/Episode';

// Mock services
jest.mock('../../services/SubtitleService');
jest.mock('react-native', () => ({
  ...jest.requireActual('react-native'),
  Alert: {
    alert: jest.fn(),
  },
}));

const mockSubtitleService = SubtitleService as jest.Mocked<typeof SubtitleService>;
const mockAlert = Alert.alert as jest.MockedFunction<typeof Alert.alert>;

// Mock navigation
const mockNavigate = jest.fn();
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
  }),
  useRoute: () => ({
    params: {
      episode: defaultEpisodes[0],
    },
  }),
}));

const renderWithProvider = () => {
  return render(
    <GlobalStateProvider>
      <A1DeciderGameScreen />
    </GlobalStateProvider>
  );
};

describe('A1DeciderGameScreen', () => {
  let mockSubtitleServiceInstance: any;

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockSubtitleServiceInstance = {
      processEpisodeSimulated: jest.fn(),
      loadRealVocabulary: jest.fn(),
    };
    
    mockSubtitleService.getInstance = jest.fn().mockReturnValue(mockSubtitleServiceInstance);
    
    // Mock vocabulary data
    mockSubtitleServiceInstance.loadRealVocabulary.mockResolvedValue([
      {
        word: 'schwierig',
        translation: 'difficult',
        frequency: 5,
        isRelevant: true,
        affectedSubtitles: 3,
      },
      {
        word: 'kompliziert',
        translation: 'complicated',
        frequency: 3,
        isRelevant: true,
        affectedSubtitles: 2,
      },
    ]);
    
    // Mock processing result
    mockSubtitleServiceInstance.processEpisodeSimulated.mockImplementation(
      (episode: any, onProgress: any) => {
        // Simulate progress updates
        setTimeout(() => onProgress({ stage: 'transcription', progress: 25, message: 'Transcribing...' }), 100);
        setTimeout(() => onProgress({ stage: 'filtering', progress: 50, message: 'Filtering...' }), 200);
        setTimeout(() => onProgress({ stage: 'translation', progress: 75, message: 'Translating...' }), 300);
        setTimeout(() => onProgress({ stage: 'complete', progress: 100, message: 'Complete!' }), 400);
        
        return Promise.resolve({
          isTranscribed: true,
          hasFilteredSubtitles: true,
          hasTranslatedSubtitles: true,
        });
      }
    );
  });

  it('should render initial processing screen', () => {
    const { getByText } = renderWithProvider();

    expect(getByText('A1 Decider Game')).toBeTruthy();
    expect(getByText('Processing Episode')).toBeTruthy();
    expect(getByText(defaultEpisodes[0].title)).toBeTruthy();
  });

  it('should show processing progress', async () => {
    const { getByText } = renderWithProvider();

    await waitFor(() => {
      expect(getByText('Transcription: ✅ Complete')).toBeTruthy();
    }, { timeout: 5000 });
  });

  it('should transition to vocabulary check after processing', async () => {
    const { getByText, queryByText } = renderWithProvider();

    await waitFor(() => {
      expect(queryByText('Processing Episode')).toBeFalsy();
      expect(getByText('Vocabulary Check')).toBeTruthy();
    }, { timeout: 6000 });
  });

  it('should handle word knowledge selection', async () => {
    const { getByText, getByTestId } = renderWithProvider();

    // Wait for vocabulary check phase
    await waitFor(() => {
      expect(getByText('Vocabulary Check')).toBeTruthy();
    }, { timeout: 6000 });

    // Should show first word
    expect(getByText('schwierig')).toBeTruthy();
    expect(getByText('difficult')).toBeTruthy();

    // Click "I know this word"
    const knowButton = getByTestId('know-word-button');
    fireEvent.press(knowButton);

    // Should move to next word
    await waitFor(() => {
      expect(getByText('kompliziert')).toBeTruthy();
    });
  });

  it('should handle word skip', async () => {
    const { getByText, getByTestId } = renderWithProvider();

    // Wait for vocabulary check phase
    await waitFor(() => {
      expect(getByText('Vocabulary Check')).toBeTruthy();
    }, { timeout: 6000 });

    // Click "Skip"
    const skipButton = getByTestId('skip-word-button');
    fireEvent.press(skipButton);

    // Should move to next word
    await waitFor(() => {
      expect(getByText('kompliziert')).toBeTruthy();
    });
  });

  it('should complete vocabulary check and show summary', async () => {
    const { getByText, getByTestId } = renderWithProvider();

    // Wait for vocabulary check phase
    await waitFor(() => {
      expect(getByText('Vocabulary Check')).toBeTruthy();
    }, { timeout: 6000 });

    // Go through all words
    const knowButton = getByTestId('know-word-button');
    
    // First word
    fireEvent.press(knowButton);
    
    // Second word (last word)
    await waitFor(() => {
      expect(getByText('kompliziert')).toBeTruthy();
    });
    fireEvent.press(knowButton);

    // Should show completion alert
    await waitFor(() => {
      expect(mockAlert).toHaveBeenCalledWith(
        'Vocabulary Check Complete!',
        expect.stringContaining('You knew'),
        expect.arrayContaining([
          expect.objectContaining({ text: 'Watch Video' }),
          expect.objectContaining({ text: 'View Results' }),
        ])
      );
    });
  });

  it('should handle watch video navigation', async () => {
    const { getByText, getByTestId } = renderWithProvider();

    // Complete vocabulary check
    await waitFor(() => {
      expect(getByText('Vocabulary Check')).toBeTruthy();
    }, { timeout: 6000 });

    const knowButton = getByTestId('know-word-button');
    fireEvent.press(knowButton);
    
    await waitFor(() => {
      expect(getByText('kompliziert')).toBeTruthy();
    });
    fireEvent.press(knowButton);

    // Simulate pressing "Watch Video" in alert
    await waitFor(() => {
      expect(mockAlert).toHaveBeenCalled();
    });

    // Get the alert call and simulate pressing "Watch Video"
    const alertCall = mockAlert.mock.calls[0];
    const watchVideoButton = alertCall[2]?.find((button: any) => button.text === 'Watch Video');
    
    act(() => {
      watchVideoButton?.onPress();
    });

    expect(mockNavigate).toHaveBeenCalledWith('VideoPlayer', {
      episode: defaultEpisodes[0],
    });
  });

  it('should handle view results navigation', async () => {
    const { getByText, getByTestId } = renderWithProvider();

    // Complete vocabulary check
    await waitFor(() => {
      expect(getByText('Vocabulary Check')).toBeTruthy();
    }, { timeout: 6000 });

    const knowButton = getByTestId('know-word-button');
    fireEvent.press(knowButton);
    
    await waitFor(() => {
      expect(getByText('kompliziert')).toBeTruthy();
    });
    fireEvent.press(knowButton);

    // Simulate pressing "View Results" in alert
    await waitFor(() => {
      expect(mockAlert).toHaveBeenCalled();
    });

    const alertCall = mockAlert.mock.calls[0];
    const viewResultsButton = alertCall[2]?.find((button: any) => button.text === 'View Results');
    
    act(() => {
      viewResultsButton?.onPress();
    });

    expect(mockNavigate).toHaveBeenCalledWith('GameResults', {
      episode: defaultEpisodes[0],
      knownWords: ['schwierig', 'kompliziert'],
      unknownWords: [],
    });
  });

  it('should handle processing errors', async () => {
    mockSubtitleServiceInstance.processEpisodeSimulated.mockRejectedValue(
      new Error('Processing failed')
    );

    const { getByText } = renderWithProvider();

    await waitFor(() => {
      expect(getByText('Error processing episode')).toBeTruthy();
    }, { timeout: 2000 });
  });

  it('should handle vocabulary loading errors', async () => {
    mockSubtitleServiceInstance.loadRealVocabulary.mockRejectedValue(
      new Error('Vocabulary loading failed')
    );

    const { getByText } = renderWithProvider();

    await waitFor(() => {
      expect(getByText('Error loading vocabulary')).toBeTruthy();
    }, { timeout: 6000 });
  });

  it('should display correct progress percentages', async () => {
    const { getByText } = renderWithProvider();

    // Check initial state
    expect(getByText('Transcription: ⏳ Pending')).toBeTruthy();
    expect(getByText('A1 Filtering: ⏳ Pending')).toBeTruthy();
    expect(getByText('Translation: ⏳ Pending')).toBeTruthy();

    // Wait for completion
    await waitFor(() => {
      expect(getByText('Transcription: ✅ Complete')).toBeTruthy();
      expect(getByText('A1 Filtering: ✅ Complete')).toBeTruthy();
      expect(getByText('Translation: ✅ Complete')).toBeTruthy();
    }, { timeout: 5000 });
  });
});