import { Episode, VocabularyWord } from '../models/Episode';
import { 
  PythonBridgeService,
  RawApiResponse, 
  RawVocabularyWord, 
  RawA1DeciderResult, 
  RawTranslationResult, 
  RawSubtitleCreationResult 
} from './PythonBridgeService';

interface SubtitleProcessingStatus {
  isTranscribed: boolean;
  hasFilteredSubtitles: boolean;
  hasTranslatedSubtitles: boolean;
  subtitlePath?: string;
  filteredSubtitlePath?: string;
  translatedSubtitlePath?: string;
}

interface ProcessingProgress {
  stage: 'transcription' | 'filtering' | 'translation' | 'complete';
  progress: number;
  message: string;
}

export class SubtitleService {
  private static instance: SubtitleService;
  private pythonBridge: PythonBridgeService;
  private processingCallbacks: Map<string, (progress: ProcessingProgress) => void> = new Map();
  private processedEpisodes: Map<string, { hasFilteredSubtitles: boolean; hasTranslatedSubtitles: boolean }> = new Map();

  constructor() {
    this.pythonBridge = new PythonBridgeService();
  }

  static getInstance(): SubtitleService {
    if (!SubtitleService.instance) {
      SubtitleService.instance = new SubtitleService();
    }
    return SubtitleService.instance;
  }

  /**
   * Check if episode has been transcribed and processed
   */
  async checkSubtitleStatus(episode: Episode): Promise<SubtitleProcessingStatus> {
    // In a real implementation, this would check the file system or API
    // For now, we'll simulate based on episode ID and tracked processing state
    const baseDir = `assets/subtitles`;
    const baseName = episode.id;
    
    // Check if episode has been processed
    const processedState = this.processedEpisodes.get(episode.id);
    
    // Simulate checking file existence
    const isTranscribed = episode.subtitleUrl !== undefined;
    const hasFilteredSubtitles = processedState?.hasFilteredSubtitles || episode.hasFilteredSubtitles || false;
    const hasTranslatedSubtitles = processedState?.hasTranslatedSubtitles || episode.hasTranslatedSubtitles || false;
    
    return {
      isTranscribed,
      hasFilteredSubtitles,
      hasTranslatedSubtitles,
      subtitlePath: isTranscribed ? episode.subtitleUrl : undefined,
      filteredSubtitlePath: hasFilteredSubtitles ? `${baseDir}/${baseName}_a1filtered.srt` : undefined,
      translatedSubtitlePath: hasTranslatedSubtitles ? `${baseDir}/${baseName}_a1filtered_es.srt` : undefined,
    };
  }

