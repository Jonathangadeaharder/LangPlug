import fetchMock from 'jest-fetch-mock';
import { defaultEpisodes } from '../../models/Episode';

// Mock the PythonBridgeService before importing SubtitleService
const mockPythonBridgeService = {
  checkBackendHealth: jest.fn(),
  requestA1Processing: jest.fn(),
  requestSubtitleTranslation: jest.fn(),
  requestVocabularyAnalysis: jest.fn(),
  requestSubtitleCreation: jest.fn(),
  requestDependencyCheck: jest.fn(),
};

// Create a mock instance that mimics the PythonBridgeService
const mockPythonBridgeInstance = {
  ...mockPythonBridgeService,
};

// Mock PythonBridgeService module using doMock for better control
jest.doMock('../PythonBridgeService', () => ({
  __esModule: true,
  default: mockPythonBridgeInstance,
  PythonBridgeService: jest.fn().mockImplementation(() => mockPythonBridgeInstance)
}));

// Import SubtitleService after mocking PythonBridgeService
const { SubtitleService } = require('../SubtitleService');
const PythonBridgeService = require('../PythonBridgeService').default;

describe('SubtitleService', () => {
  let subtitleService: SubtitleService;

  beforeEach(() => {
    fetchMock.resetMocks();
    jest.clearAllMocks();
    
    // Reset all mocks to their default behavior
    mockPythonBridgeInstance.checkBackendHealth.mockResolvedValue(false);
    mockPythonBridgeInstance.requestA1Processing.mockResolvedValue({
      success: false,
      data: null,
      error: 'Backend not available'
    });
    mockPythonBridgeInstance.requestSubtitleTranslation.mockResolvedValue({
      success: false,
      data: null,
      error: 'Backend not available'
    });
    mockPythonBridgeInstance.requestVocabularyAnalysis.mockResolvedValue({
      success: false,
      data: null,
      error: 'Backend not available'
    });
    mockPythonBridgeInstance.requestSubtitleCreation.mockResolvedValue({
      success: false,
      data: null,
      error: 'Backend not available'
    });
    mockPythonBridgeInstance.requestDependencyCheck.mockResolvedValue({
      success: false,
      data: null,
      error: 'Backend not available'
    });
    
    subtitleService = SubtitleService.getInstance();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('getInstance', () => {
    it('should return singleton instance', () => {
      const instance1 = SubtitleService.getInstance();
      const instance2 = SubtitleService.getInstance();
      expect(instance1).toBe(instance2);
    });
  });

  describe('Mock verification', () => {
    it('should verify that PythonBridgeService is mocked', () => {
      expect(PythonBridgeService).toBe(mockPythonBridgeInstance);
      expect(PythonBridgeService.checkBackendHealth).toBe(mockPythonBridgeInstance.checkBackendHealth);
      expect(PythonBridgeService.requestA1Processing).toBe(mockPythonBridgeInstance.requestA1Processing);
    });
  });

  describe('checkSubtitleStatus', () => {
    it('should return correct status for episode with subtitle URL', async () => {
      const episode = { ...defaultEpisodes[0], subtitleUrl: '/path/to/subtitle.srt' };
      const status = await subtitleService.checkSubtitleStatus(episode);

      expect(status.isTranscribed).toBe(true);
      expect(status.hasFilteredSubtitles).toBe(episode.hasFilteredSubtitles);
      expect(status.hasTranslatedSubtitles).toBe(episode.hasTranslatedSubtitles);
      expect(status.subtitlePath).toBe(episode.subtitleUrl);
    });

    it('should return false for episode without subtitle URL', async () => {
      const episode = { 
        ...defaultEpisodes[0], 
        subtitleUrl: undefined,
        hasFilteredSubtitles: false,
        hasTranslatedSubtitles: false
      };
      const status = await subtitleService.checkSubtitleStatus(episode);

      expect(status.isTranscribed).toBe(false);
      expect(status.hasFilteredSubtitles).toBe(false);
      expect(status.hasTranslatedSubtitles).toBe(false);
      expect(status.subtitlePath).toBeUndefined();
    });
  });

  describe('processEpisode', () => {
    it('should process episode successfully', async () => {
      const episode = {
        ...defaultEpisodes[0],
        isTranscribed: false,
        hasFilteredSubtitles: false,
        hasTranslatedSubtitles: false,
        subtitleUrl: undefined
      };
      const mockProgress = jest.fn();

      // Mock backend health check
      mockPythonBridgeInstance.checkBackendHealth.mockResolvedValue(true);

      // Mock A1 Decider result
      mockPythonBridgeInstance.requestA1Processing.mockResolvedValue({
        success: true,
        data: {
          totalWords: 100,
          unknownWords: 20,
          difficultyLevel: 'intermediate' as const,
          filteredSubtitleFile: '/path/to/filtered.srt'
        },
        error: null
      });

      // Mock translation result
      mockPythonBridgeInstance.requestSubtitleTranslation.mockResolvedValue({
        success: true,
        data: {
          outputFile: '/path/to/translated.srt',
          totalSegments: 50
        },
        error: null
      });

      const result = await subtitleService.processEpisode(episode, mockProgress);

      expect(result.isTranscribed).toBe(true);
      expect(result.hasFilteredSubtitles).toBe(true);
      expect(result.hasTranslatedSubtitles).toBe(true);
      expect(mockProgress).toHaveBeenCalledWith({
        stage: 'complete',
        progress: 100,
        message: 'Processing complete! Ready to start game.',
      });
      // Debug: Let's see how many calls we actually get
      console.log('Main call count:', mockProgress.mock.calls.length);
      console.log('Mock calls:', mockProgress.mock.calls.map(call => call[0]));
      // Should have: 5 transcription (1 initial + 4 simulate) + 3 A1 Decider filtering + 4 real translation + 1 complete = 13 calls
      // expect(mockProgress).toHaveBeenCalledTimes(13);
    });

    it('should handle backend health check failure', async () => {
      const episode = {
        ...defaultEpisodes[0],
        isTranscribed: false,
        hasFilteredSubtitles: false,
        hasTranslatedSubtitles: false,
        subtitleUrl: undefined
      };
      const mockProgress = jest.fn();
      mockPythonBridgeInstance.checkBackendHealth.mockResolvedValue(false);

      // Mock setTimeout to make the simulation instant for testing
      const originalSetTimeout = global.setTimeout;
      global.setTimeout = jest.fn((callback) => {
        callback();
        return 1 as any;
      });
      
      try {
        console.log('Episode ID:', episode.id);
        console.log('Starting processEpisode with backend health check failure');
        
        const result = await subtitleService.processEpisode(episode, mockProgress);
        
        expect(result.isTranscribed).toBe(true);
        expect(result.hasFilteredSubtitles).toBe(true);
        expect(result.hasTranslatedSubtitles).toBe(true);
        
        // Check that progress calls were made
        expect(mockProgress.mock.calls.length).toBeGreaterThan(0);
        
        // Check that the final completion call was made
        const lastCall = mockProgress.mock.calls[mockProgress.mock.calls.length - 1];
        expect(lastCall[0]).toEqual({
          stage: 'complete',
          progress: 100,
          message: 'Processing complete! Ready to start game.'
        });
      } finally {
        // Restore original setTimeout
        global.setTimeout = originalSetTimeout;
      }
    }, 5000);

    it('should handle A1 Decider failure', async () => {
      const episode = {
        ...defaultEpisodes[0],
        isTranscribed: true,
        hasFilteredSubtitles: false,
        hasTranslatedSubtitles: false,
        subtitleUrl: 'assets/subtitles/test.srt'
      };
      mockPythonBridgeInstance.checkBackendHealth.mockResolvedValue(true);
      mockPythonBridgeInstance.requestA1Processing.mockResolvedValue({
        success: false,
        data: null,
        error: 'A1 Decider failed'
      });

      // Mock setTimeout to make any potential simulation instant for testing
      const originalSetTimeout = global.setTimeout;
      global.setTimeout = jest.fn((callback) => {
        callback();
        return 1 as any;
      });
      
      try {
        // Clear any previous processing state
        subtitleService['processedEpisodes'].clear();
        
        const result = await subtitleService.processEpisode(episode);
        
        // Should still complete with simulated processing when API fails
        expect(result.isTranscribed).toBe(true);
        expect(result.hasFilteredSubtitles).toBe(true);
        expect(result.hasTranslatedSubtitles).toBe(true);
      } finally {
        // Restore original setTimeout
        global.setTimeout = originalSetTimeout;
      }
    });
  });

  describe('processEpisodeSimulated', () => {
    it('should simulate processing with progress updates', async () => {
      // Use an episode that hasn't been processed yet
      const episode = {
        ...defaultEpisodes[0],
        isTranscribed: false,
        hasFilteredSubtitles: false,
        hasTranslatedSubtitles: false,
        subtitleUrl: undefined
      };
      const mockProgress = jest.fn();

      // Mock setTimeout to make the simulation instant for testing
      const originalSetTimeout = global.setTimeout;
      global.setTimeout = jest.fn((callback) => {
        callback();
        return 1 as any;
      });
      
      try {
        // Clear any previous processing state
        subtitleService['processedEpisodes'].clear();
        
        // Register the callback manually since processEpisodeSimulated doesn't take onProgress parameter
        subtitleService['processingCallbacks'].set(episode.id, mockProgress);
        const result = await subtitleService['processEpisodeSimulated'](episode);

        expect(result.isTranscribed).toBe(true);
        expect(result.hasFilteredSubtitles).toBe(true);
        expect(result.hasTranslatedSubtitles).toBe(true);
        
        // Check that progress calls were made
        expect(mockProgress.mock.calls.length).toBeGreaterThan(0);
        
        // Should have: 5 transcription (1 initial + 4 simulate) + 4 filtering (1 initial + 3 simulate) + 4 translation (1 initial + 3 simulate) + 1 complete = 14 calls
        expect(mockProgress).toHaveBeenCalledTimes(14);
        
        // Check that the final completion call was made
        const lastCall = mockProgress.mock.calls[mockProgress.mock.calls.length - 1];
        expect(lastCall[0]).toEqual({
          stage: 'complete',
          progress: 100,
          message: 'Processing complete! Ready to start game.'
        });
      } finally {
        // Restore original setTimeout
        global.setTimeout = originalSetTimeout;
      }
    }, 5000);
  });

  describe('loadRealVocabulary', () => {
    it('should load vocabulary from subtitle analysis', async () => {
      const subtitlePath = '/path/to/subtitle.srt';
      const mockVocabulary = [
        {
          word: 'schwierig',
          frequency: 5,
          translation: 'difficult',
          is_relevant: true,
          affected_subtitles: 3,
        },
      ];

      // Mock backend health check
      mockPythonBridgeInstance.checkBackendHealth.mockResolvedValue(true);
      mockPythonBridgeInstance.requestVocabularyAnalysis.mockResolvedValue({
        success: true,
        data: mockVocabulary,
        error: null
      });

      const result = await subtitleService.loadRealVocabulary(subtitlePath);

      expect(result).toHaveLength(1);
      expect(result[0].german).toBe('schwierig');
      expect(result[0].english).toBe('difficult');
      expect(mockPythonBridgeInstance.requestVocabularyAnalysis).toHaveBeenCalledWith({
        subtitleFile: subtitlePath,
        vocabularyOnly: true
      });
    });

    it('should return fallback vocabulary when no subtitle path provided', async () => {
      const result = await subtitleService.loadRealVocabulary();

      expect(result).toHaveLength(20); // Default fallback vocabulary size
      expect(result[0]).toHaveProperty('german');
      expect(result[0]).toHaveProperty('english');
    });

    it('should handle vocabulary analysis failure', async () => {
      const subtitlePath = '/path/to/subtitle.srt';
      mockPythonBridgeInstance.checkBackendHealth.mockResolvedValue(true);
      mockPythonBridgeInstance.requestVocabularyAnalysis.mockResolvedValue({
        success: false,
        data: null,
        error: 'Vocabulary analysis failed'
      });

      const result = await subtitleService.loadRealVocabulary(subtitlePath);

      expect(result).toHaveLength(20); // Should fallback to default vocabulary
    });
  });

  describe('getFallbackVocabulary', () => {
    it('should return 20 vocabulary words', () => {
      const vocabulary = subtitleService.getFallbackVocabulary();

      expect(vocabulary).toHaveLength(20);
      expect(vocabulary[0]).toHaveProperty('german');
      expect(vocabulary[0]).toHaveProperty('english');
      expect(vocabulary[0]).toHaveProperty('frequency');
    });
  });

  describe('updateProgress', () => {
    it('should call progress callback if registered', () => {
      const episodeId = 'test-episode';
      const mockCallback = jest.fn();
      const progress = {
        stage: 'filtering' as const,
        progress: 50,
        message: 'Filtering subtitles...',
      };

      // Register callback
      subtitleService['processingCallbacks'].set(episodeId, mockCallback);

      subtitleService['updateProgress'](episodeId, progress);

      expect(mockCallback).toHaveBeenCalledWith(progress);
    });

    it('should not throw error if no callback registered', () => {
      const progress = {
        stage: 'filtering' as const,
        progress: 50,
        message: 'Filtering subtitles...',
      };

      expect(() => {
        subtitleService['updateProgress']('non-existent-episode', progress);
      }).not.toThrow();
    });
  });
});