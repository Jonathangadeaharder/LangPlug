"""
User profile management API routes
"""
import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator

from core.dependencies import get_current_user, get_auth_service
from services.authservice.auth_service import AuthUser, AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/profile", tags=["profile"])

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


@router.get("", response_model=UserProfile)
async def get_profile(current_user: AuthUser = Depends(get_current_user)):
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


@router.put("/languages", response_model=Dict[str, Any])
async def update_language_preferences(
    preferences: LanguagePreferences,
    current_user: AuthUser = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Update user's language preferences"""
    try:
        # Update preferences in database
        success = auth_service.update_language_preferences(
            current_user.id,
            preferences.native_language,
            preferences.target_language
        )
        
        if success:
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
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update language preferences"
            )
            
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


@router.get("/languages", response_model=Dict[str, Dict[str, str]])
async def get_supported_languages():
    """Get list of supported languages"""
    return SUPPORTED_LANGUAGES