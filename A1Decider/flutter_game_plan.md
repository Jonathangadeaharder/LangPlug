# Flutter Episode Swiping Game - Development Plan

## Project Overview

A Flutter web application that allows users to select from available Call the Midwife episodes (MP4 files) and play a vocabulary-based swiping game before watching the episode with enhanced subtitles.

## Current Assets

### Available Episodes
- Episode 3 Staffel 1 von Call the Midwife - Ruf des Lebens
- Episode 4 Staffel 1 von Call the Midwife - Ruf des Lebens
- Episode 5 Staffel 1 von Call the Midwife - Ruf des Lebens
- Episode 6 Staffel 1 von Call the Midwife - Ruf des Lebens

### Existing Python Infrastructure
- **a1decider.py**: Main subtitle processing with SpaCy NLP and Gemini AI integration
- **vocab_generate.py**: Vocabulary extraction from subtitles
- **vocabupdater.py**: Word list management and lemmatization

## Technical Architecture

### Frontend (Flutter Web)
```
flutter_episode_game/
├── lib/
│   ├── main.dart
│   ├── screens/
│   │   ├── episode_selection_screen.dart
│   │   ├── game_screen.dart
│   │   ├── video_player_screen.dart
│   │   └── results_screen.dart
│   ├── widgets/
│   │   ├── episode_card.dart
│   │   ├── swipe_card.dart
│   │   ├── progress_indicator.dart
│   │   └── custom_video_player.dart
│   ├── models/
│   │   ├── episode.dart
│   │   ├── vocabulary_word.dart
│   │   └── game_session.dart
│   ├── services/
│   │   ├── vocabulary_service.dart
│   │   ├── subtitle_service.dart
│   │   └── game_logic_service.dart
│   └── utils/
│       ├── constants.dart
│       └── helpers.dart
├── web/
│   ├── index.html
│   ├── manifest.json
│   └── assets/
│       ├── episodes/
│       └── subtitles/
└── pubspec.yaml
```

### Backend Integration
- **Python API Server**: FastAPI or Flask to serve vocabulary data
- **Subtitle Processing**: Leverage existing Python scripts for real-time subtitle enhancement
- **File Management**: Serve MP4 files and processed subtitle data

## Core Features

### 1. Episode Selection Screen
- **Grid Layout**: Display episode thumbnails with titles
- **Episode Info**: Show duration, difficulty level, vocabulary count
- **Progress Tracking**: Visual indicators for completed episodes
- **Responsive Design**: Optimized for iPhone web browsers

### 2. Vocabulary Swiping Game
- **Card-based Interface**: Swipeable cards with German words
- **Game Mechanics**:
  - Swipe Right: "I know this word"
  - Swipe Left: "I don't know this word"
  - Tap: Show definition/translation
- **Difficulty Levels**: A1, A2, B1 based on existing word lists
- **Progress System**: Track learning progress and accuracy
- **Time Limits**: Optional timed challenges

### 3. Enhanced Video Player
- **Subtitle Integration**: Display processed subtitles with highlighted vocabulary
- **Interactive Subtitles**: Tap words for instant translation
- **Playback Controls**: Custom controls optimized for learning
- **Bookmark System**: Save interesting phrases or difficult words

### 4. Results & Analytics
- **Game Statistics**: Words learned, accuracy, time spent
- **Vocabulary Progress**: Track improvement over time
- **Recommendations**: Suggest episodes based on vocabulary level

## Implementation Phases

### Phase 1: Project Setup (Week 1)
- [ ] Initialize Flutter web project
- [ ] Set up responsive design framework
- [ ] Configure web deployment for iPhone compatibility
- [ ] Create basic navigation structure
- [ ] Set up state management (Provider/Riverpod)

### Phase 2: Backend Integration (Week 2)
- [ ] Create FastAPI server for vocabulary data
- [ ] Integrate existing Python scripts as API endpoints
- [ ] Set up file serving for MP4 episodes
- [ ] Implement subtitle processing pipeline
- [ ] Create vocabulary extraction API

