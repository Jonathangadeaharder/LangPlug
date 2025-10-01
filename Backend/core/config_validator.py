"""Configuration validation and environment-specific settings"""

from enum import Enum
from pathlib import Path
from typing import Any


class Environment(str, Enum):
    """Application environments"""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class ConfigValidator:
    """Validate and provide environment-specific configuration"""

    @staticmethod
    def get_environment_config(env: Environment) -> dict[str, Any]:
        """Get environment-specific configuration overrides"""
        configs = {
            Environment.DEVELOPMENT: {"debug": True, "reload": True, "log_level": "DEBUG", "sqlalchemy_echo": False},
            Environment.TESTING: {
                "debug": True,
                "reload": False,
                "log_level": "INFO",
                "sqlalchemy_echo": False,
                "database_url": "sqlite+aiosqlite:///:memory:",
            },
            Environment.STAGING: {"debug": False, "reload": False, "log_level": "INFO", "sqlalchemy_echo": False},
            Environment.PRODUCTION: {
                "debug": False,
                "reload": False,
                "log_level": "WARNING",
                "sqlalchemy_echo": False,
                "cors_credentials": True,
            },
        }
        return configs.get(env, {})

    @staticmethod
    def _ensure_path_exists(path_str: str | None) -> None:
        """Ensure path exists, create if it doesn't"""
        if path_str:
            path = Path(path_str)
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _validate_paths(settings: Any) -> None:
        """Validate and create necessary paths"""
        ConfigValidator._ensure_path_exists(settings.videos_path)
        ConfigValidator._ensure_path_exists(settings.data_path)
        ConfigValidator._ensure_path_exists(settings.logs_path)

    @staticmethod
    def _validate_database(settings: Any, errors: list[str]) -> None:
        """Validate database configuration"""
        if settings.db_type != "postgresql":
            return

        if not settings.postgres_password:
            errors.append("PostgreSQL password is required for production")

        if not settings.database_url:
            settings.database_url = (
                f"postgresql+asyncpg://{settings.postgres_user}:"
                f"{settings.postgres_password}@{settings.postgres_host}:"
                f"{settings.postgres_port}/{settings.postgres_db}"
            )

    @staticmethod
    def _validate_security(settings: Any, errors: list[str]) -> None:
        """Validate security settings for production"""
        if settings.environment != Environment.PRODUCTION:
            return

        if not settings.secret_key or settings.secret_key == "":
            errors.append("Secret key must be set in production")
        if settings.debug:
            errors.append("Debug mode must be disabled in production")

    @staticmethod
    def _validate_services(settings: Any, errors: list[str]) -> None:
        """Validate service configurations"""
        valid_transcription = [
            "whisper-tiny",
            "whisper-base",
            "whisper-small",
            "whisper-medium",
            "whisper-large",
            "nemo-parakeet",
        ]
        if settings.transcription_service not in valid_transcription:
            errors.append(
                f"Invalid transcription service: {settings.transcription_service}. "
                f"Must be one of: {', '.join(valid_transcription)}"
            )

        valid_translation = [
            "opus-de-es",
            "opus-mt-de-en",
            "nllb-distilled-600m",
            "nllb-distilled-1.3b",
            "mbart-large-50",
        ]
        if settings.translation_service not in valid_translation:
            errors.append(
                f"Invalid translation service: {settings.translation_service}. "
                f"Must be one of: {', '.join(valid_translation)}"
            )

    @staticmethod
    def _validate_log_level(settings: Any, errors: list[str]) -> None:
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if settings.log_level.upper() not in valid_levels:
            errors.append(f"Invalid log level: {settings.log_level}. " f"Must be one of: {', '.join(valid_levels)}")

    @staticmethod
    def validate_config(settings: Any) -> None:
        """Validate configuration settings (Refactored for lower complexity)"""
        errors: list[str] = []

        # Run all validation checks
        ConfigValidator._validate_paths(settings)
        ConfigValidator._validate_database(settings, errors)
        ConfigValidator._validate_security(settings, errors)
        ConfigValidator._validate_services(settings, errors)
        ConfigValidator._validate_log_level(settings, errors)

        # Raise if any errors found
        if errors:
            error_message = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
            raise ValueError(error_message)

    @staticmethod
    def apply_environment_overrides(settings: Any) -> None:
        """Apply environment-specific configuration overrides"""
        try:
            env = Environment(settings.environment)
        except ValueError:
            env = Environment.DEVELOPMENT

        overrides = ConfigValidator.get_environment_config(env)
        for key, value in overrides.items():
            if hasattr(settings, key):
                # Only override if not explicitly set
                current_value = getattr(settings, key)
                if current_value is None or current_value == "":
                    setattr(settings, key, value)
