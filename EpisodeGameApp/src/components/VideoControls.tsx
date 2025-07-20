import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ViewStyle } from 'react-native';

interface VideoControlsProps {
  isPlaying: boolean;
  currentTime: number;
  totalDuration: number;
  onPlayPause: () => void;
  onSeek?: (time: number) => void;
  onSkipBackward?: (seconds?: number) => void;
  onSkipForward?: (seconds?: number) => void;
  skipSeconds?: number;
  showSkipButtons?: boolean;
  showProgressBar?: boolean;
  style?: ViewStyle;
}

const VideoControls: React.FC<VideoControlsProps> = ({
  isPlaying,
  currentTime,
  totalDuration,
  onPlayPause,
  onSeek,
  onSkipBackward,
  onSkipForward,
  skipSeconds = 10,
  showSkipButtons = true,
  showProgressBar = true,
  style,
}) => {
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const progress = totalDuration > 0 ? (currentTime / totalDuration) * 100 : 0;

  const handleSkipBackward = () => {
    if (onSkipBackward) {
      onSkipBackward(skipSeconds);
    } else if (onSeek) {
      onSeek(Math.max(0, currentTime - skipSeconds));
    }
  };

  const handleSkipForward = () => {
    if (onSkipForward) {
      onSkipForward(skipSeconds);
    } else if (onSeek) {
      onSeek(Math.min(totalDuration, currentTime + skipSeconds));
    }
  };

  const handleProgressBarPress = (event: any) => {
    if (!onSeek) return;
    
    const { locationX } = event.nativeEvent;
    const progressBarWidth = event.target.measure?.width || 300; // fallback width
    const percentage = locationX / progressBarWidth;
    const newTime = percentage * totalDuration;
    onSeek(Math.max(0, Math.min(totalDuration, newTime)));
  };

  return (
    <View style={[styles.container, style]}>
      {showProgressBar && (
        <View style={styles.progressContainer}>
          <Text style={styles.timeText}>{formatTime(currentTime)}</Text>
          <TouchableOpacity 
            style={styles.progressBar}
            onPress={handleProgressBarPress}
            activeOpacity={0.8}
          >
            <View style={styles.progressTrack}>
              <View style={[styles.progressFill, { width: `${progress}%` }]} />
              <View style={[styles.progressThumb, { left: `${progress}%` }]} />
            </View>
          </TouchableOpacity>
          <Text style={styles.timeText}>{formatTime(totalDuration)}</Text>
        </View>
      )}

      <View style={styles.controlButtons}>
        {showSkipButtons && (
          <TouchableOpacity 
            style={styles.controlButton}
            onPress={handleSkipBackward}
          >
            <Text style={styles.controlButtonText}>⏪ {skipSeconds}s</Text>
          </TouchableOpacity>
        )}
        
        <TouchableOpacity style={styles.playPauseButton} onPress={onPlayPause}>
          <Text style={styles.playPauseButtonText}>
            {isPlaying ? '⏸️ Pause' : '▶️ Play'}
          </Text>
        </TouchableOpacity>
        
        {showSkipButtons && (
          <TouchableOpacity 
            style={styles.controlButton}
            onPress={handleSkipForward}
          >
            <Text style={styles.controlButtonText}>{skipSeconds}s ⏩</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
};

// Separate component for the large play button overlay
export const PlayButtonOverlay: React.FC<{
  isPlaying: boolean;
  onPress: () => void;
  style?: ViewStyle;
}> = ({ isPlaying, onPress, style }) => (
  <TouchableOpacity style={[styles.playButtonOverlay, style]} onPress={onPress}>
    <View style={styles.playButton}>
      <Text style={styles.playButtonText}>
        {isPlaying ? '⏸️' : '▶️'}
      </Text>
    </View>
  </TouchableOpacity>
);

const styles = StyleSheet.create({
  container: {
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
    fontSize: 14,
    fontWeight: '500',
    minWidth: 45,
    textAlign: 'center',
  },
  progressBar: {
    flex: 1,
    height: 40,
    justifyContent: 'center',
    marginHorizontal: 12,
  },
  progressTrack: {
    height: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    borderRadius: 2,
    position: 'relative',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#FFFFFF',
    borderRadius: 2,
  },
  progressThumb: {
    position: 'absolute',
    top: -6,
    width: 16,
    height: 16,
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    marginLeft: -8,
  },
  controlButtons: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 20,
  },
  controlButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  controlButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '500',
  },
  playPauseButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 25,
  },
  playPauseButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  playButtonOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
  },
  playButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  playButtonText: {
    fontSize: 32,
    color: '#FFFFFF',
  },
});

export default VideoControls;