# Zustand Migration Guide

This guide provides step-by-step instructions for migrating from React Context API to Zustand state management.

## Overview

The migration replaces three separate Context providers with a unified Zustand store:
- `GameSessionContext` → `useAppStore` (gameSession slice)
- `EpisodeProcessingContext` → `useAppStore` (episodeProcessing slice)
- `VocabularyLearningContext` → `useAppStore` (vocabularyLearning slice)

## Migration Steps

### Step 1: Install Dependencies

```bash
npm install zustand
```

### Step 2: Import the New Store

Replace context imports with Zustand store imports:

**Before:**
```typescript
import { useGameSession } from '../context/GameSessionContext';
import { useEpisodeProcessing } from '../context/EpisodeProcessingContext';
import { useVocabularyLearning } from '../context/VocabularyLearningContext';
```

**After:**
```typescript
import {
  useGameSession,
  useGameSessionActions,
  useEpisodeProcessing,
  useEpisodeProcessingActions,
  useVocabularyLearning,
  useVocabularyLearningActions,
} from '../stores/useAppStore';
```

### Step 3: Update Component Usage

#### Pattern 1: State + Actions (Most Common)

**Before (Context API):**
```typescript
const { state, startGame, completeGame, updateEpisodeStatus } = useGameSession();
const { state: processingState, startProcessing, completeProcessing } = useEpisodeProcessing();
const { addKnownWord, addUnknownWord, addSkippedWord } = useVocabularyLearning();
```

**After (Zustand):**
```typescript
const gameState = useGameSession();
const { startGame, completeGame, updateEpisodeStatus } = useGameSessionActions();
const processingState = useEpisodeProcessing();
const { startProcessing, completeProcessing } = useEpisodeProcessingActions();
const { addKnownWord, addUnknownWord, addSkippedWord } = useVocabularyLearningActions();
```

#### Pattern 2: Selective State Access

**Before:**
```typescript
const { state } = useGameSession();
const selectedEpisode = state.selectedEpisode;
const gameStarted = state.gameStarted;
```

**After:**
```typescript
// Option 1: Get full state
const gameState = useGameSession();
const selectedEpisode = gameState.selectedEpisode;
const gameStarted = gameState.gameStarted;

// Option 2: Selective subscription (better performance)
const selectedEpisode = useAppStore(state => state.gameSession.selectedEpisode);
const gameStarted = useAppStore(state => state.gameSession.gameStarted);
```

#### Pattern 3: Multiple State Slices

**Before:**
```typescript
const { state: gameState } = useGameSession();
const { state: processingState } = useEpisodeProcessing();
const { state: vocabularyState } = useVocabularyLearning();
```

**After:**
```typescript
// Option 1: Individual hooks
const gameState = useGameSession();
const processingState = useEpisodeProcessing();
const vocabularyState = useVocabularyLearning();

// Option 2: Combined selector (for components using all states)
const { gameSession, episodeProcessing, vocabularyLearning } = useAllStates();
```

## Component Migration Examples

### Example 1: GameScreen.tsx

**Before:**
```typescript
export default function GameScreen({ navigation }: any) {
  const { state, startGame, answerQuestion, completeGame } = useGameSession();
  
  useEffect(() => {
    if (state.selectedEpisode) {
      generateQuestions();
      startGame();
    }
  }, [state.selectedEpisode]);
  
  // Component logic...
}
```

**After:**
```typescript
export default function GameScreen({ navigation }: any) {
  const gameState = useGameSession();
  const { startGame, answerQuestion, completeGame } = useGameSessionActions();
  
  useEffect(() => {
    if (gameState.selectedEpisode) {
      generateQuestions();
      startGame();
    }
  }, [gameState.selectedEpisode]);
  
  // Component logic...
}
```

### Example 2: A1DeciderGameScreen.tsx (Complex Multi-Context)

**Before:**
```typescript
export default function A1DeciderGameScreen({ navigation }: any) {
  const { state, startGame, completeGame, updateEpisodeStatus } = useGameSession();
  const { state: processingState, startProcessing, updateProcessingProgress, completeProcessing } = useEpisodeProcessing();
  const { state: vocabularyState, addKnownWord, addUnknownWord, addSkippedWord } = useVocabularyLearning();
  
  // Component logic...
}
```

