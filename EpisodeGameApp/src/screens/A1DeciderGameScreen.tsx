import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  Alert,
  Dimensions,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { useGameSession } from '../context/GameSessionContext';
import { useEpisodeProcessing } from '../context/EpisodeProcessingContext';
import { useVocabularyLearning } from '../context/VocabularyLearningContext';
import SubtitleService from '../services/SubtitleService';
import PythonBridgeService from '../services/PythonBridgeService';

// Import reusable components
import {
  ProcessingStatusIndicator,
  ProgressBar,
  VocabularyCard,
  StatsSummary,
  ActionButtonsRow,
  createGameStats,
  createCommonButtons,
} from '../components';
import { useProcessingWorkflow } from '../hooks';

interface ProcessingProgress {
  stage: 'transcription' | 'filtering' | 'translation' | 'complete';
  progress: number;
  message: string;
}

interface VocabularyWordWithStatus {
  word: string;
  isKnown?: boolean;
}

const { width } = Dimensions.get('window');

export default function A1DeciderGameScreen({ navigation }: any) {
  const { state, startGame, completeGame, updateEpisodeStatus } = useGameSession();
  const { state: processingState, startProcessing, updateProcessingProgress, completeProcessing } = useEpisodeProcessing();
  const { state: vocabularyState, addKnownWord, addUnknownWord, addSkippedWord, setVocabularyAnalysis } = useVocabularyLearning();
  const [gamePhase, setGamePhase] = useState<'processing' | 'vocabulary-check' | 'complete'>('processing');
  const [vocabularyWords, setVocabularyWords] = useState<VocabularyWordWithStatus[]>([]);
  const [currentWordIndex, setCurrentWordIndex] = useState(0);

  // Use the new processing workflow hook
  const processingWorkflow = useProcessingWorkflow({
    onStageChange: (stage) => {
      console.log('Processing stage changed to:', stage);
    },
    onComplete: (result) => {
      setGamePhase('vocabulary-check');
      completeProcessing();
    },
    onError: (stage, error) => {
      console.error(`Processing error in ${stage}:`, error);
      Alert.alert('Processing Error', `Error in ${stage}: ${error}`);
      completeProcessing();
    },
  });

  useEffect(() => {
    if (state.selectedEpisode) {
      initializeWorkflow();
    }
  }, [state.selectedEpisode]);

  const initializeWorkflow = async () => {
    if (!state.selectedEpisode) return;

    startProcessing();
    startGame();
    processingWorkflow.startProcessing();

    try {
      // Check if episode needs processing
      const status = await SubtitleService.checkSubtitleStatus(state.selectedEpisode);
      
      if (!status.isTranscribed || !status.hasFilteredSubtitles || !status.hasTranslatedSubtitles) {
        // Run the complete processing workflow with new hook integration
        await SubtitleService.processEpisode(state.selectedEpisode, (progress) => {
          updateProcessingProgress(progress.stage, progress.progress, progress.message);
          // Update the new workflow hook as well
          const stepId = progress.stage;
          processingWorkflow.updateStepProgress(stepId, progress.progress, progress.message);
          
          // Complete steps as they finish
          if (progress.progress >= 100) {
            processingWorkflow.completeStep(stepId, progress);
          }
        });
      } else {
        // If already processed, complete immediately
        processingWorkflow.completeStep('transcription', null);
        processingWorkflow.completeStep('filtering', null);
        processingWorkflow.completeStep('translation', null);
      }

      // Load real vocabulary for assessment
      const subtitleUrl = state.selectedEpisode.subtitleUrl;
      const vocabulary = await SubtitleService.loadRealVocabulary(subtitleUrl);
      const vocabularyWithStatus = vocabulary.map(vocabWord => ({ word: vocabWord.german, isKnown: undefined }));
      setVocabularyWords(vocabularyWithStatus);
      
    } catch (error) {
      console.error('Error in workflow:', error);
      Alert.alert('Error', 'Failed to process episode. Please try again.');
      processingWorkflow.failStep('transcription', 'Failed to process episode');
      completeProcessing();
    }
  };

  const handleWordKnowledge = (isKnown: boolean) => {
    const currentWord = vocabularyWords[currentWordIndex];
    if (!currentWord) return;

    if (isKnown) {
      addKnownWord(currentWord.word);
    } else {
      addUnknownWord(currentWord.word);
    }

    moveToNextWord();
  };

  const handleSkipWord = () => {
    const currentWord = vocabularyWords[currentWordIndex];
    if (!currentWord) return;

    addSkippedWord(currentWord.word);
    moveToNextWord();
  };

  const moveToNextWord = () => {
    if (currentWordIndex < vocabularyWords.length - 1) {
      setCurrentWordIndex(currentWordIndex + 1);
    } else {
      // Vocabulary check complete
      completeVocabularyCheck();
    }
  };

  const completeVocabularyCheck = () => {
    setGamePhase('complete');
    completeGame();
    
    // Update episode status to show all processing as complete
    updateEpisodeStatus(true, true);
    
    // Show summary
    Alert.alert(
      'Vocabulary Check Complete!',
      `Known words: ${vocabularyState.knownWords.length}\nUnknown words: ${vocabularyState.unknownWords.length}\nSkipped: ${vocabularyState.skippedWords.length}\n\nFiltered subtitles have been created with only unknown words.`,
      [
        {
          text: 'Watch Video',
          onPress: () => navigation.navigate('VideoPlayer')
        },
        {
          text: 'View Results',
          onPress: () => navigation.navigate('Results')
        }
      ]
    );
  };

  const handleWatchVideo = () => {
    navigation.navigate('VideoPlayer');
  };



  if (!state.selectedEpisode) {
    return (
      <SafeAreaView style={styles.container}>
        <Text style={styles.loadingText}>No episode selected</Text>
      </SafeAreaView>
    );
  }

  if (processingState.isProcessing) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.processingContainer}>
          <Text style={styles.episodeTitle}>{state.selectedEpisode.title}</Text>
          
          <ProcessingStatusIndicator
            currentStage={processingWorkflow.currentStage}
            stages={processingWorkflow.stages}
            overallProgress={processingState.progress || 0}
            currentMessage={processingState.message || 'Initializing...'}
          />
        </View>
      </SafeAreaView>
    );
  }

  if (gamePhase === 'vocabulary-check' && vocabularyWords.length > 0) {
    const currentWord = vocabularyWords[currentWordIndex];
    const progress = ((currentWordIndex + 1) / vocabularyWords.length) * 100;

    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.episodeTitle}>{state.selectedEpisode.title}</Text>
          <Text style={styles.subtitle}>Vocabulary Knowledge Check</Text>
          
          <ProgressBar
            progress={progress}
            label={`${currentWordIndex + 1} / ${vocabularyWords.length}`}
          />
        </View>

        <View style={styles.gameArea}>
          <VocabularyCard
            word={currentWord.word}
            question="Do you know this word?"
            onKnown={() => handleWordKnowledge(true)}
            onUnknown={() => handleWordKnowledge(false)}
            onSkip={handleSkipWord}
          />

          <StatsSummary
            stats={createGameStats({
              known: vocabularyState.knownWords.length,
              unknown: vocabularyState.unknownWords.length,
              skipped: vocabularyState.skippedWords.length,
              total: vocabularyWords.length,
            }, 'vocabulary')}
          />
        </View>

        <ActionButtonsRow
          buttons={createCommonButtons({
            onWatchVideo: handleWatchVideo,
          }, 'vocabulary')}
        />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.completeContainer}>
        <Text style={styles.completeTitle}>Processing Complete!</Text>
        <Text style={styles.completeMessage}>
          Your episode is ready with filtered subtitles containing only unknown words.
        </Text>
        
        <ActionButtonsRow
          buttons={createCommonButtons({
            onWatchVideo: handleWatchVideo,
          }, 'complete')}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  loadingText: {
    fontSize: 18,
    textAlign: 'center',
    marginTop: 50,
  },
  processingContainer: {
    flex: 1,
    padding: 20,
    justifyContent: 'center',
  },

  header: {
    backgroundColor: '#FFFFFF',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  episodeTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: '#666666',
    marginBottom: 12,
  },
  gameArea: {
    flex: 1,
    padding: 20,
    justifyContent: 'center',
  },

  completeContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  completeTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#4CAF50',
    marginBottom: 16,
    textAlign: 'center',
  },
  completeMessage: {
    fontSize: 16,
    color: '#666666',
    textAlign: 'center',
    marginBottom: 32,
    lineHeight: 24,
  },
});