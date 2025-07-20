import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  Dimensions,
  ScrollView,
} from 'react-native';
import { useGameSession } from '../context/GameSessionContext';
import SubtitleService from '../services/SubtitleService';

const { width, height } = Dimensions.get('window');

export default function VideoPlayerScreen({ navigation }: any) {
  const { state } = useGameSession();
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [showSubtitles, setShowSubtitles] = useState(true);
  const [subtitleStatus, setSubtitleStatus] = useState<any>(null);
  const [isLoadingSubtitles, setIsLoadingSubtitles] = useState(true);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (video) {
      const updateTime = () => setCurrentTime(video.currentTime);
      const updateDuration = () => setDuration(video.duration);
      
      video.addEventListener('timeupdate', updateTime);
      video.addEventListener('loadedmetadata', updateDuration);
      
      return () => {
        video.removeEventListener('timeupdate', updateTime);
        video.removeEventListener('loadedmetadata', updateDuration);
      };
    }
  }, []);

  useEffect(() => {
    // Load subtitle status when component mounts
    const loadSubtitleStatus = async () => {
      if (state.selectedEpisode) {
        try {
          setIsLoadingSubtitles(true);
          const status = await SubtitleService.checkSubtitleStatus(state.selectedEpisode);
          setSubtitleStatus(status);
        } catch (error) {
          console.error('Error loading subtitle status:', error);
        } finally {
          setIsLoadingSubtitles(false);
        }
      }
    };

    loadSubtitleStatus();
  }, [state.selectedEpisode]);

  const handlePlayPause = () => {
    const video = videoRef.current;
    if (video) {
      if (isPlaying) {
        video.pause();
      } else {
        video.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleSeek = (time: number) => {
    const video = videoRef.current;
    if (video) {
      video.currentTime = time;
      setCurrentTime(time);
    }
  };

  const handleBackToGame = () => {
    navigation.goBack();
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (!state.selectedEpisode) {
    return (
      <SafeAreaView style={styles.container}>
        <Text style={styles.errorText}>No episode selected</Text>
      </SafeAreaView>
    );
  }

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={handleBackToGame} style={styles.backButton}>
          <Text style={styles.backButtonText}>← Back to Game</Text>
        </TouchableOpacity>
        <Text style={styles.episodeTitle}>{state.selectedEpisode.title}</Text>
      </View>

      <View style={styles.videoContainer}>
        {/* HTML5 Video Player */}
        <div style={{
          width: '100%',
          height: '100%',
          backgroundColor: '#1A1A1A',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center'
        }}>
          <video
            ref={videoRef}
            style={{
              width: '100%',
              height: '100%',
              maxHeight: '400px',
              objectFit: 'contain'
            }}
            controls={false}
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
          >
            <source src={state.selectedEpisode.videoUrl} type="video/mp4" />
            Your browser does not support the video tag.
          </video>
        </div>

        {/* Video Controls */}
        <View style={styles.controls}>
          <View style={styles.progressContainer}>
            <Text style={styles.timeText}>{formatTime(currentTime)}</Text>
            <View style={styles.progressBar}>
              <View style={[styles.progressFill, { width: `${progress}%` }]} />
              <TouchableOpacity 
                style={[styles.progressThumb, { left: `${progress}%` }]}
                onPress={() => {
                  const newTime = (progress / 100) * duration;
                  handleSeek(newTime);
                }}
              />
            </View>
            <Text style={styles.timeText}>{formatTime(duration)}</Text>
          </View>

          <View style={styles.controlButtons}>
            <TouchableOpacity 
              style={styles.controlButton}
              onPress={() => handleSeek(Math.max(0, currentTime - 10))}
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
              onPress={() => handleSeek(Math.min(duration, currentTime + 10))}
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
            <View style={styles.subtitleNotice}>
              <Text style={styles.subtitleNoticeTitle}>📺 German Subtitles Available</Text>
              <Text style={styles.subtitleNoticeText}>
                This video includes embedded German subtitles optimized for A1 level learning.
              </Text>
              <Text style={styles.subtitleNoticeText}>
                💡 <Text style={styles.boldText}>Tip:</Text> Use the A1 Decider game to identify unknown vocabulary before watching!
              </Text>
              <Text style={styles.subtitleNoticeText}>
                🎯 <Text style={styles.boldText}>Learning Focus:</Text> Pay attention to the vocabulary words you marked as "unknown" during the game.
              </Text>
            </View>
            
            {isLoadingSubtitles ? (
              <View style={styles.subtitlePlaceholder}>
                <Text style={styles.subtitlePlaceholderText}>
                  🔄 Loading subtitle status...
                </Text>
              </View>
            ) : subtitleStatus ? (
              <View style={styles.subtitleStatus}>
                <Text style={styles.subtitleStatusTitle}>📋 Subtitle Processing Status</Text>
                
                <View style={styles.statusItem}>
                  <Text style={styles.statusLabel}>Transcription:</Text>
                  <Text style={[styles.statusValue, subtitleStatus.isTranscribed ? styles.statusComplete : styles.statusPending]}>
                    {subtitleStatus.isTranscribed ? '✅ Complete' : '⏳ Pending'}
                  </Text>
                </View>
                
                <View style={styles.statusItem}>
                  <Text style={styles.statusLabel}>A1 Filtering:</Text>
                  <Text style={[styles.statusValue, subtitleStatus.hasFilteredSubtitles ? styles.statusComplete : styles.statusPending]}>
                    {subtitleStatus.hasFilteredSubtitles ? '✅ Complete' : '⏳ Pending'}
                  </Text>
                </View>
                
                <View style={styles.statusItem}>
                  <Text style={styles.statusLabel}>Translation:</Text>
                  <Text style={[styles.statusValue, subtitleStatus.hasTranslatedSubtitles ? styles.statusComplete : styles.statusPending]}>
                    {subtitleStatus.hasTranslatedSubtitles ? '✅ Complete' : '⏳ Pending'}
                  </Text>
                </View>
                
                {subtitleStatus.isTranscribed && (
                  <View style={styles.subtitleHelp}>
                    <Text style={styles.subtitleHelpText}>
                      💡 Subtitles are embedded in the video. Use your browser's video controls to enable them.
                    </Text>
                  </View>
                )}
                
                {!subtitleStatus.isTranscribed && (
                  <View style={styles.subtitleHelp}>
                    <Text style={styles.subtitleHelpText}>
                      ⚠️ Run the A1 Decider workflow first to process subtitles for this episode.
                    </Text>
                    <TouchableOpacity 
                      style={styles.processButton}
                      onPress={() => navigation.navigate('A1DeciderGame')}
                    >
                      <Text style={styles.processButtonText}>🎮 Start A1 Decider Game</Text>
                    </TouchableOpacity>
                  </View>
                )}
              </View>
            ) : (
              <View style={styles.subtitlePlaceholder}>
                <Text style={styles.subtitlePlaceholderText}>
                  ❌ Unable to load subtitle status
                </Text>
                <Text style={styles.subtitleHelpText}>
                  Please try refreshing or check your connection.
                </Text>
              </View>
            )}
          </ScrollView>
        )}
      </View>

      {/* Vocabulary Words */}
      <View style={styles.vocabularySection}>
        <Text style={styles.vocabularyTitle}>Episode Vocabulary</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={styles.vocabularyList}>
            {state.selectedEpisode.vocabularyWords.map((word, index) => (
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
  subtitleNotice: {
    backgroundColor: '#E8F5E8',
    padding: 16,
    borderRadius: 8,
    marginBottom: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#4CAF50',
  },
  subtitleNoticeTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2E7D32',
    marginBottom: 8,
  },
  subtitleNoticeText: {
    fontSize: 14,
    color: '#388E3C',
    marginBottom: 6,
    lineHeight: 20,
  },
  boldText: {
    fontWeight: 'bold',
  },
  subtitlePlaceholder: {
    backgroundColor: '#FFF3E0',
    padding: 16,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#FF9800',
  },
  subtitlePlaceholderText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#F57C00',
    marginBottom: 8,
  },
  subtitleHelpText: {
    fontSize: 13,
    color: '#E65100',
    lineHeight: 18,
  },
  subtitleStatus: {
    backgroundColor: '#E3F2FD',
    padding: 16,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#2196F3',
  },
  subtitleStatusTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1976D2',
    marginBottom: 12,
  },
  statusItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
    paddingVertical: 4,
  },
  statusLabel: {
    fontSize: 14,
    color: '#424242',
    fontWeight: '500',
  },
  statusValue: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  statusComplete: {
    color: '#388E3C',
  },
  statusPending: {
    color: '#F57C00',
  },
  subtitleHelp: {
    marginTop: 12,
    padding: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.7)',
    borderRadius: 6,
  },
  processButton: {
    backgroundColor: '#2196F3',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 6,
    marginTop: 8,
    alignSelf: 'flex-start',
  },
  processButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: 'bold',
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