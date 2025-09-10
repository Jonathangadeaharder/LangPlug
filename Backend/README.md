# A1Decider - German Language Learning Subtitle Processor

A comprehensive subtitle processing system for German language learning, featuring AI-powered transcription, translation, and vocabulary analysis.

## Features

- 🎯 **Multiple Transcription Services**: Whisper, Canary, Parakeet
- 🌐 **Translation Support**: Marian, HuggingFace Pipeline
- 🏃 **High Performance**: Caching, batch processing, parallel execution
- 🔌 **Plugin System**: Easy to add new services
- 📊 **Vocabulary Analysis**: A1-level filtering and analysis
- 🖥️ **REST API**: FastAPI server with WebSocket support
- 🎮 **React Frontend**: EpisodeGameApp integration

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Start the API server
python unified_api_server.py
```

### CLI Usage

```bash
# Transcribe a video
python processing/unified_cli.py transcribe video.mp4

# Translate subtitles
python processing/unified_cli.py translate subtitle.srt --source de --target en

# Full processing pipeline
python processing/unified_cli.py process video.mp4 --target es
```

### API Usage

```python
from processing.services import ServiceFacade

facade = ServiceFacade()
result = facade.transcribe('audio.wav', service='whisper')
```

## Project Structure

```
A1Decider/
├── processing/           # Core processing modules
│   ├── services/        # Service implementations
│   └── unified_cli.py   # CLI interface
├── config/              # Configuration files
├── data/               # Data files
├── tests/              # Test suites
├── docs/               # Documentation
└── unified_api_server.py  # FastAPI server
```

## Configuration

Edit `config/config.py` or use environment variables:

```bash
export A1DECIDER_WHISPER_MODEL_SIZE=large
export A1DECIDER_PROFILE=fast
```

## Documentation

- [Architecture Overview](processing/services/ARCHITECTURE.md)
- [API Documentation](http://localhost:8000/docs)
- [Integration Guide](../EpisodeGameApp/ARCHITECTURE_INTEGRATION.md)

## License

MIT License - See LICENSE file for details
