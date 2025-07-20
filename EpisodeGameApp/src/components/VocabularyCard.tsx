import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ViewStyle } from 'react-native';

interface VocabularyCardProps {
  word: string;
  questionText?: string;
  options?: string[];
  selectedAnswer?: string;
  correctAnswer?: string;
  showResult?: boolean;
  onAnswerSelect?: (answer: string) => void;
  onKnown?: () => void;
  onUnknown?: () => void;
  onSkip?: () => void;
  mode?: 'knowledge-check' | 'multiple-choice' | 'display-only';
  style?: ViewStyle;
}

const VocabularyCard: React.FC<VocabularyCardProps> = ({
  word,
  questionText = 'Do you know this word?',
  options = [],
  selectedAnswer,
  correctAnswer,
  showResult = false,
  onAnswerSelect,
  onKnown,
  onUnknown,
  onSkip,
  mode = 'knowledge-check',
  style,
}) => {
  const renderKnowledgeCheckButtons = () => (
    <View style={styles.actionsContainer}>
      <TouchableOpacity
        style={[styles.actionButton, styles.knownButton]}
        onPress={onKnown}
      >
        <Text style={styles.actionButtonText}>✓ I Know It</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.actionButton, styles.unknownButton]}
        onPress={onUnknown}
      >
        <Text style={styles.actionButtonText}>✗ Don't Know</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.actionButton, styles.skipButton]}
        onPress={onSkip}
      >
        <Text style={styles.actionButtonText}>⏭ Skip</Text>
      </TouchableOpacity>
    </View>
  );

  const renderMultipleChoiceOptions = () => (
    <View style={styles.optionsContainer}>
      {options.map((option, index) => {
        let buttonStyle = [styles.optionButton];
        let textStyle = [styles.optionText];

        if (showResult) {
          if (option === correctAnswer) {
            buttonStyle.push(styles.correctOption);
            textStyle.push(styles.correctOptionText);
          } else if (option === selectedAnswer && option !== correctAnswer) {
            buttonStyle.push(styles.incorrectOption);
            textStyle.push(styles.incorrectOptionText);
          }
        } else if (selectedAnswer === option) {
          buttonStyle.push(styles.selectedOption);
          textStyle.push(styles.selectedOptionText);
        }

        return (
          <TouchableOpacity
            key={index}
            style={buttonStyle}
            onPress={() => onAnswerSelect?.(option)}
            disabled={showResult}
          >
            <Text style={textStyle}>{option}</Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );

  const renderDisplayOnly = () => (
    <View style={styles.displayContainer}>
      <Text style={styles.displayWord}>{word}</Text>
    </View>
  );

  return (
    <View style={[styles.container, style]}>
      <View style={styles.questionContainer}>
        <Text style={styles.questionText}>{questionText}</Text>
        <Text style={styles.wordText}>{word}</Text>
      </View>

      {mode === 'knowledge-check' && renderKnowledgeCheckButtons()}
      {mode === 'multiple-choice' && renderMultipleChoiceOptions()}
      {mode === 'display-only' && renderDisplayOnly()}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    marginVertical: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  questionContainer: {
    alignItems: 'center',
    marginBottom: 20,
  },
  questionText: {
    fontSize: 18,
    color: '#666666',
    marginBottom: 12,
    textAlign: 'center',
  },
  wordText: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#333333',
    textAlign: 'center',
  },
  actionsContainer: {
    gap: 12,
  },
  actionButton: {
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  knownButton: {
    backgroundColor: '#4CAF50',
  },
  unknownButton: {
    backgroundColor: '#F44336',
  },
  skipButton: {
    backgroundColor: '#FF9800',
  },
  actionButtonText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: 'bold',
  },
  optionsContainer: {
    gap: 12,
  },
  optionButton: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#E0E0E0',
  },
  selectedOption: {
    borderColor: '#2196F3',
    backgroundColor: '#E3F2FD',
  },
  correctOption: {
    borderColor: '#4CAF50',
    backgroundColor: '#E8F5E8',
  },
  incorrectOption: {
    borderColor: '#F44336',
    backgroundColor: '#FFEBEE',
  },
  optionText: {
    fontSize: 16,
    color: '#333333',
    textAlign: 'center',
  },
  selectedOptionText: {
    color: '#2196F3',
    fontWeight: '500',
  },
  correctOptionText: {
    color: '#4CAF50',
    fontWeight: '500',
  },
  incorrectOptionText: {
    color: '#F44336',
    fontWeight: '500',
  },
  displayContainer: {
    alignItems: 'center',
    padding: 10,
  },
  displayWord: {
    fontSize: 18,
    color: '#333333',
    fontWeight: '500',
  },
});

export default VocabularyCard;