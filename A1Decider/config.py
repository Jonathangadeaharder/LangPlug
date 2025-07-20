#!/usr/bin/env python3
"""
Centralized Configuration Module for A1Decider

This module provides a single source of truth for all application configuration,
including file paths, model settings, and other configurable parameters.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class WordListConfig:
    """Configuration for word list files."""
    a1_words: str
    charaktere_words: str
    giuliwords: str
    brands: str
    onomatopoeia: str
    interjections: str
    
    def get_all_files(self) -> List[str]:
        """Get all word list file paths."""
        return [
            self.a1_words,
            self.charaktere_words,
            self.giuliwords,
            self.brands,
            self.onomatopoeia,
            self.interjections
        ]
    
    def get_core_files(self) -> List[str]:
        """Get core word list files (a1, charaktere, giuliwords)."""
        return [
            self.a1_words,
            self.charaktere_words,
            self.giuliwords
        ]


@dataclass
class ModelConfig:
    """Configuration for machine learning models."""
    spacy_model: str
    whisper_model: str
    translation_model: str
    device: str
    

@dataclass
class FilePathConfig:
    """Configuration for file paths and directories."""
    base_dir: str
    output_dir: str
    temp_dir: str
    global_unknowns_file: str
    
    def ensure_directories(self) -> None:
        """Ensure all configured directories exist."""
        for dir_path in [self.output_dir, self.temp_dir]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)


@dataclass
class ProcessingConfig:
    """Configuration for processing parameters."""
    batch_size: int
    max_subtitle_length: int
    min_word_frequency: int
    default_language: str
    supported_languages: List[str]
    subtitle_formats: List[str]
    

@dataclass
class APIConfig:
    """Configuration for API server."""
    host: str
    port: int
    debug: bool
    cors_origins: List[str]
    max_file_size: int
    

@dataclass
class UIConfig:
    """Configuration for user interface."""
    refresh_rate: int
    progress_update_interval: int
    console_width: int
    default_style: str
    

@dataclass
class DatabaseConfig:
    """Configuration for database settings."""
    enabled: bool
    database_path: str
    backup_enabled: bool
    backup_directory: str
    cache_size: int
    journal_mode: str
    migration_batch_size: int
    auto_vacuum: bool
    

class AppConfig:
    """Main application configuration class."""
    
    def __init__(self, base_dir: Optional[str] = None):
        """Initialize configuration with optional base directory override."""
        if base_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.base_dir = Path(base_dir)
        self._load_config()
    
    def _load_config(self) -> None:
        """Load all configuration sections."""
        # Word List Configuration
        self.word_lists = WordListConfig(
            a1_words=str(self.base_dir / "a1.txt"),
            charaktere_words=str(self.base_dir / "charaktere.txt"),
            giuliwords=str(self.base_dir / "giuliwords.txt"),
            brands=str(self.base_dir / "brands.txt"),
            onomatopoeia=str(self.base_dir / "onomatopoeia.txt"),
            interjections=str(self.base_dir / "interjections.txt")
        )
        
        # Model Configuration
        self.models = ModelConfig(
            spacy_model="de_core_news_sm",
            whisper_model="base",
            translation_model="Helsinki-NLP/opus-mt-de-es",
            device="auto"  # auto-detect GPU/CPU
        )
        
        # File Path Configuration
        self.file_paths = FilePathConfig(
            base_dir=str(self.base_dir),
            output_dir=str(self.base_dir / "output"),
            temp_dir=str(self.base_dir / "temp"),
            global_unknowns_file=str(self.base_dir / "globalunknowns.json")
        )
        
        # Processing Configuration
        self.processing = ProcessingConfig(
            batch_size=20,
            max_subtitle_length=200,
            min_word_frequency=1,
            default_language="de",
            supported_languages=["de", "en", "es", "fr", "it"],
            subtitle_formats=[".srt", ".vtt"]
        )
        
        # API Configuration
        self.api = APIConfig(
            host="0.0.0.0",
            port=8000,
            debug=False,
            cors_origins=["*"],
            max_file_size=100 * 1024 * 1024  # 100MB
        )
        
        # UI Configuration
        self.ui = UIConfig(
            refresh_rate=4,
            progress_update_interval=100,
            console_width=120,
            default_style="bold green"
        )
        
        # Database Configuration
        self.database = DatabaseConfig(
            enabled=os.getenv("A1DECIDER_USE_DATABASE", "false").lower() == "true",
            database_path=str(self.base_dir / "vocabulary.db"),
            backup_enabled=True,
            backup_directory=str(self.base_dir / "backups"),
            cache_size=10000,
            journal_mode="WAL",
            migration_batch_size=1000,
            auto_vacuum=True
        )
        
        # Environment variable overrides
        self._apply_env_overrides()
        
        # Ensure directories exist
        self.file_paths.ensure_directories()
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        # API configuration overrides
        if os.getenv("API_HOST"):
            self.api.host = os.getenv("API_HOST")
        if os.getenv("API_PORT"):
            self.api.port = int(os.getenv("API_PORT"))
        if os.getenv("API_DEBUG"):
            self.api.debug = os.getenv("API_DEBUG").lower() == "true"
        
        # Model configuration overrides
        if os.getenv("WHISPER_MODEL"):
            self.models.whisper_model = os.getenv("WHISPER_MODEL")
        if os.getenv("SPACY_MODEL"):
            self.models.spacy_model = os.getenv("SPACY_MODEL")
        if os.getenv("DEVICE"):
            self.models.device = os.getenv("DEVICE")
        
        # File path overrides
        if os.getenv("A1_DECIDER_PATH"):
            base_path = Path(os.getenv("A1_DECIDER_PATH"))
            self.word_lists.a1_words = str(base_path / "a1.txt")
            self.word_lists.charaktere_words = str(base_path / "charaktere.txt")
            self.word_lists.giuliwords = str(base_path / "giuliwords.txt")
            self.word_lists.brands = str(base_path / "brands.txt")
            self.word_lists.onomatopoeia = str(base_path / "onomatopoeia.txt")
            self.word_lists.interjections = str(base_path / "interjections.txt")
            self.file_paths.global_unknowns_file = str(base_path / "globalunknowns.json")
        
        # Database configuration overrides
        if os.getenv("A1DECIDER_DB_PATH"):
            self.database.database_path = os.getenv("A1DECIDER_DB_PATH")
        if os.getenv("A1DECIDER_DB_CACHE_SIZE"):
            self.database.cache_size = int(os.getenv("A1DECIDER_DB_CACHE_SIZE"))
        if os.getenv("A1DECIDER_DB_JOURNAL_MODE"):
            self.database.journal_mode = os.getenv("A1DECIDER_DB_JOURNAL_MODE")
        if os.getenv("A1DECIDER_DB_BACKUP_DIR"):
            self.database.backup_directory = os.getenv("A1DECIDER_DB_BACKUP_DIR")
    
    def validate_config(self) -> Dict[str, bool]:
        """Validate configuration and return status of required components."""
        validation_results = {}
        
        # Check word list files
        for file_path in self.word_lists.get_core_files():
            file_name = Path(file_path).name
            validation_results[f"word_list_{file_name}"] = os.path.exists(file_path)
        
        # Check directories
        validation_results["base_directory"] = os.path.exists(self.file_paths.base_dir)
        validation_results["output_directory"] = os.path.exists(self.file_paths.output_dir)
        validation_results["temp_directory"] = os.path.exists(self.file_paths.temp_dir)
        
        # Check database configuration
        if self.database.enabled:
            validation_results["database_enabled"] = True
            validation_results["database_path_valid"] = (
                os.path.exists(self.database.database_path) or 
                os.path.exists(os.path.dirname(self.database.database_path))
            )
            if self.database.backup_enabled:
                validation_results["backup_directory"] = (
                    os.path.exists(self.database.backup_directory) or
                    os.access(os.path.dirname(self.database.backup_directory), os.W_OK)
                )
        else:
            validation_results["database_enabled"] = False
        
        return validation_results
    
    def get_pipeline_config(self, pipeline_type: str) -> Dict[str, Any]:
        """Get configuration for specific pipeline type."""
        base_config = {
            "batch_size": self.processing.batch_size,
            "language": self.processing.default_language,
            "word_lists": self.word_lists.get_all_files(),
            "models": {
                "spacy": self.models.spacy_model,
                "whisper": self.models.whisper_model,
                "translation": self.models.translation_model
            }
        }
        
        # Pipeline-specific configurations
        pipeline_configs = {
            "quick": {
                **base_config,
                "steps": ["transcription"],
                "quality": "fast"
            },
            "learning": {
                **base_config,
                "steps": ["transcription", "filtering"],
                "quality": "balanced"
            },
            "full": {
                **base_config,
                "steps": ["preview", "transcription", "filtering", "translation"],
                "quality": "high"
            },
            "batch": {
                **base_config,
                "steps": ["transcription", "filtering", "translation"],
                "quality": "balanced",
                "batch_mode": True
            }
        }
        
        return pipeline_configs.get(pipeline_type, base_config)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary format."""
        return {
            "word_lists": {
                "a1_words": self.word_lists.a1_words,
                "charaktere_words": self.word_lists.charaktere_words,
                "giuliwords": self.word_lists.giuliwords,
                "brands": self.word_lists.brands,
                "onomatopoeia": self.word_lists.onomatopoeia,
                "interjections": self.word_lists.interjections
            },
            "models": {
                "spacy_model": self.models.spacy_model,
                "whisper_model": self.models.whisper_model,
                "translation_model": self.models.translation_model,
                "device": self.models.device
            },
            "file_paths": {
                "base_dir": self.file_paths.base_dir,
                "output_dir": self.file_paths.output_dir,
                "temp_dir": self.file_paths.temp_dir,
                "global_unknowns_file": self.file_paths.global_unknowns_file
            },
            "processing": {
                "batch_size": self.processing.batch_size,
                "max_subtitle_length": self.processing.max_subtitle_length,
                "min_word_frequency": self.processing.min_word_frequency,
                "default_language": self.processing.default_language,
                "supported_languages": self.processing.supported_languages,
                "subtitle_formats": self.processing.subtitle_formats
            },
            "api": {
                "host": self.api.host,
                "port": self.api.port,
                "debug": self.api.debug,
                "cors_origins": self.api.cors_origins,
                "max_file_size": self.api.max_file_size
            },
            "ui": {
                "refresh_rate": self.ui.refresh_rate,
                "progress_update_interval": self.ui.progress_update_interval,
                "console_width": self.ui.console_width,
                "default_style": self.ui.default_style
            },
            "database": {
                "enabled": self.database.enabled,
                "database_path": self.database.database_path,
                "backup_enabled": self.database.backup_enabled,
                "backup_directory": self.database.backup_directory,
                "cache_size": self.database.cache_size,
                "journal_mode": self.database.journal_mode,
                "migration_batch_size": self.database.migration_batch_size,
                "auto_vacuum": self.database.auto_vacuum
            }
        }


