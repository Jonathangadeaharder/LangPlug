import React, { ReactNode } from 'react';
import { EpisodeProcessingProvider } from './EpisodeProcessingContext';
import { VocabularyLearningProvider } from './VocabularyLearningContext';
import { GameSessionProvider } from './GameSessionContext';

export function GlobalStateProvider({ children }: { children: ReactNode }) {
  return (
    <EpisodeProcessingProvider>
      <VocabularyLearningProvider>
        <GameSessionProvider>
          {children}
        </GameSessionProvider>
      </VocabularyLearningProvider>
    </EpisodeProcessingProvider>
  );
}