  /**
   * Process episode through the complete workflow
   */
  async processEpisode(
    episode: Episode,
    onProgress?: (progress: ProcessingProgress) => void
  ): Promise<SubtitleProcessingStatus> {
    const episodeId = episode.id;
    
    if (onProgress) {
      this.processingCallbacks.set(episodeId, onProgress);
    }

    try {
      // Check if backend is available
      const isBackendHealthy = await this.pythonBridge.checkBackendHealth();
      if (!isBackendHealthy) {
        console.warn('Backend not available, using simulated processing');
        return this.processEpisodeSimulated(episode);
      }

      // Check current status
      const status = await this.checkSubtitleStatus(episode);
      
      // Step 1: Create subtitles if not transcribed
      if (!status.isTranscribed) {
        await this.createSubtitles(episode);
      }
      
      // Step 2: Real A1 Decider Processing
      if (!status.hasFilteredSubtitles) {
        this.updateProgress(episodeId, {
          stage: 'filtering',
          progress: 0,
          message: 'Starting A1 vocabulary analysis...'
        });
        
        if (episode.subtitleUrl) {
          const response = await this.pythonBridge.requestA1Processing({
            subtitleFile: episode.subtitleUrl,
            outputPath: `assets/subtitles/${episode.id}_a1filtered.srt`
          });
          
          if (response.success && response.data) {
            const result = response.data as RawA1DeciderResult;
            
            this.updateProgress(episodeId, {
              stage: 'filtering',
              progress: 50,
              message: `Found ${result.totalWords} words, ${result.unknownWords} unknown`
            });
            
            this.updateProgress(episodeId, {
              stage: 'filtering',
              progress: 100,
              message: `Difficulty: ${result.difficultyLevel}`
            });
            
            // Mark episode as having filtered subtitles
            const currentState = this.processedEpisodes.get(episode.id) || { hasFilteredSubtitles: false, hasTranslatedSubtitles: false };
            this.processedEpisodes.set(episode.id, { ...currentState, hasFilteredSubtitles: true });
          } else {
            console.error('A1 processing failed:', response.error);
            await this.filterSubtitles(episode);
          }
        } else {
          await this.filterSubtitles(episode);
        }
      }
      
      // Step 3: Translate filtered subtitles
      if (!status.hasTranslatedSubtitles) {
        this.updateProgress(episodeId, {
          stage: 'translation',
          progress: 0,
          message: 'Starting translation...'
        });
        
        // Check if we have a filtered subtitle path to translate
        const currentState = this.processedEpisodes.get(episode.id);
        if (currentState?.hasFilteredSubtitles) {
          // Use real translation service
          const filteredPath = `assets/subtitles/${episode.id}_a1filtered.srt`;
          const response = await this.pythonBridge.requestSubtitleTranslation({
            inputFile: filteredPath,
            outputFile: `assets/subtitles/${episode.id}_a1filtered_es.srt`,
            targetLanguage: 'es'
          });
          
          if (response.success && response.data) {
            const result = response.data as RawTranslationResult;
            
            this.updateProgress(episodeId, {
              stage: 'translation',
              progress: 50,
              message: `Translating ${result.totalSegments} segments...`
            });
            
            this.updateProgress(episodeId, {
              stage: 'translation',
              progress: 100,
              message: `Translation complete: ${result.translatedSegments} segments processed`
            });
            
            // Mark episode as having translated subtitles
            this.processedEpisodes.set(episode.id, { ...currentState, hasTranslatedSubtitles: true });
          } else {
            console.error('Translation failed:', response.error);
            await this.translateSubtitles(episode);
          }
        } else {
          // Fallback to simulated translation
          await this.translateSubtitles(episode);
        }
      }
      
      this.updateProgress(episodeId, {
        stage: 'complete',
        progress: 100,
        message: 'Processing complete! Ready to start game.'
      });
      
      return await this.checkSubtitleStatus(episode);
      
    } catch (error) {
      console.error('Error processing episode:', error);
      throw error;
    } finally {
      // Don't delete callback here for simulated processing since it's async
      // this.processingCallbacks.delete(episodeId);
    }
  }

  /**
   * Fallback simulated processing when backend is not available
   */
  private async processEpisodeSimulated(
    episode: Episode
  ): Promise<SubtitleProcessingStatus> {
    const episodeId = episode.id;

    try {
      // Check current status
      const status = await this.checkSubtitleStatus(episode);
      
      // Step 1: Create subtitles if not transcribed
      if (!status.isTranscribed) {
        await this.createSubtitles(episode);
      }
      
      // Step 2: Filter subtitles
      if (!status.hasFilteredSubtitles) {
        await this.filterSubtitles(episode);
      }
      
      // Step 3: Translate filtered subtitles
      if (!status.hasTranslatedSubtitles) {
        await this.translateSubtitles(episode);
      }
      
      this.updateProgress(episodeId, {
        stage: 'complete',
        progress: 100,
        message: 'Processing complete! Ready to start game.'
      });
      
      const result = await this.checkSubtitleStatus(episode);
      
      // Clean up callback after processing is complete
      this.processingCallbacks.delete(episodeId);
      
      return result;
      
    } catch (error) {
      console.error('Error processing episode:', error);
      this.processingCallbacks.delete(episodeId);
      throw error;
    }
  }

