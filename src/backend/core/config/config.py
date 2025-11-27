"""
Configuration management using Pydantic Settings.
"""

import json
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    # Server settings
    host: str = Field(default="0.0.0.0", alias="LANGPLUG_HOST")  # nosec B104 - Required for Docker/development
    port: int = Field(default=8000, alias="LANGPLUG_PORT")
    reload: bool = Field(default=True, alias="LANGPLUG_RELOAD")
    debug: bool = Field(default=True, alias="LANGPLUG_DEBUG")
    sqlalchemy_echo: bool = Field(default=False, alias="LANGPLUG_SQLALCHEMY_ECHO")

    # Database settings (SQLite only)
    database_url: str | None = Field(default=None, alias="LANGPLUG_DATABASE_URL")

    # CORS settings
    cors_origins: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3002",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:3002",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        alias="LANGPLUG_CORS_ORIGINS",
    )
    cors_credentials: bool = Field(default=True, alias="LANGPLUG_CORS_CREDENTIALS")

    # File paths
    videos_path: str | None = Field(default=None, alias="LANGPLUG_VIDEOS_PATH")
    data_path: str | None = Field(default=None, alias="LANGPLUG_DATA_PATH")
    logs_path: str | None = Field(default=None, alias="LANGPLUG_LOGS_PATH")

    # Service settings (CTranslate2 optimized backends)
    transcription_service: str = Field(default="faster-whisper-turbo", alias="LANGPLUG_TRANSCRIPTION_SERVICE")
    translation_service: str = Field(default="opus-de-es-big", alias="LANGPLUG_TRANSLATION_SERVICE")  # de->es big model
    default_language: str = Field(default="de", alias="LANGPLUG_DEFAULT_LANGUAGE")

    # SpaCy model settings
    spacy_model_de: str = Field(default="de_core_news_lg", alias="LANGPLUG_SPACY_MODEL_DE")
    spacy_model_en: str = Field(default="en_core_web_sm", alias="LANGPLUG_SPACY_MODEL_EN")

    # Security settings
    secret_key: str = Field(..., alias="LANGPLUG_SECRET_KEY", min_length=32)

    # Cache TTL settings
    cache_ttl_default: int = Field(default=3600, alias="LANGPLUG_CACHE_TTL_DEFAULT")  # 1 hour
    cache_ttl_vocabulary: int = Field(default=7200, alias="LANGPLUG_CACHE_TTL_VOCABULARY")  # 2 hours
    cache_ttl_user_progress: int = Field(default=1800, alias="LANGPLUG_CACHE_TTL_USER_PROGRESS")  # 30 minutes

    # Authentication settings
    session_timeout_hours: int = Field(default=24, alias="LANGPLUG_SESSION_TIMEOUT_HOURS")
    jwt_access_token_expire_minutes: int = Field(default=60, alias="LANGPLUG_JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(default=30, alias="LANGPLUG_JWT_REFRESH_TOKEN_EXPIRE_DAYS")

    # Password policy
    password_min_length: int = Field(default=8, alias="LANGPLUG_PASSWORD_MIN_LENGTH")
    password_require_uppercase: bool = Field(default=False, alias="LANGPLUG_PASSWORD_REQUIRE_UPPERCASE")
    password_require_lowercase: bool = Field(default=True, alias="LANGPLUG_PASSWORD_REQUIRE_LOWERCASE")
    password_require_digits: bool = Field(default=True, alias="LANGPLUG_PASSWORD_REQUIRE_DIGITS")
    password_require_special: bool = Field(default=False, alias="LANGPLUG_PASSWORD_REQUIRE_SPECIAL")

    # Rate limiting
    rate_limit_requests_per_minute: int = Field(default=300, alias="LANGPLUG_RATE_LIMIT_REQUESTS_PER_MINUTE")
    rate_limit_burst_size: int = Field(default=60, alias="LANGPLUG_RATE_LIMIT_BURST_SIZE")
    login_max_attempts: int = Field(default=5, alias="LANGPLUG_LOGIN_MAX_ATTEMPTS")
    login_lockout_duration_minutes: int = Field(default=15, alias="LANGPLUG_LOGIN_LOCKOUT_DURATION_MINUTES")

    # Sentry settings
    sentry_dsn: str = Field(default="", alias="SENTRY_DSN", description="Sentry DSN for error tracking")
    environment: str = Field(
        default="development", alias="ENVIRONMENT", description="Environment name (development, staging, production)"
    )

    # Performance settings
    max_upload_size: int = Field(default=100 * 1024 * 1024, alias="LANGPLUG_MAX_UPLOAD_SIZE")  # 100MB
    task_cleanup_interval: int = Field(default=3600, alias="LANGPLUG_TASK_CLEANUP_INTERVAL")  # 1 hour

    # Logging settings
    log_level: str = Field(default="INFO", alias="LANGPLUG_LOG_LEVEL")
    log_format: str = Field(default="json", alias="LANGPLUG_LOG_FORMAT")  # json or text

    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from environment variable if it's a string"""
        if isinstance(v, str):
            try:
                # Try to parse as JSON array
                return json.loads(v)
            except json.JSONDecodeError:
                # Fall back to comma-separated values
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    def get_database_url(self) -> str:
        """Get the SQLite database connection URL"""
        if self.database_url:
            return self.database_url

        # Default SQLite database path
        base_path = Path(self.data_path) if self.data_path else Path(__file__).parent.parent.parent / "data"
        base_path.mkdir(exist_ok=True)
        db_path = base_path / "langplug.db"
        return f"sqlite+aiosqlite:///{db_path}"

    def get_database_path(self) -> Path:
        """Get the database file path (for SQLite only)"""
        if self.database_url and self.database_url.startswith("sqlite+aiosqlite:///"):
            return Path(self.database_url.replace("sqlite+aiosqlite:///", ""))

        if self.database_url and self.database_url.startswith("sqlite:///"):
            return Path(self.database_url.replace("sqlite:///", ""))

        # Default database path
        base_path = Path(self.data_path) if self.data_path else Path(__file__).parent.parent.parent / "data"
        base_path.mkdir(exist_ok=True)
        return base_path / "langplug.db"

    def get_videos_path(self) -> Path:
        """Get the videos directory path with WSL/Windows compatibility"""
        import logging

        logger = logging.getLogger(__name__)

        logger.debug(f"get_videos_path called, self.videos_path = {self.videos_path}")

        if self.videos_path:
            logger.debug(f"Using configured videos_path: {self.videos_path}")
            path = Path(self.videos_path)
            # Handle WSL path conversion if needed
            return self._ensure_accessible_path(path)

        # Default videos path (Project root/videos)
        # Use absolute path calculation to avoid working directory issues
        config_file = Path(__file__).resolve()
        logger.debug(f"Config file: {config_file}")
        default_path = config_file.parent.parent.parent.parent.parent / "videos"
        logger.debug(f"Calculated default path: {default_path}")
        return self._ensure_accessible_path(default_path)

    def _ensure_accessible_path(self, path: Path) -> Path:
        """Ensure path is accessible, converting WSL/Windows paths if needed"""
        import logging

        logger = logging.getLogger(__name__)

        # Resolve relative paths first
        if not path.is_absolute():
            path = path.resolve()
            logger.info(f"Resolved relative path to: {path}")

        # If path exists and is accessible, return as-is
        if path.exists() and path.is_dir():
            logger.info(f"Videos path exists and is accessible: {path}")
            return path

        # Try WSL to Windows conversion
        if str(path).startswith("/mnt/c/"):
            windows_path_str = str(path).replace("/mnt/c/", "C:/").replace("/", "\\")
            windows_path = Path(windows_path_str)
            if windows_path.exists() and windows_path.is_dir():
                logger.info(f"Converted WSL path {path} to accessible Windows path: {windows_path}")
                return windows_path

        # Try Windows to WSL conversion
        if str(path).startswith("C:"):
            wsl_path_str = str(path).replace("C:", "/mnt/c").replace("\\", "/")
            wsl_path = Path(wsl_path_str)
            if wsl_path.exists() and wsl_path.is_dir():
                logger.info(f"Converted Windows path {path} to accessible WSL path: {wsl_path}")
                return wsl_path

        # Log warning if path is not accessible
        logger.warning(f"Videos path is not accessible: {path}")
        return path

    def get_data_path(self) -> Path:
        """Get the data directory path"""
        if self.data_path:
            path = Path(self.data_path)
            path.mkdir(exist_ok=True)
            return path

        # Default data path
        path = Path(__file__).parent.parent.parent / "data"
        path.mkdir(exist_ok=True)
        return path

    def get_user_temp_path(self, user_id: int | str) -> Path:
        """
        Get a temporary directory path for user-specific data.

        User data (settings, progress, etc.) should be stored in temp directories
        to avoid committing user data to the repository.

        Args:
            user_id: The user ID

        Returns:
            Path to user's temp directory
        """
        import tempfile

        temp_base = Path(tempfile.gettempdir()) / "langplug" / "users" / str(user_id)
        temp_base.mkdir(parents=True, exist_ok=True)
        return temp_base

    def get_logs_path(self) -> Path:
        """Get the logs directory path"""
        if self.logs_path:
            return Path(self.logs_path)

        # Default logs path
        path = Path(__file__).parent.parent.parent / "logs"
        path.mkdir(exist_ok=True)
        return path


# Global settings instance
settings = Settings()
