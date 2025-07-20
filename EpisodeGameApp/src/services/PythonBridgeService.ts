// Raw API response interfaces - no business logic transformation
// Updated to match Python FastAPI response structure
export interface RawApiResponse<T = any> {
  success: boolean;
  message?: string;
  results?: T;
  error?: string;
}

// Python API Health Response
export interface PythonHealthResponse {
  status: string;
  version: string;
  dependencies: Record<string, boolean>;
}

// Python API Processing Response
export interface PythonProcessingResponse {
  success: boolean;
  message: string;
  results?: {
    video_file: string;
    audio_file?: string;
    preview_srt?: string;
    full_srt?: string;
    filtered_srt?: string;
    translated_srt?: string;
    metadata?: any;
  };
  error?: string;
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
 * PythonBridgeService - Responsible ONLY for HTTP communication with the Python API
 * 
 * Single Responsibility: Low-level HTTP requests and raw response handling
 * - Makes HTTP requests directly to Python FastAPI endpoints
 * - Handles network errors and timeouts
 * - Returns raw API responses without transformation
 * - No business logic or data transformation
 * - Eliminates Node.js BFF dependency for simplified architecture
 */
export class PythonBridgeService {
  private static instance: PythonBridgeService;
  private readonly pythonApiUrl = 'http://localhost:8000';
  private readonly healthUrl = 'http://localhost:8000/health';
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
  async requestSubtitleCreation(videoPath: string, language: string = 'de'): Promise<PythonProcessingResponse> {
    return this.makeRequest('/api/process', {
      method: 'POST',
      body: JSON.stringify({
        video_file_path: videoPath,
        language: language,
        pipeline_config: 'full'
      })
    });
  }

  /**
   * Make HTTP request to process subtitles with A1 Decider
   * Returns raw API response without transformation
   */
  async requestA1Processing(subtitlePath: string, vocabularyOnly: boolean = false): Promise<PythonProcessingResponse> {
    // For existing subtitle files, we need to use a different approach
    // The Python API processes video files, not subtitle files directly
    // This method may need to be redesigned or the Python API extended
    const pipelineConfig = vocabularyOnly ? 'learning' : 'full';
    return this.makeRequest('/api/process', {
      method: 'POST',
      body: JSON.stringify({
        video_file_path: subtitlePath, // This may need adjustment
        pipeline_config: pipelineConfig
      })
    });
  }

  /**
   * Make HTTP request to translate subtitles endpoint
   * Translation is now handled as part of the unified pipeline
   * Returns raw API response without transformation
   */
  async requestSubtitleTranslation(
    videoPath: string,
    sourceLang: string = 'de',
    targetLang: string = 'es'
  ): Promise<PythonProcessingResponse> {
    return this.makeRequest('/api/process', {
      method: 'POST',
      body: JSON.stringify({
        video_file_path: videoPath,
        src_lang: sourceLang,
        tgt_lang: targetLang,
        pipeline_config: 'batch'
      })
    });
  }

  /**
   * Make HTTP request to check backend dependencies
   * Returns raw API response without transformation
   */
  async requestDependencyCheck(): Promise<PythonHealthResponse> {
    return this.makeRequest('/health', {
      method: 'GET'
    });
  }

  /**
   * Make HTTP request to get vocabulary analysis
   * Returns raw API response without transformation
   */
  async requestVocabularyAnalysis(videoPath: string): Promise<PythonProcessingResponse> {
    return this.makeRequest('/api/process', {
      method: 'POST',
      body: JSON.stringify({
        video_file_path: videoPath,
        pipeline_config: 'learning'
      })
    });
  }

  /**
   * Get available pipeline configurations
   * Returns raw API response without transformation
   */
  async requestPipelineConfigurations(): Promise<RawApiResponse<any>> {
    return this.makeRequest('/api/pipelines', {
      method: 'GET'
    });
  }

  /**
   * Check Python API server health
   * Returns boolean indicating if Python API is reachable
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
      console.error('Python API health check failed:', error);
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
      const response = await fetch(`${this.pythonApiUrl}${endpoint}`, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...headers
        },
        body,
        signal: AbortSignal.timeout(timeout)
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ 
          success: false,
          message: 'Unknown error',
          error: 'Unknown error' 
        }));
        return {
          success: false,
          message: errorData.message || `HTTP ${response.status}: ${response.statusText}`,
          error: errorData.error || errorData.detail || `HTTP ${response.status}: ${response.statusText}`
        };
      }
      
      const data = await response.json();
      return data; // Return the Python API response directly
      
    } catch (error) {
      return {
        success: false,
        message: 'Network request failed',
        error: error instanceof Error ? error.message : 'Network request failed'
      };
    }
  }
}

export default PythonBridgeService.getInstance();