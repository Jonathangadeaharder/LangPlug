"""
User profile management API routes
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator

from core.dependencies import current_active_user
from core.language_preferences import (
    SUPPORTED_LANGUAGES,
    DEFAULT_NATIVE_LANGUAGE,
    DEFAULT_TARGET_LANGUAGE,
    load_language_preferences,
    save_language_preferences,
    resolve_language_runtime_settings,
)
from database.models import User

logger = logging.getLogger(__name__)
router = APIRouter(tags=["profile"])

class LanguagePreferences(BaseModel):
    """Language preference update model"""
    native_language: str
    target_language: str

    @field_validator('native_language', 'target_language')
    @classmethod
    def validate_language(cls, v):
        if v not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Language must be one of: {', '.join(SUPPORTED_LANGUAGES.keys())}")
        return v

    @field_validator('target_language')
    @classmethod
    def validate_different_languages(cls, v, values):
        if 'native_language' in values.data and v == values.data['native_language']:
            raise ValueError("Target language must be different from native language")
        return v


class UserProfile(BaseModel):
    """User profile response model"""
    id: str  # Changed from int to str to match UUID
    username: str
    is_admin: bool
    created_at: str
    last_login: str | None = None  # Make it properly optional
    native_language: dict[str, str]
    target_language: dict[str, str]
    language_runtime: dict[str, Any]


@router.get("", response_model=UserProfile, name="profile_get")
async def get_profile(current_user: User = Depends(current_active_user)):
    """Get current user's profile"""
    try:
        user_id = str(current_user.id)
        native_code, target_code = load_language_preferences(user_id)

        runtime = resolve_language_runtime_settings(native_code, target_code)

        return UserProfile(
            id=user_id,
            username=current_user.username,
            is_admin=current_user.is_superuser,
            created_at=current_user.created_at.isoformat() if current_user.created_at else None,
            last_login=current_user.last_login.isoformat() if current_user.last_login else None,
            native_language={
                "code": native_code,
                "name": SUPPORTED_LANGUAGES[native_code]["name"],
                "flag": SUPPORTED_LANGUAGES[native_code]["flag"]
            },
            target_language={
                "code": target_code,
                "name": SUPPORTED_LANGUAGES[target_code]["name"],
                "flag": SUPPORTED_LANGUAGES[target_code]["flag"]
            },
            language_runtime=runtime,
        )
    except Exception as e:
        logger.error(f"Error getting profile: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting profile: {e!s}"
        )


@router.put("/languages", response_model=dict[str, Any], name="profile_update_languages")
async def update_language_preferences(
    preferences: LanguagePreferences,
    current_user: User = Depends(current_active_user)
):
    """Update user's language preferences"""
    try:
        # Note: Language preferences would need to be added to User model
        # For now, just return success with the requested preferences
        logger.info(f"Language preferences update requested for user {current_user.id}: {preferences.native_language} -> {preferences.target_language}")

        user_id = str(current_user.id)
        save_language_preferences(user_id, preferences.native_language, preferences.target_language)
        runtime = resolve_language_runtime_settings(preferences.native_language, preferences.target_language)

        return {
            "success": True,
            "message": "Language preferences updated successfully",
            "native_language": {
                "code": preferences.native_language,
                "name": SUPPORTED_LANGUAGES[preferences.native_language]["name"],
                "flag": SUPPORTED_LANGUAGES[preferences.native_language]["flag"]
            },
            "target_language": {
                "code": preferences.target_language,
                "name": SUPPORTED_LANGUAGES[preferences.target_language]["name"],
                "flag": SUPPORTED_LANGUAGES[preferences.target_language]["flag"]
            },
            "language_runtime": runtime,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating language preferences: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating preferences: {e!s}"
        )


@router.get("/languages", response_model=dict[str, dict[str, str]], name="profile_get_supported_languages")
async def get_supported_languages():
    """Get list of supported languages"""
    return SUPPORTED_LANGUAGES


class UserSettings(BaseModel):
    """User settings model"""
    theme: str | None = "light"
    notifications_enabled: bool | None = True
    auto_play: bool | None = True
    subtitle_size: str | None = "medium"
    playback_speed: float | None = 1.0
    vocabulary_difficulty: str | None = "intermediate"
    daily_goal: int | None = 10
    language_preferences: LanguagePreferences | None = None


@router.get("/settings", response_model=UserSettings, name="profile_get_settings")
async def get_user_settings(
    current_user: User = Depends(current_active_user)
):
    """Get user settings"""
    try:
        # Get user settings from database or file system
        user_settings_path = settings.get_data_path() / str(current_user.id) / "settings.json"

        # Default settings
        default_settings = UserSettings()

        if user_settings_path.exists():
            try:
                import json
                with open(user_settings_path, encoding='utf-8') as f:
                    settings_data = json.load(f)
                    # Merge with defaults
                    for key, value in settings_data.items():
                        if hasattr(default_settings, key):
                            setattr(default_settings, key, value)
            except Exception as e:
                logger.warning(f"Error loading user settings: {e!s}")

        logger.info(f"Retrieved settings for user {current_user.id}")
        return default_settings

    except Exception as e:
        logger.error(f"Error getting user settings: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving user settings: {e!s}")


@router.put("/settings", response_model=UserSettings, name="profile_update_settings")
async def update_user_settings(
    settings_update: UserSettings,
    current_user: User = Depends(current_active_user)
):
    """Update user settings"""
    try:
        # Ensure user data directory exists
        user_data_path = settings.get_data_path() / str(current_user.id)
        user_data_path.mkdir(parents=True, exist_ok=True)

        user_settings_path = user_data_path / "settings.json"

        # Save settings to file
        import json
        settings_dict = settings_update.dict(exclude_none=True)

        with open(user_settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"Updated settings for user {current_user.id}")
        return settings_update

    except Exception as e:
        logger.error(f"Error updating user settings: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating user settings: {e!s}")
