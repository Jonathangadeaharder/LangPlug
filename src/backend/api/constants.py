"""
API-related constants to eliminate magic numbers.

These constants provide semantic meaning to numeric values used throughout the API layer.
"""

# ============================================================================
# Pagination & Limits
# ============================================================================

# Shared pagination defaults
DEFAULT_LIMIT = 20
MAX_LIMIT = 100
MIN_LIMIT = 1

# Default number of items to return in paginated lists
DEFAULT_PAGE_LIMIT = DEFAULT_LIMIT

# Maximum number of items that can be requested in a single query
MAX_PAGE_LIMIT = MAX_LIMIT

# Minimum number of items that can be requested
MIN_PAGE_LIMIT = MIN_LIMIT

# Default vocabulary query limit
DEFAULT_VOCABULARY_LIMIT = DEFAULT_LIMIT

# Maximum vocabulary items per request
MAX_VOCABULARY_LIMIT = MAX_LIMIT

# Default search results limit
DEFAULT_SEARCH_LIMIT = DEFAULT_LIMIT

# Maximum search results per request
MAX_SEARCH_LIMIT = MAX_LIMIT

# ============================================================================
# Timeout Values (seconds)
# ============================================================================

# Default HTTP request timeout
DEFAULT_HTTP_TIMEOUT = 30

# Long-running operation timeout
LONG_OPERATION_TIMEOUT = 300

# Health check timeout
HEALTH_CHECK_TIMEOUT = 5

# Database query timeout
DB_QUERY_TIMEOUT = 30

# ============================================================================
# String Length Limits
# ============================================================================

# Minimum search term length
MIN_SEARCH_LENGTH = 1

# Maximum search term length
MAX_SEARCH_LENGTH = 100

# Maximum word length in vocabulary
MAX_WORD_LENGTH = 100

# Maximum username length
MAX_USERNAME_LENGTH = 50

# Maximum email length (RFC 5321)
MAX_EMAIL_LENGTH = 320

# ============================================================================
# Retry & Backoff
# ============================================================================

# Maximum number of retry attempts for operations
MAX_RETRY_ATTEMPTS = 3

# Initial retry delay in seconds
INITIAL_RETRY_DELAY = 2

# Maximum retry delay in seconds
MAX_RETRY_DELAY = 16

# ============================================================================
# File Upload Limits
# ============================================================================

# Maximum upload size in bytes (100MB)
MAX_UPLOAD_SIZE_BYTES = 104_857_600

# Chunk size for file streaming (1MB)
FILE_STREAM_CHUNK_SIZE = 1_048_576

# ============================================================================
# Cache & Session
# ============================================================================

# Default session timeout in hours
DEFAULT_SESSION_TIMEOUT_HOURS = 24

# Refresh token lifetime in days
REFRESH_TOKEN_LIFETIME_DAYS = 30

# Access token lifetime in minutes
ACCESS_TOKEN_LIFETIME_MINUTES = 60

# ============================================================================
# Rate Limiting
# ============================================================================

# Requests per minute per user
RATE_LIMIT_PER_MINUTE = 60

# Burst allowance
RATE_LIMIT_BURST = 100

# ============================================================================
# Vocabulary & Learning
# ============================================================================

# Default chunk duration for video processing (minutes)
DEFAULT_CHUNK_DURATION_MINUTES = 20

# Minimum chunk duration (minutes)
MIN_CHUNK_DURATION_MINUTES = 5

# Maximum chunk duration (minutes)
MAX_CHUNK_DURATION_MINUTES = 20

# Maximum blocking words to return
MAX_BLOCKING_WORDS_LIMIT = 20

# ============================================================================
# WebSocket
# ============================================================================

# WebSocket heartbeat interval (seconds)
WEBSOCKET_HEARTBEAT_INTERVAL = 30

# WebSocket ping timeout (seconds)
WEBSOCKET_PING_TIMEOUT = 60


