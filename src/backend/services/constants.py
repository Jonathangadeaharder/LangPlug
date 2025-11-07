"""
Service layer constants to eliminate magic numbers.

These constants provide semantic meaning to numeric values used in service implementations.
"""

# ============================================================================
# Audio Processing
# ============================================================================

# Audio sample rate for speech recognition (Hz)
AUDIO_SAMPLE_RATE_HZ = 16_000

# PCM bit depth for audio encoding
PCM_BIT_DEPTH = 16

# Audio channels (1 = mono, 2 = stereo)
AUDIO_CHANNELS_MONO = 1
AUDIO_CHANNELS_STEREO = 2

# Default audio channels for speech recognition
DEFAULT_AUDIO_CHANNELS = AUDIO_CHANNELS_MONO

# ============================================================================
# Video Processing
# ============================================================================

# FFmpeg operation timeout (seconds)
FFMPEG_TIMEOUT_SECONDS = 600

# Default video chunk duration (seconds)
DEFAULT_CHUNK_DURATION_SECONDS = 30

# Maximum video chunk duration (seconds)
MAX_CHUNK_DURATION_SECONDS = 1200  # 20 minutes

# Minimum video chunk duration (seconds)
MIN_CHUNK_DURATION_SECONDS = 5

# Video processing buffer size (bytes)
VIDEO_BUFFER_SIZE_BYTES = 8_192

# ============================================================================
# Transcription Service
# ============================================================================

# Maximum audio file size for transcription (bytes - 500MB)
MAX_TRANSCRIPTION_FILE_SIZE = 524_288_000

# Whisper model timeout (seconds)
WHISPER_TIMEOUT_SECONDS = 300

# Transcription confidence threshold (0.0 - 1.0)
MIN_TRANSCRIPTION_CONFIDENCE = 0.6

# ============================================================================
# Translation Service
# ============================================================================

# Maximum text length for translation (characters)
MAX_TRANSLATION_LENGTH = 5_000

# Translation batch size (number of segments)
TRANSLATION_BATCH_SIZE = 100

# Translation timeout per segment (seconds)
TRANSLATION_TIMEOUT_SECONDS = 30

# ============================================================================
# Vocabulary Processing
# ============================================================================

# Maximum vocabulary words per level
MAX_WORDS_PER_LEVEL = 10_000

# Minimum word frequency for inclusion
MIN_WORD_FREQUENCY = 5

# Maximum lemma length
MAX_LEMMA_LENGTH = 100

# Default confidence level for known words
DEFAULT_CONFIDENCE_LEVEL = 100

# Minimum confidence level
MIN_CONFIDENCE_LEVEL = 0

# Maximum confidence level
MAX_CONFIDENCE_LEVEL = 100

# ============================================================================
# Database & Repository
# ============================================================================

# Default database query batch size
DEFAULT_BATCH_SIZE = 1_000

# Maximum items to fetch in a single query
MAX_QUERY_ITEMS = 10_000

# Database connection pool size
DB_POOL_SIZE = 10

# Database connection timeout (seconds)
DB_CONNECTION_TIMEOUT = 30

# ============================================================================
# Caching
# ============================================================================

# Service registry cache size
SERVICE_CACHE_SIZE = 100

# Model cache size (for AI models)
MODEL_CACHE_SIZE = 5

# Cache TTL in seconds (1 hour)
CACHE_TTL_SECONDS = 3_600

# ============================================================================
# Task Processing
# ============================================================================

# Task cleanup interval (seconds)
TASK_CLEANUP_INTERVAL_SECONDS = 3_600  # 1 hour

# Task retention period (seconds - 24 hours)
TASK_RETENTION_SECONDS = 86_400

# Maximum concurrent tasks
MAX_CONCURRENT_TASKS = 10

# Task progress update interval (seconds)
TASK_PROGRESS_UPDATE_INTERVAL = 1

# ============================================================================
# File Processing
# ============================================================================

# Chunk size for file reading (bytes - 64KB)
FILE_READ_CHUNK_SIZE = 65_536

# Maximum file descriptor limit
MAX_FILE_DESCRIPTORS = 1_024

# Temporary file retention (seconds - 1 hour)
TEMP_FILE_RETENTION_SECONDS = 3_600

# ============================================================================
# Retry & Error Handling
# ============================================================================

# Maximum retry attempts for service operations
MAX_SERVICE_RETRY_ATTEMPTS = 3

# Exponential backoff base (seconds)
RETRY_BACKOFF_BASE_SECONDS = 2

# Maximum backoff time (seconds)
MAX_RETRY_BACKOFF_SECONDS = 32

# ============================================================================
# AI Model Configuration
# ============================================================================

# Default temperature for language models
DEFAULT_MODEL_TEMPERATURE = 0.7

# Maximum tokens for model output
MAX_MODEL_OUTPUT_TOKENS = 2_048

# Model inference timeout (seconds)
MODEL_INFERENCE_TIMEOUT = 120

# ============================================================================
# Authentication & Security
# ============================================================================

# Password minimum length
PASSWORD_MIN_LENGTH = 8

# Password maximum length
PASSWORD_MAX_LENGTH = 128

# Maximum login attempts before lockout
MAX_LOGIN_ATTEMPTS = 5

# Account lockout duration (seconds - 15 minutes)
ACCOUNT_LOCKOUT_SECONDS = 900

# Token generation attempts
TOKEN_GENERATION_MAX_ATTEMPTS = 3

# ============================================================================
# Health Monitoring
# ============================================================================

# Health check interval (seconds)
HEALTH_CHECK_INTERVAL_SECONDS = 60

# Service startup grace period (seconds)
STARTUP_GRACE_PERIOD_SECONDS = 30

# Maximum allowed failures before marking unhealthy
MAX_HEALTH_CHECK_FAILURES = 3