### Phase 3: Episode Selection (Week 3)
- [ ] Design episode selection UI
- [ ] Implement episode metadata management
- [ ] Create thumbnail generation system
- [ ] Add progress tracking functionality
- [ ] Optimize for mobile web performance

### Phase 4: Swiping Game (Week 4-5)
- [ ] Implement swipe gesture recognition
- [ ] Create vocabulary card components
- [ ] Develop game logic and scoring system
- [ ] Add difficulty level selection
- [ ] Implement progress tracking
- [ ] Create engaging animations and feedback

### Phase 5: Video Player Integration (Week 6)
- [ ] Integrate video.js or similar web player
- [ ] Implement subtitle overlay system
- [ ] Add interactive subtitle features
- [ ] Create vocabulary highlighting
- [ ] Optimize video streaming for mobile

### Phase 6: Polish & Deployment (Week 7)
- [ ] Performance optimization
- [ ] Cross-browser testing (Safari focus)
- [ ] PWA implementation for app-like experience
- [ ] Deploy to web hosting service
- [ ] User testing and feedback integration

## Technical Requirements

### Flutter Dependencies
```yaml
dependencies:
  flutter:
    sdk: flutter
  video_player: ^2.7.0
  chewie: ^1.7.0
  flutter_swiper_view: ^1.1.8
  http: ^1.1.0
  provider: ^6.0.5
  shared_preferences: ^2.2.0
  flutter_svg: ^2.0.7
  animations: ^2.0.8
  
dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^2.0.0
```

### Backend Requirements
```python
# requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
spacy==3.7.2
pysrt==1.1.2
webvtt-py==0.4.6
google-generativeai==0.3.1
transformers==4.35.0
```

### Web Optimization
- **Progressive Web App (PWA)**: Enable installation on iPhone
- **Service Worker**: Offline capability for vocabulary data
- **Responsive Design**: Optimized for mobile screens
- **Performance**: Lazy loading, code splitting, asset optimization

## Data Flow

1. **Episode Selection**: User selects episode → Load vocabulary data
2. **Game Preparation**: Extract A1/A2 words from episode subtitles
3. **Swiping Game**: Present vocabulary cards → Track user responses
4. **Results Processing**: Analyze performance → Generate personalized subtitles
5. **Video Playback**: Stream episode with enhanced subtitles

## Deployment Strategy

### Web Hosting
- **Frontend**: Deploy Flutter web build to Netlify/Vercel
- **Backend**: Deploy Python API to Railway/Render
- **Assets**: Use CDN for MP4 files and static assets

### iPhone Optimization
- **Safari Compatibility**: Test all features in Safari
- **Touch Gestures**: Optimize swipe sensitivity
- **Video Playback**: Ensure MP4 compatibility
- **PWA Features**: Add to home screen functionality

## Success Metrics

- **User Engagement**: Time spent in game vs. video watching
- **Learning Effectiveness**: Vocabulary retention rates
- **Technical Performance**: Load times, smooth animations
- **Mobile Experience**: Touch responsiveness, video playback quality

## Future Enhancements

- **Multi-language Support**: Expand beyond German learning
- **Social Features**: Share progress, compete with friends
- **Advanced Analytics**: Detailed learning insights
- **Offline Mode**: Download episodes for offline learning
- **Voice Recognition**: Pronunciation practice features

## Risk Mitigation

- **Video Streaming**: Implement adaptive bitrate streaming
- **Mobile Performance**: Regular testing on actual devices
- **Browser Compatibility**: Fallbacks for unsupported features
- **Data Usage**: Optimize for mobile data constraints

This plan leverages your existing Python infrastructure while creating a modern, engaging Flutter web application optimized for iPhone users learning German through Call the Midwife episodes.