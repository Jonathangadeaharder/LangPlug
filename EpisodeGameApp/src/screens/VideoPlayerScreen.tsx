import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  Dimensions,
  ScrollView,
} from 'react-native';
import { useGameSession } from '../stores/useAppStore';

const { width, height } = Dimensions.get('window');

export default function VideoPlayerScreen({ navigation }: any) {
  const gameState = useGameSession();
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [showSubtitles, setShowSubtitles] = useState(true);

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleBackToGame = () => {
    navigation.goBack();
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (!gameState.selectedEpisode) {
    return (
      <SafeAreaView style={styles.container}>
        <Text style={styles.errorText}>No episode selected</Text>
      </SafeAreaView>
    );
  }

  const totalDuration = gameState.selectedEpisode.duration * 60; // Convert to seconds
  const progress = (currentTime / totalDuration) * 100;

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={handleBackToGame} style={styles.backButton}>
          <Text style={styles.backButtonText}>← Back to Game</Text>
        </TouchableOpacity>
        <Text style={styles.episodeTitle}>{gameState.selectedEpisode.title}</Text>
      </View>

      <View style={styles.videoContainer}>
        {/* Video Player Placeholder */}
        <View style={styles.videoPlaceholder}>
          <TouchableOpacity style={styles.playButton} onPress={handlePlayPause}>
            <Text style={styles.playButtonText}>
              {isPlaying ? '⏸️' : '▶️'}
            </Text>
          </TouchableOpacity>
          <Text style={styles.videoPlaceholderText}>
            Video Player\n(Placeholder)
          </Text>
        </View>

        {/* Video Controls */}
        <View style={styles.controls}>
          <View style={styles.progressContainer}>
            <Text style={styles.timeText}>{formatTime(currentTime)}</Text>
            <View style={styles.progressBar}>
              <View style={[styles.progressFill, { width: `${progress}%` }]} />
              <TouchableOpacity 
                style={[styles.progressThumb, { left: `${progress}%` }]}
                onPress={() => {/* Handle seek */}}
              />
            </View>
            <Text style={styles.timeText}>{formatTime(totalDuration)}</Text>
          </View>

          <View style={styles.controlButtons}>
            <TouchableOpacity 
              style={styles.controlButton}
              onPress={() => setCurrentTime(Math.max(0, currentTime - 10))}
            >
              <Text style={styles.controlButtonText}>⏪ 10s</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.playPauseButton} onPress={handlePlayPause}>
              <Text style={styles.playPauseButtonText}>
                {isPlaying ? '⏸️ Pause' : '▶️ Play'}
              </Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.controlButton}
              onPress={() => setCurrentTime(Math.min(totalDuration, currentTime + 10))}
            >
              <Text style={styles.controlButtonText}>10s ⏩</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>

      {/* Subtitles Section */}
      <View style={styles.subtitlesSection}>
        <View style={styles.subtitlesHeader}>
          <Text style={styles.subtitlesTitle}>Subtitles</Text>
          <TouchableOpacity 
            style={styles.subtitlesToggle}
            onPress={() => setShowSubtitles(!showSubtitles)}
          >
            <Text style={styles.subtitlesToggleText}>
              {showSubtitles ? 'Hide' : 'Show'}
            </Text>
          </TouchableOpacity>
        </View>
        
        {showSubtitles && (
          <ScrollView style={styles.subtitlesContainer}>
            <Text style={styles.subtitleText}>
              [00:00] Welcome to this episode of our language learning series.
            </Text>
            <Text style={styles.subtitleText}>
              [00:05] Today we'll be exploring new vocabulary words.
            </Text>
            <Text style={styles.subtitleText}>
              [00:10] Pay attention to the pronunciation and context.
            </Text>
            <Text style={styles.subtitleText}>
              [00:15] You can pause and replay any section as needed.
            </Text>
            <Text style={styles.subtitleText}>
              [00:20] Let's begin with our first vocabulary word...
            </Text>
          </ScrollView>
        )}
      </View>

      {/* Vocabulary Words */}
      <View style={styles.vocabularySection}>
        <Text style={styles.vocabularyTitle}>Episode Vocabulary</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={styles.vocabularyList}>
            {gameState.selectedEpisode.vocabularyWords.map((word, index) => (
              <View key={index} style={styles.vocabularyCard}>
                <Text style={styles.vocabularyWord}>{word}</Text>
              </View>
            ))}
          </View>
        </ScrollView>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
  },
  backButton: {
    marginRight: 16,
  },
  backButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
  },
  episodeTitle: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: 'bold',
    flex: 1,
  },
  videoContainer: {
    flex: 1,
  },
  videoPlaceholder: {
    flex: 1,
    backgroundColor: '#1A1A1A',
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  playButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  playButtonText: {
    fontSize: 32,
  },
  videoPlaceholderText: {
    color: '#FFFFFF',
    fontSize: 16,
    textAlign: 'center',
    opacity: 0.7,
  },
  controls: {
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    padding: 16,
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  timeText: {
    color: '#FFFFFF',
    fontSize: 12,
    minWidth: 40,
  },
  progressBar: {
    flex: 1,
    height: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    borderRadius: 2,
    marginHorizontal: 12,
    position: 'relative',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#FF0000',
    borderRadius: 2,
  },
  progressThumb: {
    position: 'absolute',
    top: -6,
    width: 16,
    height: 16,
    backgroundColor: '#FF0000',
    borderRadius: 8,
    marginLeft: -8,
  },
  controlButtons: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  controlButton: {
    padding: 12,
    marginHorizontal: 8,
  },
  controlButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
  },
  playPauseButton: {
    backgroundColor: '#FF0000',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    marginHorizontal: 16,
  },
  playPauseButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  subtitlesSection: {
    backgroundColor: '#F5F5F5',
    maxHeight: 150,
  },
  subtitlesHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  subtitlesTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333333',
  },
  subtitlesToggle: {
    padding: 8,
  },
  subtitlesToggleText: {
    color: '#2196F3',
    fontSize: 14,
  },
  subtitlesContainer: {
    padding: 16,
  },
  subtitleText: {
    fontSize: 14,
    color: '#333333',
    marginBottom: 8,
    lineHeight: 20,
  },
  vocabularySection: {
    backgroundColor: '#FFFFFF',
    padding: 16,
  },
  vocabularyTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 12,
  },
  vocabularyList: {
    flexDirection: 'row',
  },
  vocabularyCard: {
    backgroundColor: '#E3F2FD',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
    marginRight: 8,
  },
  vocabularyWord: {
    color: '#1976D2',
    fontSize: 14,
    fontWeight: '500',
  },
  errorText: {
    fontSize: 18,
    color: '#FFFFFF',
    textAlign: 'center',
    marginTop: 50,
  },
});