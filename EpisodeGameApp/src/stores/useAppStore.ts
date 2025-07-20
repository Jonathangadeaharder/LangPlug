import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { Episode } from '../models/Episode';

// Types from existing contexts
interface GameSessionState {
  selectedEpisode: Episode | null;
  currentScore: number;
  totalQuestions: number;
  correctAnswers: number;
  gameStarted: boolean;
  gameCompleted: boolean;
  userAnswers: { [key: string]: string };
}

interface EpisodeProcessingState {
  isProcessing: boolean;
  processingStage: 'transcription' | 'filtering' | 'translation' | 'complete' | null;
}

interface VocabularyLearningState {
  knownWords: string[];
  unknownWords: string[];
  skippedWords: string[];
  vocabularyAnalysis: {
    totalWords: number;
    knownCount: number;
    unknownCount: number;
    difficultyLevel?: 'beginner' | 'intermediate' | 'advanced';
  } | null;
}

// Combined store interface
interface AppStore {
  // Game Session State
  gameSession: GameSessionState;
  
  // Game Session Actions
  selectEpisode: (episode: Episode) => void;
  startGame: () => void;
  answerQuestion: (questionId: string, answer: string, isCorrect: boolean) => void;
  completeGame: () => void;
  resetGame: () => void;
  updateEpisodeStatus: (hasFilteredSubtitles: boolean, hasTranslatedSubtitles: boolean) => void;
  
  // Episode Processing State
  episodeProcessing: EpisodeProcessingState;
  
  // Episode Processing Actions
  startProcessing: (stage: 'transcription' | 'filtering' | 'translation') => void;
  updateProcessingProgress: (stage: 'transcription' | 'filtering' | 'translation' | 'complete') => void;
  completeProcessing: () => void;
  
  // Vocabulary Learning State
  vocabularyLearning: VocabularyLearningState;
  
  // Vocabulary Learning Actions
  addKnownWord: (word: string) => void;
  addUnknownWord: (word: string) => void;
  addSkippedWord: (word: string) => void;
  setVocabularyAnalysis: (analysis: VocabularyLearningState['vocabularyAnalysis']) => void;
}

// Initial states (matching existing context defaults)
const initialGameSessionState: GameSessionState = {
  selectedEpisode: null,
  currentScore: 0,
  totalQuestions: 0,
  correctAnswers: 0,
  gameStarted: false,
  gameCompleted: false,
  userAnswers: {},
};

const initialEpisodeProcessingState: EpisodeProcessingState = {
  isProcessing: false,
  processingStage: null,
};

const initialVocabularyLearningState: VocabularyLearningState = {
  knownWords: [],
  unknownWords: [],
  skippedWords: [],
  vocabularyAnalysis: null,
};

