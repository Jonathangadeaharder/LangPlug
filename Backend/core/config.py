"""
Configuration management using Pydantic Settings
"""
import json
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="LANGPLUG_HOST")
    port: int = Field(default=8000, env="LANGPLUG_PORT")
    reload: bool = Field(default=True, env="LANGPLUG_RELOAD")
    debug: bool = Field(default=True, env="LANGPLUG_DEBUG")
    
    # Database settings
    database_url: Optional[str] = Field(default=None, env="LANGPLUG_DATABASE_URL")
    
    # CORS settings
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:3000", 
            "http://localhost:3001",
            "http://127.0.0.1:3000", 
            "http://127.0.0.1:3001",
            "http://localhost:5173", 
            "http://127.0.0.1:5173"
        ], 
        env="LANGPLUG_CORS_ORIGINS"
    )
    cors_credentials: bool = Field(default=True, env="LANGPLUG_CORS_CREDENTIALS")
    
    # File paths
    videos_path: Optional[str] = Field(default=None, env="LANGPLUG_VIDEOS_PATH")
    data_path: Optional[str] = Field(default=None, env="LANGPLUG_DATA_PATH")
    logs_path: Optional[str] = Field(default=None, env="LANGPLUG_LOGS_PATH")
    
    # Service settings
    transcription_service: str = Field(default="whisper", env="LANGPLUG_TRANSCRIPTION_SERVICE")
    translation_service: str = Field(default="nllb", env="LANGPLUG_TRANSLATION_SERVICE")
    default_language: str = Field(default="de", env="LANGPLUG_DEFAULT_LANGUAGE")
    
    # SpaCy model settings
    spacy_model_de: str = Field(default="de_core_news_sm", env="LANGPLUG_SPACY_MODEL_DE")
    spacy_model_en: str = Field(default="en_core_web_sm", env="LANGPLUG_SPACY_MODEL_EN")
    
    # Security settings
    session_timeout_hours: int = Field(default=24, env="LANGPLUG_SESSION_TIMEOUT_HOURS")
    
    # Performance settings
    max_upload_size: int = Field(default=100 * 1024 * 1024, env="LANGPLUG_MAX_UPLOAD_SIZE")  # 100MB
    task_cleanup_interval: int = Field(default=3600, env="LANGPLUG_TASK_CLEANUP_INTERVAL")  # 1 hour
    
    # Logging settings
    log_level: str = Field(default="INFO", env="LANGPLUG_LOG_LEVEL")
    log_format: str = Field(default="json", env="LANGPLUG_LOG_FORMAT")  # json or text
    
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
        
    def get_database_path(self) -> Path:
        """Get the database file path"""
        if self.database_url:
            # Handle file:// URLs or return as-is for other schemes
            if self.database_url.startswith("sqlite:///"):
                return Path(self.database_url.replace("sqlite:///", ""))
            return Path(self.database_url)
        
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
            return Path(self.data_path)
        
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