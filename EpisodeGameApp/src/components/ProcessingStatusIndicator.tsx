import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';

interface ProcessingStep {
  id: string;
  name: string;
  number: number;
}

interface ProcessingStatusIndicatorProps {
  currentStage: 'transcription' | 'filtering' | 'translation' | 'complete' | null;
  progress: number;
  message: string;
  isProcessing: boolean;
  steps?: ProcessingStep[];
}

const defaultSteps: ProcessingStep[] = [
  { id: 'transcription', name: 'Transcribe', number: 1 },
  { id: 'filtering', name: 'Filter', number: 2 },
  { id: 'translation', name: 'Translate', number: 3 },
];

const ProcessingStatusIndicator: React.FC<ProcessingStatusIndicatorProps> = ({
  currentStage,
  progress,
  message,
  isProcessing,
  steps = defaultSteps,
}) => {
  const getProgressColor = () => {
    if (!currentStage) return '#4CAF50';
    
    switch (currentStage) {
      case 'transcription': return '#FF9800';
      case 'filtering': return '#2196F3';
      case 'translation': return '#9C27B0';
      case 'complete': return '#4CAF50';
      default: return '#4CAF50';
    }
  };

  const getStageTitle = () => {
    if (!currentStage) return 'Processing';
    
    switch (currentStage) {
      case 'transcription': return 'Creating Subtitles';
      case 'filtering': return 'Analyzing Vocabulary';
      case 'translation': return 'Translating Subtitles';
      case 'complete': return 'Complete';
      default: return 'Processing';
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.processingCard}>
        <Text style={styles.stageTitle}>{getStageTitle()}</Text>
        
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <View 
              style={[
                styles.progressFill, 
                { 
                  width: `${progress || 0}%`,
                  backgroundColor: getProgressColor()
                }
              ]} 
            />
          </View>
          <Text style={styles.progressText}>
            {progress || 0}%
          </Text>
        </View>
        
        <Text style={styles.progressMessage}>
          {message || 'Initializing...'}
        </Text>
        
        {isProcessing && (
          <ActivityIndicator 
            size="large" 
            color={getProgressColor()} 
            style={styles.spinner}
          />
        )}
      </View>
      
      <View style={styles.stageIndicators}>
        {steps.map((step) => (
          <View 
            key={step.id}
            style={[
              styles.stageIndicator, 
              currentStage === step.id && styles.activeStage
            ]}
          >
            <Text style={styles.stageNumber}>{step.number}</Text>
            <Text style={styles.stageName}>{step.name}</Text>
          </View>
        ))}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 20,
  },
  processingCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 24,
    marginVertical: 20,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  stageTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 20,
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    width: '100%',
    marginBottom: 16,
  },
  progressBar: {
    flex: 1,
    height: 8,
    backgroundColor: '#E0E0E0',
    borderRadius: 4,
    marginRight: 12,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
    borderRadius: 4,
  },
  progressText: {
    fontSize: 14,
    color: '#666666',
    fontWeight: '500',
    minWidth: 40,
  },
  progressMessage: {
    fontSize: 16,
    color: '#666666',
    textAlign: 'center',
    marginBottom: 20,
  },
  spinner: {
    marginTop: 10,
  },
  stageIndicators: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
  },
  stageIndicator: {
    alignItems: 'center',
    opacity: 0.5,
  },
  activeStage: {
    opacity: 1,
  },
  stageNumber: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#4CAF50',
    marginBottom: 4,
  },
  stageName: {
    fontSize: 12,
    color: '#666666',
  },
});

export default ProcessingStatusIndicator;