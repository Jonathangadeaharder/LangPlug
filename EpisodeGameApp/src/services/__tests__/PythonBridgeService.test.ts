import PythonBridgeService from '../PythonBridgeService';
import fetchMock from 'jest-fetch-mock';

describe('PythonBridgeService', () => {
  let pythonBridgeService: PythonBridgeService;

  beforeEach(() => {
    fetchMock.resetMocks();
    pythonBridgeService = new PythonBridgeService();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('constructor', () => {
    it('should create instance with default configuration', () => {
      const service = new PythonBridgeService();
      expect(service).toBeInstanceOf(PythonBridgeService);
    });
  });

  describe('checkBackendHealth', () => {
    it('should return true when backend is healthy', async () => {
      fetchMock.mockResponseOnce(
        JSON.stringify({ status: 'OK', timestamp: new Date().toISOString() })
      );

      const result = await pythonBridgeService.checkBackendHealth();

      expect(result).toBe(true);
      expect(fetchMock).toHaveBeenCalledWith(
        'http://localhost:3001/health',
        expect.objectContaining({
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          signal: expect.any(AbortSignal)
        })
      );
    });

    it('should return false when backend is unhealthy', async () => {
      fetchMock.mockRejectOnce(new Error('Connection refused'));

      const result = await pythonBridgeService.checkBackendHealth();

      expect(result).toBe(false);
    });

    it('should return false when backend returns non-OK response', async () => {
      fetchMock.mockResponseOnce('', { status: 500 });

      const result = await pythonBridgeService.checkBackendHealth();

      expect(result).toBe(false);
    });
  });

  describe('requestA1Processing', () => {
    const mockA1Response = {
      success: true,
      data: {
        subtitleFile: '/path/to/subtitle.srt',
        totalSubtitles: 100,
        skippedSubtitles: 80,
        skippedHard: 5,
        relevantVocabularyCount: 15,
        totalWords: 20,
        unknownWords: 15,
        difficultyLevel: 'intermediate',
        filteredSubtitleFile: '/path/to/filtered.srt',
        vocabulary: [
          {
            word: 'schwierig',
            frequency: 5,
            translation: 'difficult',
            isRelevant: true,
            affectedSubtitles: 3,
          },
        ],
      },
    };

    it('should process subtitles successfully', async () => {
      fetchMock.mockResponseOnce(JSON.stringify(mockA1Response));

      const result = await pythonBridgeService.requestA1Processing({
        subtitleFile: '/path/to/subtitle.srt',
        outputPath: '/path/to/filtered.srt'
      });

      expect(result.success).toBe(true);
      expect(result.data?.totalWords).toBe(20);
      expect(result.data?.unknownWords).toBe(15);
      expect(result.data?.difficultyLevel).toBe('intermediate');
      expect(result.data?.filteredSubtitleFile).toBe('/path/to/filtered.srt');

      expect(fetchMock).toHaveBeenCalledWith(
        'http://localhost:3001/api/process-subtitles',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            subtitleFile: '/path/to/subtitle.srt',
            outputPath: '/path/to/filtered.srt'
          }),
          signal: expect.any(AbortSignal)
        })
      );
    });

    it('should handle error responses', async () => {
      const errorResponse = {
        success: false,
        error: 'Processing failed'
      };
      
      fetchMock.mockResponseOnce(JSON.stringify(errorResponse), { status: 500 });

      const result = await pythonBridgeService.requestA1Processing({
        subtitleFile: '/path/to/subtitle.srt',
        outputPath: '/path/to/filtered.srt'
      });

      expect(result.success).toBe(false);
      expect(result.error).toBe('Processing failed');
    });

    it('should handle network errors', async () => {
      fetchMock.mockRejectOnce(new Error('Network error'));

      const result = await pythonBridgeService.requestA1Processing({
        subtitleFile: '/path/to/subtitle.srt',
        outputPath: '/path/to/filtered.srt'
      });

      expect(result.success).toBe(false);
      expect(result.error).toBe('Network error');
    });
  });

  describe('requestSubtitleTranslation', () => {
    it('should translate subtitles successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          inputFile: '/path/to/filtered.srt',
          outputFile: '/path/to/translated.srt',
          targetLanguage: 'es',
          totalSegments: 100,
          translatedSegments: 100
        }
      };

      fetchMock.mockResponseOnce(JSON.stringify(mockResponse));

      const result = await pythonBridgeService.requestSubtitleTranslation({
        inputFile: '/path/to/filtered.srt',
        outputFile: '/path/to/translated.srt',
        targetLanguage: 'es'
      });

      expect(result.success).toBe(true);
      expect(result.data?.outputFile).toBe('/path/to/translated.srt');
      expect(result.data?.totalSegments).toBe(100);
    });

    it('should handle translation errors', async () => {
      fetchMock.mockResponseOnce(
        JSON.stringify({
          success: false,
          error: 'Translation failed',
        }),
        { status: 500 }
      );

      const result = await pythonBridgeService.requestSubtitleTranslation({
        inputFile: '/path/to/filtered.srt',
        outputFile: '/path/to/translated.srt',
        targetLanguage: 'es'
      });

      expect(result.success).toBe(false);
      expect(result.error).toBe('Translation failed');
    });
  });

  describe('requestVocabularyAnalysis', () => {
    it('should get vocabulary analysis successfully', async () => {
      const mockVocabulary = [
        {
          word: 'schwierig',
          frequency: 5,
          translation: 'difficult',
          isRelevant: true,
          affectedSubtitles: 3,
        },
      ];

      fetchMock.mockResponseOnce(
        JSON.stringify({
          success: true,
          data: mockVocabulary,
        })
      );

      const result = await pythonBridgeService.requestVocabularyAnalysis({
        subtitleFile: '/path/to/subtitle.srt',
        vocabularyOnly: true
      });

      expect(result.success).toBe(true);
      expect(result.data).toEqual(mockVocabulary);
      expect(fetchMock).toHaveBeenCalledWith(
        'http://localhost:3001/api/vocabulary-analysis',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            subtitleFile: '/path/to/subtitle.srt',
            vocabularyOnly: true,
          }),
          signal: expect.any(AbortSignal)
        })
      );
    });

    it('should handle vocabulary analysis errors', async () => {
      fetchMock.mockRejectOnce(new Error('Analysis failed'));

      const result = await pythonBridgeService.requestVocabularyAnalysis({
        subtitleFile: '/path/to/subtitle.srt',
        vocabularyOnly: true
      });

      expect(result.success).toBe(false);
      expect(result.error).toBe('Analysis failed');
    });
  });

  describe('requestDependencyCheck', () => {
    it('should check dependencies successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          pythonAvailable: true,
          backendAvailable: true,
          missingDependencies: []
        }
      };

      fetchMock.mockResponseOnce(JSON.stringify(mockResponse));

      const result = await pythonBridgeService.requestDependencyCheck();

      expect(result.success).toBe(true);
      expect(result.data?.pythonAvailable).toBe(true);
      expect(fetchMock).toHaveBeenCalledWith(
        'http://localhost:3001/api/check-dependencies',
        expect.objectContaining({
          method: 'GET',
          signal: expect.any(AbortSignal)
        })
      );
    });

    it('should handle dependency check errors', async () => {
      fetchMock.mockRejectOnce(new Error('Connection failed'));

      const result = await pythonBridgeService.requestDependencyCheck();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Connection failed');
    });
  });
});