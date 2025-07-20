import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  Dimensions,
} from 'react-native';
import { useGameSession } from '../context/GameSessionContext';

const { width } = Dimensions.get('window');

export default function ResultsScreen({ navigation }: any) {
  const { state, resetGame } = useGameSession();

  const handlePlayAgain = () => {
    resetGame();
    navigation.navigate('EpisodeSelection');
  };

  const handleWatchVideo = () => {
    navigation.navigate('VideoPlayer');
  };

  const getScoreColor = (percentage: number) => {
    if (percentage >= 80) return '#4CAF50';
    if (percentage >= 60) return '#FF9800';
    return '#F44336';
  };

  const getScoreMessage = (percentage: number) => {
    if (percentage >= 90) return 'Excellent! 🌟';
    if (percentage >= 80) return 'Great job! 👏';
    if (percentage >= 70) return 'Good work! 👍';
    if (percentage >= 60) return 'Not bad! 😊';
    return 'Keep practicing! 💪';
  };

  if (!state.selectedEpisode) {
    return (
      <SafeAreaView style={styles.container}>
        <Text style={styles.errorText}>No episode data available</Text>
      </SafeAreaView>
    );
  }

  const percentage = state.totalQuestions > 0 ? (state.correctAnswers / state.totalQuestions) * 100 : 0;
  const scoreColor = getScoreColor(percentage);
  const scoreMessage = getScoreMessage(percentage);

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <Text style={styles.completedText}>🎉 Episode Completed!</Text>
          <Text style={styles.episodeTitle}>{state.selectedEpisode.title}</Text>
        </View>

        <View style={styles.scoreContainer}>
          <View style={[styles.scoreCircle, { borderColor: scoreColor }]}>
            <Text style={[styles.scorePercentage, { color: scoreColor }]}>
              {Math.round(percentage)}%
            </Text>
            <Text style={styles.scoreLabel}>Score</Text>
          </View>
          
          <Text style={[styles.scoreMessage, { color: scoreColor }]}>
            {scoreMessage}
          </Text>
        </View>

        <View style={styles.statsContainer}>
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>{state.correctAnswers}</Text>
            <Text style={styles.statLabel}>Correct</Text>
          </View>
          
          <View style={styles.statDivider} />
          
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>{state.totalQuestions - state.correctAnswers}</Text>
            <Text style={styles.statLabel}>Incorrect</Text>
          </View>
          
          <View style={styles.statDivider} />
          
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>{state.totalQuestions}</Text>
            <Text style={styles.statLabel}>Total</Text>
          </View>
        </View>

        <View style={styles.detailsContainer}>
          <Text style={styles.detailsTitle}>Performance Details</Text>
          
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Final Score:</Text>
            <Text style={[styles.detailValue, { color: scoreColor }]}>
              {state.currentScore} points
            </Text>
          </View>
          
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Accuracy:</Text>
            <Text style={[styles.detailValue, { color: scoreColor }]}>
              {Math.round(percentage)}%
            </Text>
          </View>
          
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Difficulty Level:</Text>
            <Text style={styles.detailValue}>
              {state.selectedEpisode.difficultyLevel.charAt(0).toUpperCase() + 
               state.selectedEpisode.difficultyLevel.slice(1)}
            </Text>
          </View>
          
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Episode Duration:</Text>
            <Text style={styles.detailValue}>
              {state.selectedEpisode.duration} minutes
            </Text>
          </View>
        </View>

        <View style={styles.vocabularyReview}>
          <Text style={styles.vocabularyTitle}>Vocabulary Reviewed</Text>
          <View style={styles.vocabularyGrid}>
            {state.selectedEpisode.vocabularyWords.map((word, index) => {
              const questionId = `q${index}`;
              const userAnswer = state.userAnswers[questionId];
              const isCorrect = userAnswer === `meaning of ${word}`;
              
              return (
                <View 
                  key={index} 
                  style={[
                    styles.vocabularyItem,
                    { backgroundColor: isCorrect ? '#E8F5E8' : '#FFEBEE' }
                  ]}
                >
                  <Text style={[
                    styles.vocabularyWord,
                    { color: isCorrect ? '#4CAF50' : '#F44336' }
                  ]}>
                    {word}
                  </Text>
                  <Text style={styles.vocabularyStatus}>
                    {isCorrect ? '✅' : '❌'}
                  </Text>
                </View>
              );
            })}
          </View>
        </View>
      </ScrollView>

      <View style={styles.actionButtons}>
        <TouchableOpacity 
          style={styles.videoButton} 
          onPress={handleWatchVideo}
        >
          <Text style={styles.videoButtonText}>📺 Watch Episode</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={styles.playAgainButton} 
          onPress={handlePlayAgain}
        >
          <Text style={styles.playAgainButtonText}>🔄 Play Again</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  scrollContent: {
    padding: 20,
  },
  header: {
    alignItems: 'center',
    marginBottom: 30,
  },
  completedText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 8,
  },
  episodeTitle: {
    fontSize: 18,
    color: '#666666',
    textAlign: 'center',
  },
  scoreContainer: {
    alignItems: 'center',
    marginBottom: 30,
  },
  scoreCircle: {
    width: 120,
    height: 120,
    borderRadius: 60,
    borderWidth: 4,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    marginBottom: 16,
  },
  scorePercentage: {
    fontSize: 32,
    fontWeight: 'bold',
  },
  scoreLabel: {
    fontSize: 14,
    color: '#666666',
  },
  scoreMessage: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  statsContainer: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 14,
    color: '#666666',
  },
  statDivider: {
    width: 1,
    backgroundColor: '#E0E0E0',
    marginHorizontal: 20,
  },
  detailsContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  detailsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 16,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  detailLabel: {
    fontSize: 16,
    color: '#666666',
  },
  detailValue: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333333',
  },
  vocabularyReview: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  vocabularyTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 16,
  },
  vocabularyGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  vocabularyItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 8,
    marginBottom: 8,
  },
  vocabularyWord: {
    fontSize: 14,
    fontWeight: '500',
    marginRight: 4,
  },
  vocabularyStatus: {
    fontSize: 12,
  },
  actionButtons: {
    flexDirection: 'row',
    padding: 20,
    gap: 12,
  },
  videoButton: {
    flex: 1,
    backgroundColor: '#FF9800',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  videoButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  playAgainButton: {
    flex: 1,
    backgroundColor: '#4CAF50',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  playAgainButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  errorText: {
    fontSize: 18,
    textAlign: 'center',
    marginTop: 50,
    color: '#666666',
  },
});