"""
Application-wide constants to avoid magic numbers
"""

from datetime import timedelta

# Timeouts
API_TIMEOUT = 10  # seconds
SERVER_STARTUP_TIMEOUT = 30  # seconds
WHISPER_MODEL_LOAD_TIMEOUT = 60  # seconds
TASK_POLLING_INTERVAL = 2  # seconds

# Authentication
JWT_EXPIRATION = timedelta(hours=24)
SESSION_TIMEOUT = timedelta(minutes=30)
MAX_LOGIN_ATTEMPTS = 5

# Transcription
DEFAULT_WHISPER_MODEL = "base"
AVAILABLE_WHISPER_MODELS = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3", "large-v3-turbo"]
DEFAULT_LANGUAGE = "de"
MAX_AUDIO_LENGTH = 600  # seconds (10 minutes)

# File limits
MAX_VIDEO_SIZE_MB = 500
MAX_SUBTITLE_SIZE_KB = 500
CHUNK_SIZE = 1024 * 1024  # 1MB

# Database
MAX_VOCABULARY_WORDS = 10000
BATCH_SIZE = 100

# Progress tracking
PROGRESS_STEPS = {
    "INITIALIZING": 0,
    "LOADING_MODEL": 10,
    "EXTRACTING_AUDIO": 30,
    "TRANSCRIBING": 70,
    "SAVING_RESULTS": 90,
    "COMPLETED": 100
}

# API Rate limiting
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60  # seconds