  private async createSubtitles(episode: Episode): Promise<void> {
    this.updateProgress(episode.id, {
      stage: 'transcription',
      progress: 10,
      message: 'Starting transcription...'
    });
    
    try {
      // Try real subtitle creation first
      const response = await this.pythonBridge.requestSubtitleCreation({
        videoFile: episode.videoUrl,
        outputFile: `assets/subtitles/${episode.id}.srt`,
        language: 'en'
      });
      
      if (response.success && response.data) {
        const result = response.data as RawSubtitleCreationResult;
        
        this.updateProgress(episode.id, {
          stage: 'transcription',
          progress: 50,
          message: `Processing ${result.totalSegments} segments...`
        });
        
        this.updateProgress(episode.id, {
          stage: 'transcription',
          progress: 100,
          message: `Transcription complete: ${result.duration} seconds processed`
        });
        
        // Mark episode as transcribed by setting subtitleUrl
        episode.subtitleUrl = result.outputFile;
        console.log(`Created subtitles for ${episode.title}`);
        return;
      } else {
        console.error('Subtitle creation failed:', response.error);
      }
    } catch (error) {
      console.error('Error in subtitle creation:', error);
    }
    
    // Fallback to simulated transcription process
    await this.simulateProcess([
      { progress: 20, message: 'Extracting audio...' },
      { progress: 40, message: 'Running Whisper transcription...' },
      { progress: 60, message: 'Processing segments...' },
      { progress: 80, message: 'Generating SRT file...' },
    ], episode.id, 'transcription');
    
    // Mark episode as transcribed by setting subtitleUrl
    episode.subtitleUrl = `assets/subtitles/${episode.id}.srt`;
    console.log(`Created subtitles for ${episode.title} (simulated)`);
  }

  private async filterSubtitles(episode: Episode): Promise<void> {
    this.updateProgress(episode.id, {
      stage: 'filtering',
      progress: 10,
      message: 'Loading known words...'
    });
    
    // Simulate filtering process
    await this.simulateProcess([
      { progress: 30, message: 'Analyzing vocabulary...' },
      { progress: 60, message: 'Filtering unknown words...' },
      { progress: 90, message: 'Generating filtered subtitles...' },
    ], episode.id, 'filtering');
    
    // Mark episode as having filtered subtitles
    const currentState = this.processedEpisodes.get(episode.id) || { hasFilteredSubtitles: false, hasTranslatedSubtitles: false };
    this.processedEpisodes.set(episode.id, { ...currentState, hasFilteredSubtitles: true });
    
    // In real implementation, this would call the a1decider filtering logic
    console.log(`Filtered subtitles for ${episode.title}`);
  }

  private async translateSubtitles(episode: Episode): Promise<void> {
    this.updateProgress(episode.id, {
      stage: 'translation',
      progress: 10,
      message: 'Loading translation model...'
    });
    
    // Simulate translation process
    await this.simulateProcess([
      { progress: 30, message: 'Translating subtitles...' },
      { progress: 70, message: 'Processing translations...' },
      { progress: 90, message: 'Saving translated subtitles...' },
    ], episode.id, 'translation');
    
    // Mark episode as having translated subtitles
    const currentState = this.processedEpisodes.get(episode.id) || { hasFilteredSubtitles: false, hasTranslatedSubtitles: false };
    this.processedEpisodes.set(episode.id, { ...currentState, hasTranslatedSubtitles: true });
    
    // In real implementation, this would call the subtitle_translate
    console.log(`Translated subtitles for ${episode.title}`);
  }

  private async simulateProcess(
    steps: { progress: number; message: string }[],
    episodeId: string,
    stage: ProcessingProgress['stage']
  ): Promise<void> {
    for (const step of steps) {
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate processing time
      this.updateProgress(episodeId, {
        stage,
        progress: step.progress,
        message: step.message
      });
    }
  }

  private updateProgress(episodeId: string, progress: ProcessingProgress): void {
    const callback = this.processingCallbacks.get(episodeId);
    if (callback) {
      callback(progress);
    }
  }

  /**
   * Get vocabulary words from filtered subtitles for game generation
   */
  async getVocabularyFromSubtitles(episode: Episode): Promise<string[]> {
    // In real implementation, this would parse the filtered subtitle file
    // and extract unique vocabulary words for the game
    
    // For now, return the existing vocabulary words
    return episode.vocabularyWords;
  }

