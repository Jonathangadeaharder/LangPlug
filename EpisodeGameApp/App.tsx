import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { StatusBar } from 'react-native';

import { GlobalStateProvider } from './src/context/GlobalStateProvider';
import EpisodeSelectionScreen from './src/screens/EpisodeSelectionScreen';
import GameScreen from './src/screens/GameScreen';
import A1DeciderGameScreen from './src/screens/A1DeciderGameScreen';
import VideoPlayerScreen from './src/screens/VideoPlayerScreen';
import ResultsScreen from './src/screens/ResultsScreen';

const Stack = createStackNavigator();

function App(): React.JSX.Element {
  return (
    <GlobalStateProvider>
      <NavigationContainer>
        <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />
        <Stack.Navigator
          initialRouteName="EpisodeSelection"
          screenOptions={{
            headerStyle: {
              backgroundColor: '#FFFFFF',
            },
            headerTintColor: '#333333',
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
                backgroundColor: '#4CAF50',
              },
              headerTintColor: '#FFFFFF',
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
                backgroundColor: '#000000',
              },
              headerTintColor: '#FFFFFF',
            }}
          />
          <Stack.Screen
            name="Results"
            component={ResultsScreen}
            options={{
              title: 'Game Results',
              headerLeft: () => null, // Disable back button on results
              headerStyle: {
                backgroundColor: '#4CAF50',
              },
              headerTintColor: '#FFFFFF',
            }}
          />
        </Stack.Navigator>
      </NavigationContainer>
    </GlobalStateProvider>
  );
}

export default App;