// Create the Zustand store
export const useAppStore = create<AppStore>()(devtools((set, get) => ({
  // Initial state
  gameSession: initialGameSessionState,
  episodeProcessing: initialEpisodeProcessingState,
  vocabularyLearning: initialVocabularyLearningState,
  
  // Game Session Actions
  selectEpisode: (episode: Episode) => {
    set((state) => ({
      gameSession: {
        ...initialGameSessionState,
        selectedEpisode: episode,
      }
    }), false, 'gameSession/selectEpisode');
  },
  
  startGame: () => {
    set((state) => ({
      gameSession: {
        ...state.gameSession,
        gameStarted: true,
        gameCompleted: false,
        totalQuestions: state.gameSession.selectedEpisode?.vocabularyWords.length || 0,
      }
    }), false, 'gameSession/startGame');
  },
  
  answerQuestion: (questionId: string, answer: string, isCorrect: boolean) => {
    set((state) => {
      const newUserAnswers = {
        ...state.gameSession.userAnswers,
        [questionId]: answer,
      };
      
      return {
        gameSession: {
          ...state.gameSession,
          userAnswers: newUserAnswers,
          correctAnswers: isCorrect
            ? state.gameSession.correctAnswers + 1
            : state.gameSession.correctAnswers,
          currentScore: isCorrect
            ? state.gameSession.currentScore + 10
            : state.gameSession.currentScore,
        }
      };
    }, false, 'gameSession/answerQuestion');
  },
  
  completeGame: () => {
    set((state) => ({
      gameSession: {
        ...state.gameSession,
        gameCompleted: true,
        gameStarted: false,
      }
    }), false, 'gameSession/completeGame');
  },
  
  resetGame: () => {
    set({ gameSession: initialGameSessionState }, false, 'gameSession/resetGame');
  },
  
  updateEpisodeStatus: (hasFilteredSubtitles: boolean, hasTranslatedSubtitles: boolean) => {
    set((state) => ({
      gameSession: {
        ...state.gameSession,
        selectedEpisode: state.gameSession.selectedEpisode ? {
          ...state.gameSession.selectedEpisode,
          hasFilteredSubtitles,
          hasTranslatedSubtitles,
        } : null,
      }
    }), false, 'gameSession/updateEpisodeStatus');
  },
  
  // Episode Processing Actions
  startProcessing: (stage: 'transcription' | 'filtering' | 'translation') => {
    set((state) => ({
      episodeProcessing: {
        ...state.episodeProcessing,
        isProcessing: true,
        processingStage: stage,
      }
    }), false, 'episodeProcessing/startProcessing');
  },
  
  updateProcessingProgress: (stage: 'transcription' | 'filtering' | 'translation' | 'complete') => {
    set((state) => ({
      episodeProcessing: {
        ...state.episodeProcessing,
        processingStage: stage,
      }
    }), false, 'episodeProcessing/updateProgress');
  },
  
  completeProcessing: () => {
    set((state) => ({
      episodeProcessing: {
        ...state.episodeProcessing,
        isProcessing: false,
        processingStage: 'complete',
      }
    }), false, 'episodeProcessing/completeProcessing');
  },
  
  // Vocabulary Learning Actions
  addKnownWord: (word: string) => {
    set((state) => ({
      vocabularyLearning: {
        ...state.vocabularyLearning,
        knownWords: [...state.vocabularyLearning.knownWords, word],
      }
    }), false, 'vocabularyLearning/addKnownWord');
  },
  
  addUnknownWord: (word: string) => {
    set((state) => ({
      vocabularyLearning: {
        ...state.vocabularyLearning,
        unknownWords: [...state.vocabularyLearning.unknownWords, word],
      }
    }), false, 'vocabularyLearning/addUnknownWord');
  },
  
  addSkippedWord: (word: string) => {
    set((state) => ({
      vocabularyLearning: {
        ...state.vocabularyLearning,
        skippedWords: [...state.vocabularyLearning.skippedWords, word],
      }
    }), false, 'vocabularyLearning/addSkippedWord');
  },
  
  setVocabularyAnalysis: (analysis: VocabularyLearningState['vocabularyAnalysis']) => {
    set((state) => ({
      vocabularyLearning: {
        ...state.vocabularyLearning,
        vocabularyAnalysis: analysis,
      }
    }), false, 'vocabularyLearning/setAnalysis');
  },
}), {
  name: 'episode-game-store', // DevTools name
}));

// Selector hooks for better performance and convenience
export const useGameSession = () => useAppStore((state) => state.gameSession);
export const useGameSessionActions = () => useAppStore((state) => ({
  selectEpisode: state.selectEpisode,
  startGame: state.startGame,
  answerQuestion: state.answerQuestion,
  completeGame: state.completeGame,
  resetGame: state.resetGame,
  updateEpisodeStatus: state.updateEpisodeStatus,
}));

export const useEpisodeProcessing = () => useAppStore((state) => state.episodeProcessing);
export const useEpisodeProcessingActions = () => useAppStore((state) => ({
  startProcessing: state.startProcessing,
  updateProcessingProgress: state.updateProcessingProgress,
  completeProcessing: state.completeProcessing,
}));

export const useVocabularyLearning = () => useAppStore((state) => state.vocabularyLearning);
export const useVocabularyLearningActions = () => useAppStore((state) => ({
  addKnownWord: state.addKnownWord,
  addUnknownWord: state.addUnknownWord,
  addSkippedWord: state.addSkippedWord,
  setVocabularyAnalysis: state.setVocabularyAnalysis,
}));

// Combined selectors for components that need multiple state slices
export const useGameAndProcessing = () => useAppStore((state) => ({
  gameSession: state.gameSession,
  episodeProcessing: state.episodeProcessing,
}));

export const useAllStates = () => useAppStore((state) => ({
  gameSession: state.gameSession,
  episodeProcessing: state.episodeProcessing,
  vocabularyLearning: state.vocabularyLearning,
}));