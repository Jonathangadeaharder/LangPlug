// Raw API response interfaces - no business logic transformation
export interface RawApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface RawVocabularyWord {
  word: string;
  frequency: number;
  translation: string;
  is_relevant: boolean;
  affected_subtitles: number;
}

export interface RawA1DeciderResult {
  subtitle_file: string;
  total_subtitles: number;
  skipped_subtitles: number;
  skipped_hard: number;
  total_unknown_words: number;
  relevant_vocabulary_count: number;
  vocabulary: RawVocabularyWord[];
  filtered_subtitle_file?: string;
}

export interface RawTranslationResult {
  success: boolean;
  output_path?: string;
  source_file: string;
  target_language: string;
}

export interface RawSubtitleCreationResult {
  success: boolean;
  output_path?: string;
  video_file: string;
  language: string;
}

/**
 * PythonBridgeService - Responsible ONLY for HTTP communication with the backend API
 * 
 * Single Responsibility: Low-level HTTP requests and raw response handling
 * - Makes HTTP requests to backend endpoints
 * - Handles network errors and timeouts
 * - Returns raw API responses without transformation
 * - No business logic or data transformation
 */
export class PythonBridgeService {
  private static instance: PythonBridgeService;
  private readonly backendUrl = 'http://localhost:3001/api';
  private readonly healthUrl = 'http://localhost:3001/health';
  private readonly defaultTimeout = 30000; // 30 seconds

  static getInstance(): PythonBridgeService {
    if (!PythonBridgeService.instance) {
      PythonBridgeService.instance = new PythonBridgeService();
    }
    return PythonBridgeService.instance;
  }

  /**
   * Make HTTP request to create subtitles endpoint
   * Returns raw API response without transformation
   */
  async requestSubtitleCreation(videoPath: string, language: string = 'de'): Promise<RawApiResponse<RawSubtitleCreationResult>> {
    return this.makeRequest('/create-subtitles', {
      method: 'POST',
      body: JSON.stringify({
        videoPath,
        language
      })
    });
  }

  /**
   * Make HTTP request to process subtitles with A1 Decider
   * Returns raw API response without transformation
   */
  async requestA1Processing(subtitlePath: string, vocabularyOnly: boolean = false): Promise<RawApiResponse<RawA1DeciderResult>> {
    return this.makeRequest('/process-subtitles', {
      method: 'POST',
      body: JSON.stringify({
        subtitleFile: subtitlePath,
        vocabularyOnly: vocabularyOnly
      })
    });
  }

  /**
   * Make HTTP request to translate subtitles endpoint
   * Returns raw API response without transformation
   */
  async requestSubtitleTranslation(
    filteredSubtitlePath: string,
    sourceLang: string = 'de',
    targetLang: string = 'es'
  ): Promise<RawApiResponse<RawTranslationResult>> {
    return this.makeRequest('/translate-subtitles', {
      method: 'POST',
      body: JSON.stringify({
        subtitleFile: filteredSubtitlePath,
        sourceLang,
        targetLang
      })
    });
  }

  /**
   * Make HTTP request to check backend dependencies
   * Returns raw API response without transformation
   */
  async requestDependencyCheck(): Promise<RawApiResponse<any>> {
    return this.makeRequest('/check-dependencies', {
      method: 'GET'
    });
  }

  /**
   * Make HTTP request to get vocabulary analysis
   * Returns raw API response without transformation
   */
  async requestVocabularyAnalysis(subtitlePath: string): Promise<RawApiResponse<RawA1DeciderResult>> {
    return this.makeRequest('/process-subtitles', {
      method: 'POST',
      body: JSON.stringify({
        subtitleFile: subtitlePath,
        vocabularyOnly: true
      })
    });
  }

  /**
   * Check backend server health
   * Returns boolean indicating if backend is reachable
   */
  async checkBackendHealth(): Promise<boolean> {
    try {
      const response = await fetch(this.healthUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(5000) // 5 second timeout for health check
      });
      
      return response.ok;
    } catch (error) {
      console.error('Backend health check failed:', error);
      return false;
    }
  }

  /**
   * Core HTTP request method - handles all API communication
   * Returns raw response without business logic transformation
   */
  private async makeRequest<T = any>(
    endpoint: string,
    options: {
      method: 'GET' | 'POST' | 'PUT' | 'DELETE';
      body?: string;
      headers?: Record<string, string>;
      timeout?: number;
    }
  ): Promise<RawApiResponse<T>> {
    const { method, body, headers = {}, timeout = this.defaultTimeout } = options;
    
    try {
      const response = await fetch(`${this.backendUrl}${endpoint}`, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...headers
        },
        body,
        signal: AbortSignal.timeout(timeout)
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        return {
          success: false,
          error: errorData.error || `HTTP ${response.status}: ${response.statusText}`
        };
      }
      
      const data = await response.json();
      return {
        success: true,
        data: data.data || data,
        message: data.message
      };
      
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network request failed'
      };
    }
  }
}

export default PythonBridgeService.getInstance();