# Global configuration instance
_config_instance = None

def get_config(base_dir: Optional[str] = None) -> AppConfig:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None or base_dir is not None:
        _config_instance = AppConfig(base_dir)
    return _config_instance


# Convenience functions for common configuration access
def get_word_list_files() -> List[str]:
    """Get all word list file paths."""
    return get_config().word_lists.get_all_files()

def get_core_word_list_files() -> List[str]:
    """Get core word list file paths (a1, charaktere, giuliwords)."""
    return get_config().word_lists.get_core_files()

def get_global_unknowns_file() -> str:
    """Get the global unknowns file path."""
    return get_config().file_paths.global_unknowns_file

def get_spacy_model() -> str:
    """Get the spaCy model name."""
    return get_config().models.spacy_model

def get_whisper_model() -> str:
    """Get the Whisper model name."""
    return get_config().models.whisper_model

def get_batch_size() -> int:
    """Get the processing batch size."""
    return get_config().processing.batch_size

def get_api_config() -> APIConfig:
    """Get the API configuration."""
    return get_config().api

def get_database_config() -> DatabaseConfig:
    """Get the database configuration."""
    return get_config().database

def is_database_enabled() -> bool:
    """Check if database mode is enabled."""
    return get_config().database.enabled


if __name__ == "__main__":
    # Configuration validation and testing
    config = get_config()
    print("A1Decider Configuration:")
    print(f"Base Directory: {config.file_paths.base_dir}")
    print(f"Word Lists: {config.word_lists.get_core_files()}")
    print(f"Models: spaCy={config.models.spacy_model}, Whisper={config.models.whisper_model}")
    print(f"API: {config.api.host}:{config.api.port}")
    
    validation = config.validate_config()
    print("\nValidation Results:")
    for component, status in validation.items():
        status_str = "✓" if status else "✗"
        print(f"  {status_str} {component}")