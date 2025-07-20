import React from 'react';
import { View, Text, TouchableOpacity, ScrollView, StyleSheet, ViewStyle } from 'react-native';

interface SubtitleEntry {
  timestamp: string;
  text: string;
  startTime?: number;
  endTime?: number;
}

interface SubtitleDisplayProps {
  subtitles: SubtitleEntry[];
  currentTime?: number;
  showSubtitles: boolean;
  onToggleSubtitles: () => void;
  onSubtitlePress?: (subtitle: SubtitleEntry) => void;
  style?: ViewStyle;
  headerStyle?: ViewStyle;
  contentStyle?: ViewStyle;
  highlightCurrent?: boolean;
}

const SubtitleDisplay: React.FC<SubtitleDisplayProps> = ({
  subtitles,
  currentTime = 0,
  showSubtitles,
  onToggleSubtitles,
  onSubtitlePress,
  style,
  headerStyle,
  contentStyle,
  highlightCurrent = true,
}) => {
  const getCurrentSubtitleIndex = () => {
    if (!highlightCurrent || currentTime === 0) return -1;
    
    return subtitles.findIndex(subtitle => {
      if (subtitle.startTime !== undefined && subtitle.endTime !== undefined) {
        return currentTime >= subtitle.startTime && currentTime <= subtitle.endTime;
      }
      return false;
    });
  };

  const currentSubtitleIndex = getCurrentSubtitleIndex();

  const renderSubtitleEntry = (subtitle: SubtitleEntry, index: number) => {
    const isActive = highlightCurrent && index === currentSubtitleIndex;
    
    return (
      <TouchableOpacity
        key={index}
        style={[
          styles.subtitleEntry,
          isActive && styles.activeSubtitleEntry
        ]}
        onPress={() => onSubtitlePress?.(subtitle)}
        disabled={!onSubtitlePress}
      >
        <Text style={[
          styles.subtitleText,
          isActive && styles.activeSubtitleText
        ]}>
          {subtitle.timestamp && (
            <Text style={styles.timestamp}>[{subtitle.timestamp}] </Text>
          )}
          {subtitle.text}
        </Text>
      </TouchableOpacity>
    );
  };

  return (
    <View style={[styles.container, style]}>
      <View style={[styles.header, headerStyle]}>
        <Text style={styles.title}>Subtitles</Text>
        <TouchableOpacity 
          style={styles.toggleButton}
          onPress={onToggleSubtitles}
        >
          <Text style={styles.toggleButtonText}>
            {showSubtitles ? 'Hide' : 'Show'}
          </Text>
        </TouchableOpacity>
      </View>
      
      {showSubtitles && (
        <ScrollView 
          style={[styles.content, contentStyle]}
          showsVerticalScrollIndicator={false}
        >
          {subtitles.length > 0 ? (
            subtitles.map((subtitle, index) => renderSubtitleEntry(subtitle, index))
          ) : (
            <Text style={styles.noSubtitlesText}>
              No subtitles available
            </Text>
          )}
        </ScrollView>
      )}
    </View>
  );
};

// Helper function to create subtitle entries from common formats
export const createSubtitleEntries = ({
  srtContent,
  simpleEntries,
}: {
  srtContent?: string;
  simpleEntries?: Array<{ time: string; text: string }>;
}): SubtitleEntry[] => {
  if (simpleEntries) {
    return simpleEntries.map(entry => ({
      timestamp: entry.time,
      text: entry.text,
    }));
  }
  
  if (srtContent) {
    // Basic SRT parsing (can be enhanced)
    const blocks = srtContent.split('\n\n');
    return blocks.map(block => {
      const lines = block.trim().split('\n');
      if (lines.length >= 3) {
        const timestamp = lines[1];
        const text = lines.slice(2).join(' ');
        return { timestamp, text };
      }
      return { timestamp: '', text: block };
    }).filter(entry => entry.text.trim() !== '');
  }
  
  return [];
};

// Default subtitle entries for demo purposes
export const defaultSubtitles: SubtitleEntry[] = [
  {
    timestamp: '00:00',
    text: 'Welcome to this episode of our language learning series.',
    startTime: 0,
    endTime: 5,
  },
  {
    timestamp: '00:05',
    text: 'Today we\'ll be exploring new vocabulary words.',
    startTime: 5,
    endTime: 10,
  },
  {
    timestamp: '00:10',
    text: 'Pay attention to the pronunciation and context.',
    startTime: 10,
    endTime: 15,
  },
  {
    timestamp: '00:15',
    text: 'You can pause and replay any section as needed.',
    startTime: 15,
    endTime: 20,
  },
  {
    timestamp: '00:20',
    text: 'Let\'s begin with our first vocabulary word...',
    startTime: 20,
    endTime: 25,
  },
];

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#F8F9FA',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333333',
  },
  toggleButton: {
    backgroundColor: '#2196F3',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  toggleButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '500',
  },
  content: {
    maxHeight: 200,
    padding: 16,
  },
  subtitleEntry: {
    paddingVertical: 8,
    paddingHorizontal: 4,
    borderRadius: 4,
    marginBottom: 4,
  },
  activeSubtitleEntry: {
    backgroundColor: '#E3F2FD',
  },
  subtitleText: {
    fontSize: 16,
    color: '#333333',
    lineHeight: 22,
  },
  activeSubtitleText: {
    color: '#2196F3',
    fontWeight: '500',
  },
  timestamp: {
    color: '#666666',
    fontSize: 14,
    fontWeight: '500',
  },
  noSubtitlesText: {
    fontSize: 16,
    color: '#666666',
    textAlign: 'center',
    fontStyle: 'italic',
    paddingVertical: 20,
  },
});

export default SubtitleDisplay;