**After:**
```typescript
export default function A1DeciderGameScreen({ navigation }: any) {
  const gameState = useGameSession();
  const { startGame, completeGame, updateEpisodeStatus } = useGameSessionActions();
  const processingState = useEpisodeProcessing();
  const { startProcessing, updateProcessingProgress, completeProcessing } = useEpisodeProcessingActions();
  const vocabularyState = useVocabularyLearning();
  const { addKnownWord, addUnknownWord, addSkippedWord } = useVocabularyLearningActions();
  
  // Component logic...
}
```

## Performance Optimizations

### 1. Selective Subscriptions

For better performance, subscribe only to the state you need:

```typescript
// Instead of:
const gameState = useGameSession();
const isGameStarted = gameState.gameStarted;

// Use:
const isGameStarted = useAppStore(state => state.gameSession.gameStarted);
```

### 2. Multiple Selections with useShallow

```typescript
import { useShallow } from 'zustand/react/shallow';

// For multiple related properties:
const { currentScore, correctAnswers } = useAppStore(
  useShallow(state => ({
    currentScore: state.gameSession.currentScore,
    correctAnswers: state.gameSession.correctAnswers,
  }))
);
```

### 3. Action-Only Subscriptions

```typescript
// When you only need actions (no re-renders on state changes):
const actions = useGameSessionActions();
```

## Testing Updates

### Update Test Files

**Before:**
```typescript
import { GlobalStateProvider } from '../GlobalStateProvider';

const TestComponent = () => {
  const { state: gameState } = useGameSession();
  return <div>{gameState.selectedEpisode?.title}</div>;
};

render(
  <GlobalStateProvider>
    <TestComponent />
  </GlobalStateProvider>
);
```

**After:**
```typescript
import { useGameSession } from '../stores/useAppStore';

const TestComponent = () => {
  const gameState = useGameSession();
  return <div>{gameState.selectedEpisode?.title}</div>;
};

// No provider needed!
render(<TestComponent />);
```

## Migration Checklist

### Phase 1: Setup
- [ ] Install Zustand
- [ ] Create `src/stores/useAppStore.ts`
- [ ] Verify store structure matches existing contexts

### Phase 2: Component Migration
- [ ] Update `GameScreen.tsx`
- [ ] Update `A1DeciderGameScreen.tsx`
- [ ] Update `EpisodeSelectionScreen.tsx`
- [ ] Update `ResultsScreen.tsx`
- [ ] Update any other components using contexts

### Phase 3: Cleanup
- [ ] Remove `GlobalStateProvider` from `App.tsx`
- [ ] Delete context files:
  - [ ] `src/context/GameSessionContext.tsx`
  - [ ] `src/context/EpisodeProcessingContext.tsx`
  - [ ] `src/context/VocabularyLearningContext.tsx`
  - [ ] `src/context/GlobalStateProvider.tsx`
- [ ] Update test files
- [ ] Remove unused imports

### Phase 4: Optimization
- [ ] Add selective subscriptions where beneficial
- [ ] Implement `useShallow` for multi-property selections
- [ ] Add performance monitoring
- [ ] Update documentation

## Common Pitfalls and Solutions

### 1. State Structure Changes

**Problem:** Accessing nested state differently

**Before:**
```typescript
const { state } = useGameSession();
const episode = state.selectedEpisode;
```

**After:**
```typescript
const gameState = useGameSession();
const episode = gameState.selectedEpisode;
```

### 2. Action Patterns

**Problem:** Actions are now separate from state

**Solution:** Use dedicated action hooks or direct store access

### 3. Provider Removal

**Problem:** Components expecting providers

**Solution:** Zustand works without providers - remove `GlobalStateProvider` wrapper

## Benefits After Migration

1. **Performance**: Selective re-renders reduce unnecessary updates
2. **Bundle Size**: Smaller footprint compared to multiple contexts
3. **Developer Experience**: Better debugging with Zustand DevTools
4. **Maintainability**: Centralized state management
5. **Scalability**: Better suited for app growth

## Rollback Plan

If issues arise during migration:

1. Keep original context files until migration is complete
2. Use feature flags to switch between implementations
3. Migrate one component at a time
4. Test thoroughly at each step

The migration can be done incrementally, allowing for safe rollback at any point.