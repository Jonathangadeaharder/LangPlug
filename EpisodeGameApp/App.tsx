import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { StatusBar } from 'react-native';


import { ThemeProvider, useTheme } from './src/theme/ThemeProvider';
import EpisodeSelectionScreen from './src/screens/EpisodeSelectionScreen';
import GameScreen from './src/screens/GameScreen';
import A1DeciderGameScreen from './src/screens/A1DeciderGameScreen';
import VideoPlayerScreen from './src/screens/VideoPlayerScreen';
import ResultsScreen from './src/screens/ResultsScreen';

const Stack = createStackNavigator();

function AppContent(): React.JSX.Element {
  const theme = useTheme();
  
  return (
    <NavigationContainer>
      <StatusBar barStyle="dark-content" backgroundColor={theme.colors.background.primary} />
      <Stack.Navigator
        initialRouteName="EpisodeSelection"
        screenOptions={{
          headerStyle: {
            backgroundColor: theme.colors.background.primary,
          },
          headerTintColor: theme.colors.text.primary,
          headerTitleStyle: {
            fontWeight: 'bold',
          },
        }}
      >
          <Stack.Screen
            name="EpisodeSelection"
            component={EpisodeSelectionScreen}
            options={{
              title: 'Episode Game',
              headerStyle: {
                backgroundColor: theme.colors.primary.main,
              },
              headerTintColor: theme.colors.background.primary,
            }}
          />
          <Stack.Screen
            name="Game"
            component={GameScreen}
            options={{
              title: 'Vocabulary Game',
              headerLeft: () => null, // Disable back button during game
            }}
          />
          <Stack.Screen
            name="A1DeciderGame"
            component={A1DeciderGameScreen}
            options={{
              title: 'A1 Decider Game',
              headerLeft: () => null, // Disable back button during game
            }}
          />
          <Stack.Screen
            name="VideoPlayer"
            component={VideoPlayerScreen}
            options={{
              title: 'Episode Video',
              headerStyle: {
                backgroundColor: theme.colors.surface.dark,
              },
              headerTintColor: theme.colors.background.primary,
            }}
          />
          <Stack.Screen
            name="Results"
            component={ResultsScreen}
            options={{
              title: 'Game Results',
              headerLeft: () => null, // Disable back button on results
              headerStyle: {
                backgroundColor: theme.colors.primary.main,
              },
              headerTintColor: theme.colors.background.primary,
            }}
          />
        </Stack.Navigator>
      </NavigationContainer>
  );
}

function App(): React.JSX.Element {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

export default App;
