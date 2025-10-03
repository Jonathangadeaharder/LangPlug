# LangPlug - German Language Learning Platform

A Netflix-style language learning platform that combines video streaming with interactive vocabulary learning. Learn German by watching TV shows with intelligent subtitle processing and gamified vocabulary training.

## 🌟 Features

- **🎬 Netflix-Style Interface**: Beautiful, responsive video streaming platform
- **🎯 Interactive Vocabulary Games**: Tinder-style word swiping for effective learning
- **📺 Smart Video Player**: Custom player with subtitle controls and 5-minute learning segments
- **🤖 AI-Powered Transcription**: Automatic subtitle generation using Whisper
- **📊 Progress Tracking**: Track your vocabulary learning across episodes
- **🔐 User Authentication**: Secure login and progress storage
- **🎮 Gamified Learning**: Learn through engaging interactive experiences

## 🏗️ Architecture

### Backend (`Backend/`)

- **FastAPI Server**: RESTful API with automatic documentation
- **AI Services**: Whisper transcription, vocabulary filtering, translation
- **Database**: SQLite with repository pattern for user progress and vocabulary
- **Authentication**: Secure session-based authentication with bcrypt hashing

### Frontend (`Frontend/`)

- **React + TypeScript**: Modern frontend with type safety
- **Netflix-Style UI**: Professional interface with styled-components
- **State Management**: Zustand for efficient state management
- **Video Player**: ReactPlayer with custom controls
- **Responsive Design**: Works on desktop, tablet, and mobile

### Video Structure (`videos/`)

Your video files should be organized like this:

```
videos/
└── Superstore/
    ├── Episode 1 Staffel 1 von Superstore.mp4
    ├── Episode 2 Staffel 1 von Superstore.mp4
    └── Episode 3 Staffel 1 von Superstore.mp4
```

### Legacy Projects (`archived_legacy_projects/`)

- Archived legacy subtitle processing projects
- Maintained for reference and historical purposes

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Node.js 16+**
- **FFmpeg** (for video processing)
- **CUDA GPU** (optional, for faster transcription)

### 1. One-Command Setup

```bash
# Clone the repository
git clone <repository-url>
cd LangPlug

# Start everything (installs dependencies automatically)
start.bat
```

This will:

- ✅ Perform cleanup of any existing processes
- ✅ Start both backend and frontend servers in separate windows
- ✅ Automatically close the startup window
- ✅ Backend API: http://localhost:8000
- ✅ Frontend App: http://localhost:3000

### 2. Manual Setup (Alternative)

**Start Both Servers:**

```bash
python server_manager.py start
```

**Stop All Servers:**

```bash
python server_manager.py stop
```

### 3. Add Your Videos

Place your German videos in the `videos/` directory:

```
videos/
└── Superstore/
    ├── Episode 1.mp4
    ├── Episode 2.mp4
    └── ...
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📖 How to Use

### Step 1: Register & Login

- **Default Admin Credentials:**
  - **Email:** `admin@langplug.com`
  - **Password:** `admin`
- Create an account or login with existing credentials
- Your learning progress will be saved automatically

> **⚠️ Important:** For login, use the **full email address** `admin@langplug.com`, not just `admin`

### Step 2: Select a Series

- Browse available TV series in the Netflix-style interface
- Click on a series to see available episodes

### Step 3: Choose an Episode

- Select an episode to start learning
- The system will transcribe subtitles if needed (first time only)

### Step 4: Vocabulary Game

- Before watching, play the vocabulary game
- Swipe right if you know a word, left if you don't
- This helps personalize the learning experience

### Step 5: Watch & Learn

- Watch 5-minute segments with smart subtitle filtering
- Words you marked as unknown will be highlighted
- After each segment, review new vocabulary

### Step 6: Progress Tracking

- Your vocabulary knowledge is tracked across episodes
- System adapts to show only relevant new words

## 🔧 Tech Stack

### Backend

- **FastAPI** - High-performance Python web framework
- **SQLite** - Lightweight database for user data and progress
- **OpenAI Whisper** - AI-powered speech transcription
- **SpaCy** - Natural language processing for German
- **Transformers** - Hugging Face models for translation
- **MoviePy** - Video and audio processing

### Frontend

- **React 18** - Modern UI framework
- **TypeScript** - Type-safe JavaScript
- **Vite** - Lightning-fast build tool
- **Styled Components** - CSS-in-JS styling
- **Zustand** - Lightweight state management
- **React Router** - Client-side routing
- **Framer Motion** - Smooth animations
- **React Player** - Video streaming component

### AI & Machine Learning

- **Whisper Models** - Automatic speech recognition
- **NLLB-200** - Neural machine translation
- **SpaCy Models** - German language processing
- **CEFR Vocabulary Lists** - A1-B2 German word levels

## 🛠️ Configuration

### Environment Variables

```bash
# Backend (.env in Backend/)
WHISPER_MODEL_SIZE=base
DEVICE=cuda  # or cpu
DATABASE_URL=sqlite:///data/langplug.db
```

### Video Formats Supported

- **MP4** (recommended)
- **AVI**
- **MKV**
- **MOV**

### Subtitle Formats

- **SRT** - SubRip
- **VTT** - WebVTT

## 🐛 Troubleshooting

### Common Issues

**"No videos found"**

- Make sure videos are in `videos/SeriesName/` directory
- Check video file formats (MP4 recommended)

**Transcription is slow**

- Install CUDA-compatible GPU drivers
- Use smaller Whisper model: set `WHISPER_MODEL_SIZE=tiny`

**Frontend won't start**

- Make sure Node.js 16+ is installed
- Delete `Frontend/node_modules` and reinstall

**Backend crashes on startup**

- Check Python version (3.8+ required)
- Verify all dependencies installed: `pip install -r Backend/requirements.txt`

**CUDA out of memory**

- System automatically falls back to CPU
- Close other GPU applications
- Use smaller model size

### Performance Tips

- 🚀 **Use CUDA GPU** for 10x faster transcription
- 📁 **Organize videos properly** in series folders
- 💾 **SSD storage** recommended for video files
- 🔧 **Close unnecessary apps** when processing

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and test thoroughly
4. **Commit your changes**: `git commit -m 'Add amazing feature'`
5. **Push to your branch**: `git push origin feature/amazing-feature`
6. \*\*Open a Pull Request`

### Development Guidelines

- Follow existing code style and patterns
- Add tests for new features
- Update documentation for API changes
- Test on both development and production builds

### Test Suite Shortcuts (from repo root)

- Postgres-backed backend tests (Docker required):
  - Bash: `./scripts/run_backend_tests_postgres.sh`
  - PowerShell: `./scripts/run_backend_tests_postgres.ps1`
  - Make: `make test-postgres`

These wrap `Backend/scripts/run_tests_postgres.(sh|ps1)` to start Postgres via docker-compose and run
the backend pytest suite with a 60s per-test timeout.

### Unified Test Suite

The project now includes a unified test suite that combines backend, frontend unit, and E2E tests:

- Run all tests: `cd tests && npm run test:all`
- Run E2E tests: `cd tests && npm run test:e2e`
- Run CI tests: `cd tests && npm run test:ci`

The test suite uses Puppeteer for E2E testing and includes automatic server management.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI Whisper** for excellent speech recognition
- **Hugging Face** for transformer models
- **SpaCy** for German language processing
- **React** and **FastAPI** communities
- **Netflix** for interface design inspiration

---

**Happy Learning! 🎉**

Start your German learning journey with LangPlug - where entertainment meets education.
