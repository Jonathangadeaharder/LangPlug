import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import { Episode } from '../models/Episode';

interface GameSessionState {
  selectedEpisode: Episode | null;
  currentScore: number;
  totalQuestions: number;
  correctAnswers: number;
  gameStarted: boolean;
  gameCompleted: boolean;
  userAnswers: { [key: string]: string };
}

type GameSessionAction =
  | { type: 'SELECT_EPISODE'; payload: Episode }
  | { type: 'START_GAME' }
  | { type: 'ANSWER_QUESTION'; payload: { questionId: string; answer: string; isCorrect: boolean } }
  | { type: 'COMPLETE_GAME' }
  | { type: 'RESET_GAME' }
  | { type: 'UPDATE_EPISODE_STATUS'; payload: { hasFilteredSubtitles: boolean; hasTranslatedSubtitles: boolean } };

const initialState: GameSessionState = {
  selectedEpisode: null,
  currentScore: 0,
  totalQuestions: 0,
  correctAnswers: 0,
  gameStarted: false,
  gameCompleted: false,
  userAnswers: {},
};

function gameSessionReducer(state: GameSessionState, action: GameSessionAction): GameSessionState {
  switch (action.type) {
    case 'SELECT_EPISODE':
      return {
        ...state,
        selectedEpisode: action.payload,
        gameStarted: false,
        gameCompleted: false,
        currentScore: 0,
        correctAnswers: 0,
        userAnswers: {},
      };
    case 'START_GAME':
      return {
        ...state,
        gameStarted: true,
        gameCompleted: false,
        totalQuestions: state.selectedEpisode?.vocabularyWords.length || 0,
      };
    case 'ANSWER_QUESTION':
      const newUserAnswers = {
        ...state.userAnswers,
        [action.payload.questionId]: action.payload.answer,
      };
      return {
        ...state,
        userAnswers: newUserAnswers,
        correctAnswers: action.payload.isCorrect
          ? state.correctAnswers + 1
          : state.correctAnswers,
        currentScore: action.payload.isCorrect
          ? state.currentScore + 10
          : state.currentScore,
      };
    case 'COMPLETE_GAME':
      return {
        ...state,
        gameCompleted: true,
        gameStarted: false,
      };
    case 'RESET_GAME':
      return initialState;
    case 'UPDATE_EPISODE_STATUS':
      return {
        ...state,
        selectedEpisode: state.selectedEpisode ? {
          ...state.selectedEpisode,
          hasFilteredSubtitles: action.payload.hasFilteredSubtitles,
          hasTranslatedSubtitles: action.payload.hasTranslatedSubtitles,
        } : null,
      };
    default:
      return state;
  }
}

interface GameSessionContextType {
  state: GameSessionState;
  dispatch: React.Dispatch<GameSessionAction>;
  selectEpisode: (episode: Episode) => void;
  startGame: () => void;
  answerQuestion: (questionId: string, answer: string, isCorrect: boolean) => void;
  completeGame: () => void;
  resetGame: () => void;
  updateEpisodeStatus: (hasFilteredSubtitles: boolean, hasTranslatedSubtitles: boolean) => void;
}

const GameSessionContext = createContext<GameSessionContextType | undefined>(undefined);

export function GameSessionProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(gameSessionReducer, initialState);

  const selectEpisode = (episode: Episode) => {
    dispatch({ type: 'SELECT_EPISODE', payload: episode });
  };

  const startGame = () => {
    dispatch({ type: 'START_GAME' });
  };

  const answerQuestion = (questionId: string, answer: string, isCorrect: boolean) => {
    dispatch({ type: 'ANSWER_QUESTION', payload: { questionId, answer, isCorrect } });
  };

  const completeGame = () => {
    dispatch({ type: 'COMPLETE_GAME' });
  };

  const resetGame = () => {
    dispatch({ type: 'RESET_GAME' });
  };

  const updateEpisodeStatus = (hasFilteredSubtitles: boolean, hasTranslatedSubtitles: boolean) => {
    dispatch({ type: 'UPDATE_EPISODE_STATUS', payload: { hasFilteredSubtitles, hasTranslatedSubtitles } });
  };

  return (
    <GameSessionContext.Provider
      value={{
        state,
        dispatch,
        selectEpisode,
        startGame,
        answerQuestion,
        completeGame,
        resetGame,
        updateEpisodeStatus,
      }}
    >
      {children}
    </GameSessionContext.Provider>
  );
}

export function useGameSession() {
  const context = useContext(GameSessionContext);
  if (context === undefined) {
    throw new Error('useGameSession must be used within a GameSessionProvider');
  }
  return context;
}
