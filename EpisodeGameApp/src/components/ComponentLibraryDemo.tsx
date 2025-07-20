import React, { useState, useEffect } from 'react';
import { View, ScrollView, Text, StyleSheet, Alert } from 'react-native';

// Import all components and hooks from the library
import {
  ProcessingStatusIndicator,
  ProgressBar,
  VocabularyCard,
  StatsSummary,
  VideoControls,
  SubtitleDisplay,
  ActionButtonsRow,
  createGameStats,
  createCommonButtons,
  defaultSubtitles,
} from './index';

import {
  useGameLogic,
  useProcessingWorkflow,
  generateSampleQuestions,
  formatTime,
  simulateProcessingStep,
} from '../hooks';

/**
 * ComponentLibraryDemo
 * 
 * This component demonstrates the usage of all reusable components and hooks
 * in the EpisodeGameApp component library. It serves as both documentation
 * and a testing ground for the components.
 */
const ComponentLibraryDemo: React.FC = () => {
  // Demo state for various components
  const [progressValue, setProgressValue] = useState(0);
  const [showSubtitles, setShowSubtitles] = useState(true);
  const [videoTime, setVideoTime] = useState(0);
  const [isVideoPlaying, setIsVideoPlaying] = useState(false);
  const [selectedVocabAnswer, setSelectedVocabAnswer] = useState<number | null>(null);
  const [showVocabResult, setShowVocabResult] = useState(false);

  // Game logic hook demonstration
  const gameLogic = useGameLogic({
    questions: generateSampleQuestions(5),
    timeLimit: 120,
    onGameComplete: (stats) => {
      Alert.alert('Game Complete!', `Final Score: ${stats.score}%`);
    },
    onQuestionAnswered: (questionId, isCorrect) => {
      console.log(`Question ${questionId}: ${isCorrect ? 'Correct' : 'Incorrect'}`);
    },
  });

  // Processing workflow hook demonstration
  const processingWorkflow = useProcessingWorkflow({
    onStageChange: (stage) => {
      console.log('Stage changed to:', stage);
    },
    onProgress: (stage, progress) => {
      console.log(`${stage} progress: ${progress}%`);
    },
    onComplete: (result) => {
      Alert.alert('Processing Complete!', 'All stages finished successfully.');
    },
    onError: (stage, error) => {
      Alert.alert('Processing Error', `Error in ${stage}: ${error}`);
    },
  });

  // Demo animations and updates
  useEffect(() => {
    // Animate progress bar
    const progressInterval = setInterval(() => {
      setProgressValue(prev => (prev >= 100 ? 0 : prev + 5));
    }, 200);

    // Simulate video time
    const videoInterval = setInterval(() => {
      if (isVideoPlaying) {
        setVideoTime(prev => (prev >= 300 ? 0 : prev + 1));
      }
    }, 1000);

    return () => {
      clearInterval(progressInterval);
      clearInterval(videoInterval);
    };
  }, [isVideoPlaying]);

  // Sample data for demonstrations
  const sampleVocabularyWord = {
    id: 'demo-word',
    text: 'What does "gracias" mean in English?',
    options: ['Hello', 'Goodbye', 'Thank you', 'Please'],
    correctAnswer: 2,
    explanation: '"Gracias" means "thank you" in Spanish.',
  };

  const sampleGameStats = createGameStats({
    correct: 8,
    incorrect: 2,
    total: 10,
    mode: 'results',
  });

  const sampleProcessingStages = [
    {
      id: 'transcription',
      name: 'Audio Transcription',
      status: 'completed' as const,
      progress: 100,
      message: 'Transcription completed successfully',
    },
    {
      id: 'filtering',
      name: 'Content Filtering',
      status: 'active' as const,
      progress: 65,
      message: 'Filtering vocabulary words...',
    },
    {
      id: 'translation',
      name: 'Translation Processing',
      status: 'pending' as const,
      progress: 0,
      message: 'Waiting for filtering to complete...',
    },
  ];

  const demoActionButtons = createCommonButtons({
    onWatchVideo: () => Alert.alert('Demo', 'Watch Video button pressed'),
    onPlayAgain: () => {
      gameLogic.resetGame();
      Alert.alert('Demo', 'Play Again button pressed');
    },
    onViewResults: () => Alert.alert('Demo', 'View Results button pressed'),
    onSubmit: () => {
      setShowVocabResult(true);
      Alert.alert('Demo', 'Submit button pressed');
    },
  });

  // Simulate processing step
  const handleStartProcessing = async () => {
    processingWorkflow.startProcessing();
    
    try {
      // Simulate transcription
      const transcriptionResult = await simulateProcessingStep(
        'transcription',
        (progress, message) => {
          processingWorkflow.updateStepProgress('transcription', progress, message);
        },
        2000
      );
      processingWorkflow.completeStep('transcription', transcriptionResult);

      // Simulate filtering
      const filteringResult = await simulateProcessingStep(
        'filtering',
        (progress, message) => {
          processingWorkflow.updateStepProgress('filtering', progress, message);
        },
        1500
      );
      processingWorkflow.completeStep('filtering', filteringResult);

      // Simulate translation
      const translationResult = await simulateProcessingStep(
        'translation',
        (progress, message) => {
          processingWorkflow.updateStepProgress('translation', progress, message);
        },
        1000
      );
      processingWorkflow.completeStep('translation', translationResult);
    } catch (error) {
      processingWorkflow.failStep('transcription', 'Simulation error');
    }
  };

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      <Text style={styles.title}>Component Library Demo</Text>
      <Text style={styles.subtitle}>
        Demonstrating all reusable components and hooks
      </Text>

      {/* Processing Status Indicator Demo */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Processing Status Indicator</Text>
        <ProcessingStatusIndicator
          stages={sampleProcessingStages}
          currentStage="filtering"
          onStagePress={(stage) => Alert.alert('Demo', `Pressed stage: ${stage.name}`)}
        />
        <ActionButtonsRow
          buttons={[
            {
              id: 'start-processing',
              title: 'Start Processing',
              onPress: handleStartProcessing,
              style: 'primary',
            },
            {
              id: 'reset-processing',
              title: 'Reset',
              onPress: processingWorkflow.resetProcessing,
              style: 'secondary',
            },
          ]}
          layout="horizontal"
        />
      </View>

      {/* Progress Bar Demo */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Progress Bar</Text>
        <ProgressBar
          progress={progressValue}
          showPercentage={true}
          color="#4CAF50"
        />
        <Text style={styles.demoText}>Animated progress: {progressValue}%</Text>
      </View>

      {/* Vocabulary Card Demo */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Vocabulary Card</Text>
        <VocabularyCard
          word={sampleVocabularyWord}
          selectedAnswer={selectedVocabAnswer}
          onAnswerSelect={setSelectedVocabAnswer}
          showResult={showVocabResult}
          disabled={showVocabResult}
        />
        <ActionButtonsRow
          buttons={[
            {
              id: 'reset-vocab',
              title: 'Reset',
              onPress: () => {
                setSelectedVocabAnswer(null);
                setShowVocabResult(false);
              },
              style: 'secondary',
            },
          ]}
          layout="horizontal"
        />
      </View>

      {/* Stats Summary Demo */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Stats Summary</Text>
        <StatsSummary
          stats={sampleGameStats}
          mode="results"
          showDetails={true}
        />
      </View>

      {/* Video Controls Demo */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Video Controls</Text>
        <VideoControls
          isPlaying={isVideoPlaying}
          currentTime={videoTime}
          duration={300}
          onPlayPause={() => setIsVideoPlaying(!isVideoPlaying)}
          onSeek={(time) => setVideoTime(time)}
          onSkip={() => setVideoTime(prev => Math.min(prev + 10, 300))}
        />
        <Text style={styles.demoText}>
          Current time: {formatTime(videoTime)} / {formatTime(300)}
        </Text>
      </View>

      {/* Subtitle Display Demo */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Subtitle Display</Text>
        <SubtitleDisplay
          subtitles={defaultSubtitles}
          currentTime={videoTime}
          showSubtitles={showSubtitles}
          onToggleSubtitles={() => setShowSubtitles(!showSubtitles)}
          onSubtitlePress={(subtitle) => {
            if (subtitle.startTime !== undefined) {
              setVideoTime(subtitle.startTime);
            }
            Alert.alert('Demo', `Jumped to: ${subtitle.text}`);
          }}
          highlightCurrent={true}
        />
      </View>

      {/* Action Buttons Demo */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Action Buttons Row</Text>
        <ActionButtonsRow
          buttons={demoActionButtons}
          layout="horizontal"
          spacing={12}
        />
      </View>

      {/* Game Logic Hook Demo */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Game Logic Hook Demo</Text>
        {gameLogic.isGameStarted ? (
          <View>
            <Text style={styles.demoText}>
              Question {gameLogic.currentQuestionIndex + 1} of {generateSampleQuestions(5).length}
            </Text>
            <Text style={styles.demoText}>
              Time remaining: {formatTime(gameLogic.timeRemaining)}
            </Text>
            <Text style={styles.demoText}>
              Score: {gameLogic.gameStats.score}% 
              ({gameLogic.gameStats.correct}/{gameLogic.gameStats.total})
            </Text>
            {gameLogic.currentQuestion && (
              <VocabularyCard
                word={gameLogic.currentQuestion}
                selectedAnswer={gameLogic.selectedAnswer}
                onAnswerSelect={gameLogic.selectAnswer}
                showResult={gameLogic.isAnswerSubmitted}
                disabled={gameLogic.isAnswerSubmitted}
              />
            )}
            <ActionButtonsRow
              buttons={[
                {
                  id: 'submit-game',
                  title: 'Submit',
                  onPress: gameLogic.submitAnswer,
                  style: 'success',
                  disabled: gameLogic.selectedAnswer === null || gameLogic.isAnswerSubmitted,
                },
                {
                  id: 'next-game',
                  title: 'Next',
                  onPress: gameLogic.nextQuestion,
                  style: 'primary',
                  disabled: !gameLogic.isAnswerSubmitted,
                },
                {
                  id: 'skip-game',
                  title: 'Skip',
                  onPress: gameLogic.skipQuestion,
                  style: 'warning',
                  disabled: gameLogic.isAnswerSubmitted,
                },
              ]}
              layout="horizontal"
            />
          </View>
        ) : (
          <ActionButtonsRow
            buttons={[
              {
                id: 'start-game',
                title: 'Start Game',
                onPress: gameLogic.startGame,
                style: 'primary',
              },
            ]}
            layout="horizontal"
          />
        )}
      </View>

      <View style={styles.footer}>
        <Text style={styles.footerText}>
          🎉 Component Library Demo Complete!
        </Text>
        <Text style={styles.footerSubtext}>
          All components are working and ready for integration.
        </Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
    padding: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333333',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666666',
    textAlign: 'center',
    marginBottom: 24,
  },
  section: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 12,
  },
  demoText: {
    fontSize: 14,
    color: '#666666',
    marginTop: 8,
    textAlign: 'center',
  },
  footer: {
    backgroundColor: '#E8F5E8',
    borderRadius: 12,
    padding: 20,
    marginTop: 16,
    marginBottom: 32,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2E7D32',
    marginBottom: 4,
  },
  footerSubtext: {
    fontSize: 14,
    color: '#4CAF50',
    textAlign: 'center',
  },
});

export default ComponentLibraryDemo;