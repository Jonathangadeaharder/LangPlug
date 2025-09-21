"""
Configuration management using Pydantic Settings
"""
import json
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

    # Server settings
    host: str = Field(default="0.0.0.0", alias="LANGPLUG_HOST")
    port: int = Field(default=8000, alias="LANGPLUG_PORT")
    reload: bool = Field(default=True, alias="LANGPLUG_RELOAD")
    debug: bool = Field(default=True, alias="LANGPLUG_DEBUG")
    sqlalchemy_echo: bool = Field(default=False, alias="LANGPLUG_SQLALCHEMY_ECHO")

    # Database settings
    database_url: str | None = Field(default=None, alias="LANGPLUG_DATABASE_URL")
    db_type: str = Field(default="sqlite", alias="LANGPLUG_DB_TYPE")  # sqlite or postgresql
    postgres_host: str = Field(default="localhost", alias="LANGPLUG_POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="LANGPLUG_POSTGRES_PORT")
    postgres_db: str = Field(default="langplug", alias="LANGPLUG_POSTGRES_DB")
    postgres_user: str = Field(default="langplug_user", alias="LANGPLUG_POSTGRES_USER")
    postgres_password: str = Field(default="langplug_password", alias="LANGPLUG_POSTGRES_PASSWORD")
    postgres_pool_size: int = Field(default=10, alias="LANGPLUG_POSTGRES_POOL_SIZE")
    postgres_max_overflow: int = Field(default=20, alias="LANGPLUG_POSTGRES_MAX_OVERFLOW")

    # CORS settings
    cors_origins: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://localhost:5173",
            "http://127.0.0.1:5173"
        ],
        alias="LANGPLUG_CORS_ORIGINS"
    )
    cors_credentials: bool = Field(default=True, alias="LANGPLUG_CORS_CREDENTIALS")

    # File paths
    videos_path: str | None = Field(default=None, alias="LANGPLUG_VIDEOS_PATH")
    data_path: str | None = Field(default=None, alias="LANGPLUG_DATA_PATH")
    logs_path: str | None = Field(default=None, alias="LANGPLUG_LOGS_PATH")

    # Service settings
    transcription_service: str = Field(default="whisper-tiny", alias="LANGPLUG_TRANSCRIPTION_SERVICE")
    translation_service: str = Field(default="opus-de-es", alias="LANGPLUG_TRANSLATION_SERVICE")  # Fast for testing
    default_language: str = Field(default="de", alias="LANGPLUG_DEFAULT_LANGUAGE")

    # SpaCy model settings
    spacy_model_de: str = Field(default="de_core_news_sm", alias="LANGPLUG_SPACY_MODEL_DE")
    spacy_model_en: str = Field(default="en_core_web_sm", alias="LANGPLUG_SPACY_MODEL_EN")

    # Security settings
    secret_key: str = Field(default="your-secret-key-change-in-production", alias="LANGPLUG_SECRET_KEY")
    session_timeout_hours: int = Field(default=24, alias="LANGPLUG_SESSION_TIMEOUT_HOURS")

    # Sentry settings
    sentry_dsn: str = Field(
        default="",
        alias="SENTRY_DSN",
        description="Sentry DSN for error tracking"
    )
    environment: str = Field(
        default="development",
        alias="ENVIRONMENT",
        description="Environment name (development, staging, production)"
    )

    # Performance settings
    max_upload_size: int = Field(default=100 * 1024 * 1024, alias="LANGPLUG_MAX_UPLOAD_SIZE")  # 100MB
    task_cleanup_interval: int = Field(default=3600, alias="LANGPLUG_TASK_CLEANUP_INTERVAL")  # 1 hour

    # Logging settings
    log_level: str = Field(default="INFO", alias="LANGPLUG_LOG_LEVEL")
    log_format: str = Field(default="json", alias="LANGPLUG_LOG_FORMAT")  # json or text

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }

    @field_validator('cors_origins')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from environment variable if it's a string"""
        if isinstance(v, str):
            try:
                # Try to parse as JSON array
                return json.loads(v)
            except json.JSONDecodeError:
                # Fall back to comma-separated values
                return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v

    def get_database_url(self) -> str:
        """Get the database connection URL"""
        if self.database_url:
            return self.database_url

        if self.db_type == "postgresql":
            return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        else:
            # Default SQLite database path
            base_path = Path(self.data_path) if self.data_path else Path(__file__).parent.parent / "data"
            base_path.mkdir(exist_ok=True)
            db_path = base_path / "langplug.db"
            return f"sqlite:///{db_path}"

    def get_database_path(self) -> Path:
        """Get the database file path (for SQLite only)"""
        if self.database_url and self.database_url.startswith("sqlite:///"):
            return Path(self.database_url.replace("sqlite:///", ""))

        # Default database path
        base_path = Path(self.data_path) if self.data_path else Path(__file__).parent.parent / "data"
        base_path.mkdir(exist_ok=True)
        return base_path / "langplug.db"

    def get_videos_path(self) -> Path:
        """Get the videos directory path"""
        if self.videos_path:
            return Path(self.videos_path)

        # Default videos path (one level up from Backend)
        return Path(__file__).parent.parent.parent / "videos"

    def get_data_path(self) -> Path:
        """Get the data directory path"""
        if self.data_path:
            path = Path(self.data_path)
            path.mkdir(exist_ok=True)
            return path

        # Default data path
        path = Path(__file__).parent.parent / "data"
        path.mkdir(exist_ok=True)
        return path

    def get_logs_path(self) -> Path:
        """Get the logs directory path"""
        if self.logs_path:
            return Path(self.logs_path)

        # Default logs path
        path = Path(__file__).parent.parent / "logs"
        path.mkdir(exist_ok=True)
        return path


# Global settings instance
settings = Settings()
