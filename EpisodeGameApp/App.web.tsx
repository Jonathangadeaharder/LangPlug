import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { GameProvider } from './src/context/GameContext';
import EpisodeSelectionScreen from './src/screens/EpisodeSelectionScreen';
import A1DeciderGameScreen from './src/screens/A1DeciderGameScreen';
import VideoPlayerScreen from './src/screens/VideoPlayerScreen.web';
import ResultsScreen from './src/screens/ResultsScreen';

type Screen = 'EpisodeSelection' | 'A1DeciderGame' | 'VideoPlayer' | 'Results';

const App: React.FC = () => {
  const [currentScreen, setCurrentScreen] = useState<Screen>('EpisodeSelection');
  const [selectedEpisode, setSelectedEpisode] = useState<any>(null);

  const navigate = (screen: Screen, params?: any) => {
    if (params?.episode) {
      setSelectedEpisode(params.episode);
    }
    setCurrentScreen(screen);
  };

  const renderScreen = () => {
    switch (currentScreen) {
      case 'EpisodeSelection':
        return (
          <EpisodeSelectionScreen
            navigation={{
              navigate: (screen: string, params?: any) => {
                if (screen === 'A1DeciderGame') {
                  navigate('A1DeciderGame', params);
                }
              }
            } as any}
          />
        );
      case 'A1DeciderGame':
        return (
          <A1DeciderGameScreen
            navigation={{
              navigate: (screen: string) => {
                if (screen === 'VideoPlayer') {
                  navigate('VideoPlayer');
                } else if (screen === 'Results') {
                  navigate('Results');
                }
              },
              goBack: () => navigate('EpisodeSelection')
            } as any}
            route={{ params: { episode: selectedEpisode } } as any}
          />
        );
      case 'VideoPlayer':
        return (
          <VideoPlayerScreen
            navigation={{
              navigate: (screen: string) => {
                if (screen === 'Results') {
                  navigate('Results');
                }
              },
              goBack: () => navigate('A1DeciderGame')
            } as any}
            route={{ params: { episode: selectedEpisode } } as any}
          />
        );
      case 'Results':
        return (
          <ResultsScreen
            navigation={{
              navigate: (screen: string) => {
                if (screen === 'EpisodeSelection') {
                  navigate('EpisodeSelection');
                }
              },
              goBack: () => navigate('VideoPlayer')
            } as any}
          />
        );
      default:
        return null;
    }
  };

  return (
    <GameProvider>
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Episode Game App - A1 Decider Integration</Text>
          <Text style={styles.headerSubtitle}>Current Screen: {currentScreen}</Text>
        </View>
        <View style={styles.content}>
          {renderScreen()}
        </View>
      </View>
    </GameProvider>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#2196F3',
    padding: 20,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 5,
  },
  headerSubtitle: {
    fontSize: 16,
    color: 'white',
    opacity: 0.8,
  },
  content: {
    flex: 1,
  },
});

export default App;