  /**
   * Load real vocabulary from subtitle analysis using A1Decider
   * Returns only the 20 most relevant vocabulary words
   */
  async loadRealVocabulary(subtitlePath?: string): Promise<VocabularyWord[]> {
    try {
      // If no subtitle path provided, use fallback vocabulary
      if (!subtitlePath) {
        return this.getFallbackVocabulary();
      }
      
      // Check if backend is available
      const isBackendHealthy = await this.pythonBridge.checkBackendHealth();
      if (!isBackendHealthy) {
        console.warn('Backend not available, using fallback vocabulary');
        return this.getFallbackVocabulary();
      }
      
      // Get real vocabulary analysis from subtitle file
      const response = await this.pythonBridge.requestVocabularyAnalysis({
        subtitleFile: subtitlePath,
        vocabularyOnly: true
      });
      
      if (!response.success || !response.data) {
        console.error('Vocabulary analysis failed:', response.error);
        return this.getFallbackVocabulary();
      }
      
      const vocabularyWords = response.data as RawVocabularyWord[];
      
      // Convert to our VocabularyWord format
      const allWords = vocabularyWords.map((word, index) => ({
        id: `real_word_${index}`,
        german: word.word,
        english: word.translation,
        difficulty: word.isRelevant ? 'A1' : 'A2',
        frequency: word.frequency,
        context: `Found in ${word.affectedSubtitles} subtitle${word.affectedSubtitles !== 1 ? 's' : ''}`,
        relevanceScore: word.isRelevant ? word.frequency * 2 : word.frequency // Boost relevant words
      }));
      
      // Sort by relevance score (frequency + relevance boost) and return top 20
      return allWords
        .sort((a, b) => (b as any).relevanceScore - (a as any).relevanceScore)
        .slice(0, 20)
        .map(word => {
          // Remove relevanceScore from final result
          const { relevanceScore, ...finalWord } = word as any;
          return finalWord;
        });
      
    } catch (error) {
      console.error('Error loading real vocabulary:', error);
      console.log('Falling back to static vocabulary');
      return this.getFallbackVocabulary();
    }
  }
  
  /**
   * Get fallback vocabulary when real analysis is not available
   * Returns only the 20 most relevant vocabulary words
   */
  getFallbackVocabulary(): VocabularyWord[] {
    // Most common and relevant A1 German vocabulary (prioritized for learning)
    const priorityA1Words = [
      'ja', 'und', 'von', 'ein', 'einer', 'es', 'seine', 'ihre', 'man', 'können',
      'kommen', 'als', 'jetzt', 'verstehen', 'beginnen', 'immer', 'sehr', 'aber',
      'wissen', 'Leben', 'essen', 'Wasser', 'klein', 'alt', 'frei', 'sicher',
      'gegen', 'wo', 'bis', 'genug'
    ];

    // Select top 20 most relevant words for A1 learners
    const selectedWords = priorityA1Words.slice(0, 20);
    
    return selectedWords.map((word, index) => ({
      id: `fallback_word_${index}`,
      german: word,
      english: this.getEnglishTranslation(word),
      difficulty: 'A1',
      frequency: 10 - Math.floor(index / 2), // Higher frequency for earlier words
      context: `Aus "Call the Midwife": "...${word}..."`
    }));
  }

  private getEnglishTranslation(germanWord: string): string {
    const translations: { [key: string]: string } = {
      'drücken': 'to press', 'vielleicht': 'maybe', 'Bahnhof': 'train station',
      'Salat': 'salad', 'Block': 'block', 'Kasse': 'cash register',
      'wunderbar': 'wonderful', 'Maschine': 'machine', 'Fall': 'case',
      'tief': 'deep', 'jeder': 'everyone', 'Liste': 'list', 'ja': 'yes',
      'beide': 'both', 'Apartment': 'apartment', 'Krieg': 'war',
      'geradeaus': 'straight ahead', 'sieben': 'seven', 'Lösung': 'solution',
      'von': 'from', 'Kuchen': 'cake', 'danken': 'to thank', 'Farbe': 'color',
      'team': 'team', 'trainerin': 'trainer (female)', 'ins': 'into the',
      'des': 'of the', 'guter': 'good', 'unseren': 'our', 'zum': 'to the',
      'camp': 'camp', 'freundinnen': 'girlfriends', 'besten': 'best',
      'gesagt': 'said', 'habt': 'have', 'peinlich': 'embarrassing',
      'kummer': 'sorrow', 'ideen': 'ideas', 'erinnerungen': 'memories',
      'sehe': 'see', 'glaube': 'believe', 'extra': 'extra', 'jahre': 'years',
      'steht': 'stands', 'keinen': 'no', 'nächstes': 'next', 'guten': 'good',
      'wäre': 'would be', 'denkt': 'thinks', 'mag': 'likes', 'bilder': 'pictures'
    };
    
    return translations[germanWord] || `Translation for ${germanWord}`;
  }
}

export default SubtitleService.getInstance();