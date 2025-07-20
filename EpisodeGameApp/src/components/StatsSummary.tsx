import React from 'react';
import { View, Text, StyleSheet, ViewStyle } from 'react-native';

interface StatItem {
  label: string;
  value: number | string;
  color?: string;
}

interface StatsSummaryProps {
  stats: StatItem[];
  layout?: 'horizontal' | 'vertical' | 'grid';
  showDividers?: boolean;
  style?: ViewStyle;
  itemStyle?: ViewStyle;
}

const StatsSummary: React.FC<StatsSummaryProps> = ({
  stats,
  layout = 'horizontal',
  showDividers = true,
  style,
  itemStyle,
}) => {
  const renderStatItem = (stat: StatItem, index: number) => (
    <React.Fragment key={index}>
      <View style={[styles.statItem, itemStyle]}>
        <Text style={[styles.statNumber, stat.color && { color: stat.color }]}>
          {stat.value}
        </Text>
        <Text style={styles.statLabel}>{stat.label}</Text>
      </View>
      {showDividers && index < stats.length - 1 && layout === 'horizontal' && (
        <View style={styles.statDivider} />
      )}
    </React.Fragment>
  );

  const getContainerStyle = () => {
    const baseStyle = [styles.container, style];
    
    switch (layout) {
      case 'horizontal':
        return [...baseStyle, styles.horizontalLayout];
      case 'vertical':
        return [...baseStyle, styles.verticalLayout];
      case 'grid':
        return [...baseStyle, styles.gridLayout];
      default:
        return baseStyle;
    }
  };

  return (
    <View style={getContainerStyle()}>
      {stats.map((stat, index) => renderStatItem(stat, index))}
    </View>
  );
};

// Helper function to create common stat configurations
export const createGameStats = ({
  known = 0,
  unknown = 0,
  skipped = 0,
  correct = 0,
  incorrect = 0,
  total = 0,
  score = 0,
  mode = 'vocabulary'
}: {
  known?: number;
  unknown?: number;
  skipped?: number;
  correct?: number;
  incorrect?: number;
  total?: number;
  score?: number;
  mode?: 'vocabulary' | 'game' | 'results';
}): StatItem[] => {
  switch (mode) {
    case 'vocabulary':
      return [
        { label: 'Known', value: known, color: '#4CAF50' },
        { label: 'Unknown', value: unknown, color: '#F44336' },
        { label: 'Skipped', value: skipped, color: '#FF9800' },
      ];
    case 'game':
      return [
        { label: 'Correct', value: correct, color: '#4CAF50' },
        { label: 'Incorrect', value: incorrect, color: '#F44336' },
        { label: 'Total', value: total, color: '#666666' },
      ];
    case 'results':
      return [
        { label: 'Score', value: score, color: '#4CAF50' },
        { label: 'Correct', value: correct, color: '#4CAF50' },
        { label: 'Incorrect', value: incorrect, color: '#F44336' },
        { label: 'Total', value: total, color: '#666666' },
      ];
    default:
      return [];
  }
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  horizontalLayout: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
  },
  verticalLayout: {
    flexDirection: 'column',
    gap: 16,
  },
  gridLayout: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statItem: {
    alignItems: 'center',
    minWidth: 60,
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333333',
  },
  statLabel: {
    fontSize: 12,
    color: '#666666',
    marginTop: 4,
    textAlign: 'center',
  },
  statDivider: {
    width: 1,
    height: 40,
    backgroundColor: '#E0E0E0',
  },
});

export default StatsSummary;