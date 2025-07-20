import React, { createContext, useContext, useReducer, ReactNode } from 'react';

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

type VocabularyLearningAction =
  | { type: 'ADD_KNOWN_WORD'; payload: string }
  | { type: 'ADD_UNKNOWN_WORD'; payload: string }
  | { type: 'ADD_SKIPPED_WORD'; payload: string }
  | { type: 'SET_VOCABULARY_ANALYSIS'; payload: VocabularyLearningState['vocabularyAnalysis'] };

const initialState: VocabularyLearningState = {
  knownWords: [],
  unknownWords: [],
  skippedWords: [],
  vocabularyAnalysis: null,
};

function vocabularyLearningReducer(state: VocabularyLearningState, action: VocabularyLearningAction): VocabularyLearningState {
  switch (action.type) {
    case 'ADD_KNOWN_WORD':
      return {
        ...state,
        knownWords: [...state.knownWords, action.payload],
      };
    case 'ADD_UNKNOWN_WORD':
      return {
        ...state,
        unknownWords: [...state.unknownWords, action.payload],
      };
    case 'ADD_SKIPPED_WORD':
      return {
        ...state,
        skippedWords: [...state.skippedWords, action.payload],
      };
    case 'SET_VOCABULARY_ANALYSIS':
      return {
        ...state,
        vocabularyAnalysis: action.payload,
      };
    default:
      return state;
  }
}

interface VocabularyLearningContextType {
  state: VocabularyLearningState;
  dispatch: React.Dispatch<VocabularyLearningAction>;
  addKnownWord: (word: string) => void;
  addUnknownWord: (word: string) => void;
  addSkippedWord: (word: string) => void;
  setVocabularyAnalysis: (analysis: VocabularyLearningState['vocabularyAnalysis']) => void;
}

const VocabularyLearningContext = createContext<VocabularyLearningContextType | undefined>(undefined);

export function VocabularyLearningProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(vocabularyLearningReducer, initialState);

  const addKnownWord = (word: string) => {
    dispatch({ type: 'ADD_KNOWN_WORD', payload: word });
  };

  const addUnknownWord = (word: string) => {
    dispatch({ type: 'ADD_UNKNOWN_WORD', payload: word });
  };

  const addSkippedWord = (word: string) => {
    dispatch({ type: 'ADD_SKIPPED_WORD', payload: word });
  };

  const setVocabularyAnalysis = (analysis: VocabularyLearningState['vocabularyAnalysis']) => {
    dispatch({ type: 'SET_VOCABULARY_ANALYSIS', payload: analysis });
  };

  return (
    <VocabularyLearningContext.Provider
      value={{
        state,
        dispatch,
        addKnownWord,
        addUnknownWord,
        addSkippedWord,
        setVocabularyAnalysis,
      }}
    >
      {children}
    </VocabularyLearningContext.Provider>
  );
}

export function useVocabularyLearning() {
  const context = useContext(VocabularyLearningContext);
  if (context === undefined) {
    throw new Error('useVocabularyLearning must be used within a VocabularyLearningProvider');
  }
  return context;
}
