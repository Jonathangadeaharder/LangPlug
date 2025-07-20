import React, { createContext, useContext, useReducer, ReactNode } from 'react';

interface EpisodeProcessingState {
  isProcessing: boolean;
  processingStage: 'transcription' | 'filtering' | 'translation' | 'complete' | null;
}

type EpisodeProcessingAction =
  | { type: 'START_PROCESSING'; payload: { stage: 'transcription' | 'filtering' | 'translation' } }
  | { type: 'UPDATE_PROCESSING_PROGRESS'; payload: { stage: 'transcription' | 'filtering' | 'translation' | 'complete' } }
  | { type: 'COMPLETE_PROCESSING' };

const initialState: EpisodeProcessingState = {
  isProcessing: false,
  processingStage: null,
};

function episodeProcessingReducer(state: EpisodeProcessingState, action: EpisodeProcessingAction): EpisodeProcessingState {
  switch (action.type) {
    case 'START_PROCESSING':
      return {
        ...state,
        isProcessing: true,
        processingStage: action.payload.stage,
      };
    case 'UPDATE_PROCESSING_PROGRESS':
      return {
        ...state,
        processingStage: action.payload.stage,
      };
    case 'COMPLETE_PROCESSING':
      return {
        ...state,
        isProcessing: false,
        processingStage: 'complete',
      };
    default:
      return state;
  }
}

interface EpisodeProcessingContextType {
  state: EpisodeProcessingState;
  dispatch: React.Dispatch<EpisodeProcessingAction>;
  startProcessing: (stage: 'transcription' | 'filtering' | 'translation') => void;
  updateProcessingProgress: (stage: 'transcription' | 'filtering' | 'translation' | 'complete') => void;
  completeProcessing: () => void;
}

const EpisodeProcessingContext = createContext<EpisodeProcessingContextType | undefined>(undefined);

export function EpisodeProcessingProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(episodeProcessingReducer, initialState);

  const startProcessing = (stage: 'transcription' | 'filtering' | 'translation') => {
    dispatch({ type: 'START_PROCESSING', payload: { stage } });
  };

  const updateProcessingProgress = (stage: 'transcription' | 'filtering' | 'translation' | 'complete') => {
    dispatch({ type: 'UPDATE_PROCESSING_PROGRESS', payload: { stage } });
  };

  const completeProcessing = () => {
    dispatch({ type: 'COMPLETE_PROCESSING' });
  };

  return (
    <EpisodeProcessingContext.Provider
      value={{
        state,
        dispatch,
        startProcessing,
        updateProcessingProgress,
        completeProcessing,
      }}
    >
      {children}
    </EpisodeProcessingContext.Provider>
  );
}

export function useEpisodeProcessing() {
  const context = useContext(EpisodeProcessingContext);
  if (context === undefined) {
    throw new Error('useEpisodeProcessing must be used within a EpisodeProcessingProvider');
  }
  return context;
}
