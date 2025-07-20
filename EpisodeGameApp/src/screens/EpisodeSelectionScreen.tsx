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
import { useGameSession } from '../context/GameSessionContext';

interface EpisodeCardProps {
  episode: Episode;
  onSelect: (episode: Episode) => void;
}

function EpisodeCard({ episode, onSelect }: EpisodeCardProps) {
  const getDifficultyColor = (level: string) => {
    switch (level) {
      case 'beginner':
        return '#4CAF50';
      case 'intermediate':
        return '#FF9800';
      case 'advanced':
        return '#F44336';
      default:
        return '#757575';
    }
  };

  return (
    <TouchableOpacity
      style={styles.episodeCard}
      onPress={() => onSelect(episode)}
      activeOpacity={0.7}
    >
      <View style={styles.thumbnailContainer}>
        <View style={[styles.thumbnailPlaceholder, { backgroundColor: '#E0E0E0' }]}>
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
  const { selectEpisode } = useGameSession();

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

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  header: {
    padding: 20,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 8,
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#666666',
  },
  episodeList: {
    padding: 16,
  },
  episodeCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    marginBottom: 16,
    padding: 16,
    flexDirection: 'row',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  thumbnailContainer: {
    marginRight: 16,
  },
  thumbnailPlaceholder: {
    width: 80,
    height: 60,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  thumbnailText: {
    fontSize: 24,
  },
  episodeInfo: {
    flex: 1,
  },
  episodeTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 8,
  },
  episodeDescription: {
    fontSize: 14,
    color: '#666666',
    marginBottom: 12,
    lineHeight: 20,
  },
  episodeDetails: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  detailItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  detailLabel: {
    fontSize: 12,
    color: '#888888',
    marginRight: 4,
  },
  detailValue: {
    fontSize: 12,
    color: '#333333',
    fontWeight: '500',
  },
  difficultyBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 12,
  },
  difficultyText: {
    fontSize: 10,
    color: '#FFFFFF',
    fontWeight: 'bold',
    textTransform: 'uppercase',
  },
});