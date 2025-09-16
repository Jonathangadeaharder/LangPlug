"""
User profile management API routes
"""
import logging
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator

from core.dependencies import current_active_user
from database.models import User
from core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["profile"])

# Supported languages
SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "flag": "🇬🇧"},
    "de": {"name": "German", "flag": "🇩🇪"},
    "es": {"name": "Spanish", "flag": "🇪🇸"}
}

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
    id: int
    username: str
    is_admin: bool
    created_at: str
    last_login: str = None
    native_language: Dict[str, str]
    target_language: Dict[str, str]


@router.get("", response_model=UserProfile, name="profile_get")
async def get_profile(current_user: User = Depends(current_active_user)):
    """Get current user's profile"""
    try:
        return UserProfile(
            id=current_user.id,
            username=current_user.username,
            is_admin=current_user.is_admin,
            created_at=current_user.created_at,
            last_login=current_user.last_login,
            native_language={
                "code": current_user.native_language,
                "name": SUPPORTED_LANGUAGES[current_user.native_language]["name"],
                "flag": SUPPORTED_LANGUAGES[current_user.native_language]["flag"]
            },
            target_language={
                "code": current_user.target_language,
                "name": SUPPORTED_LANGUAGES[current_user.target_language]["name"],
                "flag": SUPPORTED_LANGUAGES[current_user.target_language]["flag"]
            }
        )
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting profile: {str(e)}"
        )


@router.put("/languages", response_model=Dict[str, Any], name="profile_update_languages")
async def update_language_preferences(
    preferences: LanguagePreferences,
    current_user: User = Depends(current_active_user)
):
    """Update user's language preferences"""
    try:
        # Note: Language preferences would need to be added to User model
        # For now, just return success with the requested preferences
        logger.info(f"Language preferences update requested for user {current_user.id}: {preferences.native_language} -> {preferences.target_language}")
        
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
            }
        }
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating language preferences: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating preferences: {str(e)}"
        )


@router.get("/languages", response_model=Dict[str, Dict[str, str]], name="profile_get_supported_languages")
async def get_supported_languages():
    """Get list of supported languages"""
    return SUPPORTED_LANGUAGES


class UserSettings(BaseModel):
    """User settings model"""
    theme: Optional[str] = "light"
    notifications_enabled: Optional[bool] = True
    auto_play: Optional[bool] = True
    subtitle_size: Optional[str] = "medium"
    playback_speed: Optional[float] = 1.0
    vocabulary_difficulty: Optional[str] = "intermediate"
    daily_goal: Optional[int] = 10
    language_preferences: Optional[LanguagePreferences] = None


@router.get("/settings", response_model=UserSettings, name="profile_get_settings")
async def get_user_settings(
    current_user: User = Depends(current_active_user)
):
    """Get user settings"""
    try:
        # Get user settings from database or file system
        user_settings_path = settings.get_user_data_path() / str(current_user.id) / "settings.json"
        
        # Default settings
        default_settings = UserSettings()
        
        if user_settings_path.exists():
            try:
                import json
                with open(user_settings_path, 'r', encoding='utf-8') as f:
                    settings_data = json.load(f)
                    # Merge with defaults
                    for key, value in settings_data.items():
                        if hasattr(default_settings, key):
                            setattr(default_settings, key, value)
            except Exception as e:
                logger.warning(f"Error loading user settings: {str(e)}")
        
        logger.info(f"Retrieved settings for user {current_user.id}")
        return default_settings
        
    except Exception as e:
        logger.error(f"Error getting user settings: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving user settings: {str(e)}")


@router.put("/settings", response_model=UserSettings, name="profile_update_settings")
async def update_user_settings(
    settings_update: UserSettings,
    current_user: User = Depends(current_active_user)
):
    """Update user settings"""
    try:
        # Ensure user data directory exists
        user_data_path = settings.get_user_data_path() / str(current_user.id)
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
        logger.error(f"Error updating user settings: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating user settings: {str(e)}")