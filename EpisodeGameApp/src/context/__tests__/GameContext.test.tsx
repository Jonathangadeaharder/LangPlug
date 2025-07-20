import React from 'react';
import { render, act } from '@testing-library/react-native';
import { useAppStore } from '../../store/useAppStore';
import { defaultEpisodes } from '../../models/Episode';

// Test component to access Zustand store
const TestComponent = () => {
  const { gameState } = useAppStore();
  const { selectEpisode, startGame, completeGame, updateEpisodeStatus, startProcessing, updateProcessingProgress, completeProcessing, addKnownWord } = useAppStore();

  return (
    <>
      <div testID="current-episode">{gameState.selectedEpisode?.title || 'No episode'}</div>
      <div testID="game-started">{gameState.gameStarted.toString()}</div>
      <div testID="game-completed">{gameState.gameCompleted.toString()}</div>
      <div testID="is-processing">{gameState.isProcessing.toString()}</div>
      <div testID="processing-stage">{gameState.processingStage}</div>
      <div testID="known-words">{gameState.knownWords.length.toString()}</div>
      <button testID="select-episode" onPress={() => selectEpisode(defaultEpisodes[0])} />
      <button testID="start-game" onPress={() => startGame()} />
      <button testID="complete-game" onPress={() => completeGame()} />
      <button testID="start-processing" onPress={() => startProcessing('transcription')} />
      <button testID="update-processing" onPress={() => updateProcessingProgress('filtering')} />
      <button testID="complete-processing" onPress={() => completeProcessing()} />
      <button testID="add-known-word" onPress={() => addKnownWord('test')} />
      <button testID="update-status" onPress={() => updateEpisodeStatus(true, true)} />
    </>
  );
};

const renderWithProvider = () => {
  return render(<TestComponent />);
};

describe('Zustand Store Integration', () => {
  it('should provide initial state', () => {
    const { getByTestId } = renderWithProvider();

    expect(getByTestId('current-episode')).toHaveTextContent('No episode');
    expect(getByTestId('game-started')).toHaveTextContent('false');
    expect(getByTestId('game-completed')).toHaveTextContent('false');
    expect(getByTestId('is-processing')).toHaveTextContent('false');
    expect(getByTestId('processing-stage')).toHaveTextContent('');
    expect(getByTestId('known-words')).toHaveTextContent('0');
  });

  it('should start game correctly', () => {
    const { getByTestId } = renderWithProvider();

    // First select an episode
    act(() => {
      getByTestId('select-episode').props.onPress();
    });

    // Then start the game
    act(() => {
      getByTestId('start-game').props.onPress();
    });

    expect(getByTestId('current-episode')).toHaveTextContent(defaultEpisodes[0].title);
    expect(getByTestId('game-started')).toHaveTextContent('true');
    expect(getByTestId('game-completed')).toHaveTextContent('false');
  });

  it('should complete game correctly', () => {
    const { getByTestId } = renderWithProvider();

    // Select episode and start game first
    act(() => {
      getByTestId('select-episode').props.onPress();
    });
    
    act(() => {
      getByTestId('start-game').props.onPress();
    });

    // Complete game
    act(() => {
      getByTestId('complete-game').props.onPress();
    });

    expect(getByTestId('game-started')).toHaveTextContent('false');
    expect(getByTestId('game-completed')).toHaveTextContent('true');
  });

  it('should handle processing workflow', () => {
    const { getByTestId } = renderWithProvider();

    // Start processing
    act(() => {
      getByTestId('start-processing').props.onPress();
    });

    expect(getByTestId('is-processing')).toHaveTextContent('true');
    expect(getByTestId('processing-stage')).toHaveTextContent('transcription');

    // Update processing progress
    act(() => {
      getByTestId('update-processing').props.onPress();
    });

    expect(getByTestId('processing-stage')).toHaveTextContent('filtering');

    // Complete processing
    act(() => {
      getByTestId('complete-processing').props.onPress();
    });

    expect(getByTestId('is-processing')).toHaveTextContent('false');
    expect(getByTestId('processing-stage')).toHaveTextContent('complete');
  });

  it('should handle vocabulary learning', () => {
    const { getByTestId } = renderWithProvider();

    // Add known word
    act(() => {
      getByTestId('add-known-word').props.onPress();
    });

    expect(getByTestId('known-words')).toHaveTextContent('1');
  });

  it('should handle multiple state changes across contexts', () => {
    const { getByTestId } = renderWithProvider();

    // Select episode and start game
    act(() => {
      getByTestId('select-episode').props.onPress();
    });
    
    act(() => {
      getByTestId('start-game').props.onPress();
    });

    // Start processing
    act(() => {
      getByTestId('start-processing').props.onPress();
    });

    // Add vocabulary
    act(() => {
      getByTestId('add-known-word').props.onPress();
    });

    // Complete game
    act(() => {
      getByTestId('complete-game').props.onPress();
    });

    expect(getByTestId('game-started')).toHaveTextContent('false');
    expect(getByTestId('game-completed')).toHaveTextContent('true');
    expect(getByTestId('is-processing')).toHaveTextContent('true');
    expect(getByTestId('known-words')).toHaveTextContent('1');
  });
});