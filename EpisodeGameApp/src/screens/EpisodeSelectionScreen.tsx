import React from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Image,
  SafeAreaView,
} from 'react-native';
import { Episode, defaultEpisodes } from '../models/Episode';
import { useGameSessionActions } from '../stores/useAppStore';
import { useTheme } from '../theme/ThemeProvider';
import { createCommonStyles, getDifficultyColors } from '../theme/styleUtils';

interface EpisodeCardProps {
  episode: Episode;
  onSelect: (episode: Episode) => void;
}

function EpisodeCard({ episode, onSelect }: EpisodeCardProps) {
  const { theme } = useTheme();
  const difficultyColors = getDifficultyColors(theme);
  const styles = createStyles(theme);
  
  const getDifficultyColor = (level: string) => {
    return difficultyColors[level as keyof typeof difficultyColors] || theme.colors.onSurfaceVariant;
  };

  return (
    <TouchableOpacity
      style={styles.episodeCard}
      onPress={() => onSelect(episode)}
      activeOpacity={0.7}
    >
      <View style={styles.thumbnailContainer}>
        <View style={[styles.thumbnailPlaceholder, { backgroundColor: theme.colors.outline }]}>
          <Text style={styles.thumbnailText}>📺</Text>
        </View>
      </View>
      
      <View style={styles.episodeInfo}>
        <Text style={styles.episodeTitle}>{episode.title}</Text>
        <Text style={styles.episodeDescription} numberOfLines={2}>
          {episode.description}
        </Text>
        
        <View style={styles.episodeDetails}>
          <View style={styles.detailItem}>
            <Text style={styles.detailLabel}>Duration:</Text>
            <Text style={styles.detailValue}>{episode.duration} min</Text>
          </View>
          
          <View style={styles.detailItem}>
            <Text style={styles.detailLabel}>Level:</Text>
            <View style={[styles.difficultyBadge, { backgroundColor: getDifficultyColor(episode.difficultyLevel) }]}>
              <Text style={styles.difficultyText}>
                {episode.difficultyLevel.charAt(0).toUpperCase() + episode.difficultyLevel.slice(1)}
              </Text>
            </View>
          </View>
          
          <View style={styles.detailItem}>
            <Text style={styles.detailLabel}>Words:</Text>
            <Text style={styles.detailValue}>{episode.vocabularyWords.length}</Text>
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
}

export default function EpisodeSelectionScreen({ navigation }: any) {
  const { selectEpisode } = useGameSessionActions();
  const { theme } = useTheme();
  const commonStyles = createCommonStyles(theme);
  const styles = createStyles(theme);

  const handleEpisodeSelect = (episode: Episode) => {
    selectEpisode(episode);
    navigation.navigate('A1DeciderGame');
  };

  const renderEpisode = ({ item }: { item: Episode }) => (
    <EpisodeCard episode={item} onSelect={handleEpisodeSelect} />
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Choose an Episode</Text>
        <Text style={styles.headerSubtitle}>
          Select an episode to start learning vocabulary
        </Text>
      </View>
      
      <FlatList
        data={defaultEpisodes}
        renderItem={renderEpisode}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.episodeList}
        showsVerticalScrollIndicator={false}
      />
    </SafeAreaView>
  );
}

const createStyles = (theme: any) => StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  header: {
    padding: theme.spacing.xl,
    backgroundColor: theme.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.outline,
  },
  headerTitle: {
    fontSize: theme.typography.fontSize['3xl'],
    fontWeight: theme.typography.fontWeight.bold,
    color: theme.colors.onSurface,
    marginBottom: theme.spacing.sm,
  },
  headerSubtitle: {
    fontSize: theme.typography.fontSize.md,
    color: theme.colors.onSurfaceVariant,
  },
  episodeList: {
    padding: theme.spacing.lg,
  },
  episodeCard: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.lg,
    marginBottom: theme.spacing.lg,
    padding: theme.spacing.lg,
    flexDirection: 'row',
    ...theme.shadows.md,
  },
  thumbnailContainer: {
    marginRight: theme.spacing.lg,
  },
  thumbnailPlaceholder: {
    width: 80,
    height: 60,
    borderRadius: theme.borderRadius.md,
    justifyContent: 'center',
    alignItems: 'center',
  },
  thumbnailText: {
    fontSize: theme.typography.fontSize['2xl'],
  },
  episodeInfo: {
    flex: 1,
  },
  episodeTitle: {
    fontSize: theme.typography.fontSize.lg,
    fontWeight: theme.typography.fontWeight.bold,
    color: theme.colors.onSurface,
    marginBottom: theme.spacing.sm,
  },
  episodeDescription: {
    fontSize: theme.typography.fontSize.base,
    color: theme.colors.onSurfaceVariant,
    marginBottom: theme.spacing.md,
    lineHeight: theme.typography.fontSize.base * theme.typography.lineHeight.normal,
  },
  episodeDetails: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: theme.spacing.md,
  },
  detailItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  detailLabel: {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.onSurfaceVariant,
    marginRight: theme.spacing.xs,
  },
  detailValue: {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.onSurface,
    fontWeight: theme.typography.fontWeight.medium,
  },
  difficultyBadge: {
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: theme.spacing.xs / 2,
    borderRadius: theme.borderRadius.lg,
  },
  difficultyText: {
    fontSize: theme.typography.fontSize.xs,
    color: theme.colors.onPrimary,
    fontWeight: theme.typography.fontWeight.bold,
    textTransform: 'uppercase',
  },
});