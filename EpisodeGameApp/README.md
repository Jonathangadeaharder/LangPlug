# Episode Game App - A1 Decider Integration

A React Native application that integrates the A1 Decider vocabulary learning workflow with episode-based language learning.

## Features

### Complete A1 Decider Workflow
When an episode is started, the app automatically:

1. **Checks Transcription Status**: Verifies if the episode has been transcribed
2. **Creates Subtitles**: Uses `subtitle_maker.py` to transcribe the video if needed
3. **Runs A1 Decider Game**: Interactive vocabulary knowledge check
4. **Filters Subtitles**: Creates filtered subtitles containing only unknown words
5. **Translates Subtitles**: Uses `subtitle_translate.py` to translate filtered subtitles
6. **Starts Video**: Launches the episode with processed subtitles

### A1 Decider Game Interface

- **Processing Screen**: Shows real-time progress through transcription, filtering, and translation stages
- **Vocabulary Check**: Interactive word-by-word knowledge assessment
- **Word Classification**: Mark words as Known, Unknown, or Skip
- **Progress Tracking**: Visual progress indicators and statistics
- **Seamless Integration**: Direct transition to video playback

## Project Structure

```
src/
├── context/
│   └── GameContext.tsx          # Enhanced state management for A1 workflow
├── models/
│   └── Episode.ts               # Extended Episode model with processing status
├── screens/
│   ├── EpisodeSelectionScreen.tsx
│   ├── A1DeciderGameScreen.tsx  # New A1 Decider workflow screen
│   ├── GameScreen.tsx           # Original vocabulary game
│   ├── VideoPlayerScreen.tsx
│   └── ResultsScreen.tsx
└── services/
    ├── SubtitleService.ts       # Subtitle processing orchestration
    └── PythonBridgeService.ts   # Python script integration
```

## Integration with Python Scripts

The app integrates with the existing Python codebase:

- **A1Decider**: `c:\Users\Jonandrop\IdeaProjects\A1Decider\`
  - `a1decider.py`: Vocabulary analysis and filtering
  - `subtitle_maker.py`: Video transcription using Whisper
  - `subtitle_translate.py`: Subtitle translation using MarianMT

- **Unified Processor**: `c:\Users\Jonandrop\IdeaProjects\unified_subtitle_processor.py`
  - Complete workflow automation
  - Memory management for CUDA
  - Progress tracking and error handling

## Usage Flow

1. **Select Episode**: Choose an episode from the selection screen
2. **Automatic Processing**: App checks and processes subtitles as needed
3. **Vocabulary Game**: Interactive word knowledge assessment
4. **Watch Video**: Episode plays with filtered subtitles showing only unknown words
5. **Review Results**: View learning progress and statistics

## Setup Instructions

### Prerequisites

1. **Node.js** (v16 or higher)
2. **React Native CLI**
3. **Android Studio** (for Android development)
4. **Xcode** (for iOS development - macOS only)

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd EpisodeGameApp
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Install iOS dependencies (macOS only):**
   ```bash
   cd ios && pod install && cd ..
   ```

### Running the App

#### Android

1. **Start an Android emulator** or connect an Android device
2. **Run the app:**
   ```bash
   npx react-native run-android
   ```

#### iOS (macOS only)

1. **Run the app:**
   ```bash
   npx react-native run-ios
   ```

### Development

1. **Start Metro bundler:**
   ```bash
   npx react-native start
   ```

2. **Enable hot reloading** in the app for faster development

## App Flow

1. **Episode Selection**: Users browse and select from available episodes
2. **Game Play**: Answer vocabulary questions with a 30-second timer per question
3. **Video Watching**: Optional video viewing with subtitle support
4. **Results Review**: View performance metrics and vocabulary review

## Key Components

### GameContext
- Manages global game state using React Context and useReducer
- Handles episode selection, game progress, and scoring
- Provides actions for game flow control

### Episode Model
- Defines episode structure with metadata
- Includes vocabulary words, difficulty levels, and media URLs
- Contains default episode data for testing

### Screen Components
- **EpisodeSelectionScreen**: Grid layout with episode cards
- **GameScreen**: Timer-based multiple choice questions
- **VideoPlayerScreen**: Video controls with subtitle toggle
- **ResultsScreen**: Performance analytics and vocabulary review

## Customization

### Adding New Episodes

Edit `src/models/Episode.ts` and add new episodes to the `defaultEpisodes` array:

```typescript
{
  id: 'ep5',
  title: 'Episode 5: Your Title',
  description: 'Episode description',
  videoUrl: 'path/to/video.mp4',
  thumbnailUrl: 'path/to/thumbnail.jpg',
  duration: 25,
  difficultyLevel: 'beginner',
  vocabularyWords: ['word1', 'word2', 'word3'],
  subtitleUrl: 'path/to/subtitles.srt'
}
```

### Styling

Each screen component contains its own StyleSheet. Key design elements:
- **Colors**: Green (#4CAF50) for primary actions, Orange (#FF9800) for secondary
- **Typography**: Bold headers, readable body text
- **Layout**: Card-based design with shadows and rounded corners

### Game Logic

Modify game behavior in `src/screens/GameScreen.tsx`:
- **Timer duration**: Change `setTimeLeft(30)` to desired seconds
- **Scoring**: Modify point values in the `answerQuestion` action
- **Question generation**: Update `generateQuestions()` for different question types

## Dependencies

- **@react-navigation/native**: Navigation framework
- **@react-navigation/stack**: Stack navigator
- **react-native-screens**: Native screen components
- **react-native-safe-area-context**: Safe area handling

## Troubleshooting

### Common Issues

1. **Metro bundler issues**: Clear cache with `npx react-native start --reset-cache`
2. **Android build errors**: Clean with `cd android && ./gradlew clean`
3. **iOS build errors**: Clean build folder in Xcode
4. **Navigation errors**: Ensure all screen components are properly imported

### Performance Tips

- Use `React.memo()` for components that don't need frequent re-renders
- Optimize images and videos for mobile devices
- Consider lazy loading for large episode lists
- Use FlatList for better performance with many episodes

## Future Enhancements

- **Real video integration**: Replace placeholder with actual video player
- **Audio support**: Add pronunciation guides
- **Offline mode**: Cache episodes for offline play
- **User profiles**: Save progress and achievements
- **Social features**: Share scores and compete with friends
- **Advanced analytics**: Detailed learning progress tracking

## License

This project is for educational purposes. Modify and distribute as needed.

## Support

For issues or questions, refer to the React Native documentation or create an issue in the project repository.
