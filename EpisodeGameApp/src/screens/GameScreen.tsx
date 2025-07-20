import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  Alert,
  Dimensions,
} from 'react-native';
import { useGameSession } from '../context/GameSessionContext';

// Import reusable components
import {
  ProgressBar,
  VocabularyCard,
  StatsSummary,
  ActionButtonsRow,
  createGameStats,
  createCommonButtons,
} from '../components';
import { useGameLogic } from '../hooks';

interface Question {
  id: string;
  word: string;
  options: string[];
  correctAnswer: string;
}

const { width } = Dimensions.get('window');

export default function GameScreen({ navigation }: any) {
  const { state, startGame, answerQuestion, completeGame } = useGameSession();
  const [questions, setQuestions] = useState<Question[]>([]);
  
  // Use the new game logic hook
  const gameLogic = useGameLogic({
    onGameComplete: () => {
      completeGame();
      navigation.navigate('Results');
    },
    onAnswerSubmitted: (questionId, answer, isCorrect) => {
      answerQuestion(questionId, answer, isCorrect);
    },
  });

  useEffect(() => {
    if (state.selectedEpisode) {
      generateQuestions();
      startGame();
      gameLogic.startGame();
    }
  }, [state.selectedEpisode]);

  useEffect(() => {
    if (questions.length > 0) {
      gameLogic.setQuestions(questions);
    }
  }, [questions]);

  const generateQuestions = () => {
    if (!state.selectedEpisode) return;

    const generatedQuestions: Question[] = state.selectedEpisode.vocabularyWords.map((word, index) => {
      // Generate fake options for multiple choice
      const fakeOptions = [
        'option1',
        'option2',
        'option3',
      ];
      
      const correctAnswer = `meaning of ${word}`;
      const allOptions = [correctAnswer, ...fakeOptions].sort(() => Math.random() - 0.5);

      return {
        id: `q${index}`,
        word,
        options: allOptions,
        correctAnswer,
      };
    });

    setQuestions(generatedQuestions);
  };

  const handleAnswerSelect = (answer: string) => {
    gameLogic.selectAnswer(answer);
  };

  const handleSubmitAnswer = () => {
    gameLogic.submitAnswer();
  };

  const handleWatchVideo = () => {
    navigation.navigate('VideoPlayer');
  };

  if (!state.selectedEpisode || questions.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <Text style={styles.loadingText}>Loading...</Text>
      </SafeAreaView>
    );
  }

  const currentQuestion = gameLogic.currentQuestion || questions[gameLogic.currentQuestionIndex];
  const progress = ((gameLogic.currentQuestionIndex + 1) / questions.length) * 100;

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.episodeTitle}>{state.selectedEpisode.title}</Text>
        <ProgressBar
          progress={progress}
          label={`${gameLogic.currentQuestionIndex + 1} / ${questions.length}`}
        />
      </View>

      <View style={styles.gameArea}>
        <View style={styles.timerContainer}>
          <Text style={[styles.timer, { color: gameLogic.timeLeft <= 10 ? '#F44336' : '#4CAF50' }]}>
            {gameLogic.timeLeft}s
          </Text>
        </View>

        <View style={styles.questionContainer}>
          <Text style={styles.questionText}>What does this word mean?</Text>
          <Text style={styles.wordText}>{currentQuestion?.word}</Text>
        </View>

        <View style={styles.optionsContainer}>
          {currentQuestion?.options.map((option, index) => {
            let buttonStyle = [styles.optionButton];
            let textStyle = [styles.optionText];

            if (gameLogic.showResult) {
              if (option === currentQuestion.correctAnswer) {
                buttonStyle.push(styles.correctOption);
                textStyle.push(styles.correctOptionText);
              } else if (option === gameLogic.selectedAnswer && option !== currentQuestion.correctAnswer) {
                buttonStyle.push(styles.incorrectOption);
                textStyle.push(styles.incorrectOptionText);
              }
            } else if (gameLogic.selectedAnswer === option) {
              buttonStyle.push(styles.selectedOption);
              textStyle.push(styles.selectedOptionText);
            }

            return (
              <TouchableOpacity
                key={index}
                style={buttonStyle}
                onPress={() => handleAnswerSelect(option)}
                disabled={gameLogic.showResult}
              >
                <Text style={textStyle}>{option}</Text>
              </TouchableOpacity>
            );
          })}
        </View>

        {!gameLogic.showResult ? (
          <TouchableOpacity
            style={[styles.submitButton, !gameLogic.selectedAnswer && styles.disabledButton]}
            onPress={handleSubmitAnswer}
            disabled={!gameLogic.selectedAnswer}
          >
            <Text style={styles.submitButtonText}>Submit Answer</Text>
          </TouchableOpacity>
        ) : (
          <View style={styles.resultContainer}>
            <Text style={[styles.resultText, 
              gameLogic.selectedAnswer === currentQuestion?.correctAnswer ? styles.correctText : styles.incorrectText
            ]}>
              {gameLogic.selectedAnswer === currentQuestion?.correctAnswer ? '✅ Correct!' : '❌ Incorrect'}
            </Text>
          </View>
        )}
        <StatsSummary
          stats={createGameStats({
            correct: gameLogic.stats.correctAnswers,
            incorrect: gameLogic.stats.incorrectAnswers,
            total: questions.length,
            timeLeft: gameLogic.timeLeft,
          }, 'game')}
        />
      </View>

      <ActionButtonsRow
        buttons={createCommonButtons({
          onWatchVideo: handleWatchVideo,
        }, 'game')}
      />
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
    marginBottom: 12,
  },

  gameArea: {
    flex: 1,
    padding: 20,
  },
  timerContainer: {
    alignItems: 'center',
    marginBottom: 20,
  },
  timer: {
    fontSize: 32,
    fontWeight: 'bold',
  },
  questionContainer: {
    alignItems: 'center',
    marginBottom: 30,
  },
  questionText: {
    fontSize: 18,
    color: '#666666',
    marginBottom: 12,
  },
  wordText: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#333333',
  },
  optionsContainer: {
    marginBottom: 30,
  },
  optionButton: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
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
  submitButton: {
    backgroundColor: '#4CAF50',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  disabledButton: {
    backgroundColor: '#CCCCCC',
  },
  submitButtonText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: 'bold',
  },
  resultContainer: {
    alignItems: 'center',
    padding: 16,
  },
  resultText: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  correctText: {
    color: '#4CAF50',
  },
  incorrectText: {
    color: '#F44336',
  },

});