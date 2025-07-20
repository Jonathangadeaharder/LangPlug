// Custom Hooks for EpisodeGameApp

// Game Logic Hook
export { default as useGameLogic } from './useGameLogic';
export { formatTime, generateSampleQuestions } from './useGameLogic';

// Processing Workflow Hook
export { default as useProcessingWorkflow } from './useProcessingWorkflow';
export { simulateProcessingStep } from './useProcessingWorkflow';

// Export hook types
export type { ProcessingStage } from './useProcessingWorkflow';