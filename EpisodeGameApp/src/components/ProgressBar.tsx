import React from 'react';
import { View, Text, StyleSheet, ViewStyle } from 'react-native';

interface ProgressBarProps {
  progress: number; // 0-100
  current?: number;
  total?: number;
  color?: string;
  backgroundColor?: string;
  height?: number;
  showPercentage?: boolean;
  showFraction?: boolean;
  style?: ViewStyle;
  textStyle?: ViewStyle;
}

const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  current,
  total,
  color = '#4CAF50',
  backgroundColor = '#E0E0E0',
  height = 8,
  showPercentage = true,
  showFraction = false,
  style,
  textStyle,
}) => {
  const clampedProgress = Math.max(0, Math.min(100, progress));
  
  const renderText = () => {
    if (showFraction && current !== undefined && total !== undefined) {
      return `${current} / ${total}`;
    }
    if (showPercentage) {
      return `${Math.round(clampedProgress)}%`;
    }
    return null;
  };

  const text = renderText();

  return (
    <View style={[styles.container, style]}>
      <View style={[styles.progressBar, { height, backgroundColor }]}>
        <View 
          style={[
            styles.progressFill, 
            { 
              width: `${clampedProgress}%`,
              backgroundColor: color,
              height,
            }
          ]} 
        />
      </View>
      {text && (
        <Text style={[styles.progressText, textStyle]}>
          {text}
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    width: '100%',
  },
  progressBar: {
    flex: 1,
    backgroundColor: '#E0E0E0',
    borderRadius: 4,
    marginRight: 12,
  },
  progressFill: {
    borderRadius: 4,
  },
  progressText: {
    fontSize: 14,
    color: '#666666',
    fontWeight: '500',
    minWidth: 40,
  },
});

export default ProgressBar;