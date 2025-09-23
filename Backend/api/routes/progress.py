"""Progress tracking API routes"""
import json
import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.config import settings
from core.dependencies import current_active_user
from database.models import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["progress"])


class UserProgress(BaseModel):
    """User progress model"""
    user_id: str
    total_videos_watched: int = 0
    total_watch_time: float = 0.0  # in minutes
    vocabulary_learned: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    level: str = "Beginner"
    experience_points: int = 0
    daily_goals_completed: int = 0
    weekly_goals_completed: int = 0
    last_activity: datetime | None = None
    achievements: list[str] = []
    learning_stats: dict[str, Any] = {}


class DailyProgress(BaseModel):
    """Daily progress model"""
    date: str
    videos_watched: int = 0
    watch_time: float = 0.0
    vocabulary_learned: int = 0
    goals_completed: int = 0
    experience_gained: int = 0


@router.get("/user", response_model=UserProgress, name="progress_get_user")
async def get_user_progress(
    current_user: User = Depends(current_active_user)
):
    """Get progress data for the current user"""
    try:
        # Get user progress from database or file system
        user_progress_path = settings.get_data_path() / str(current_user.id) / "progress.json"

        # Default progress
        default_progress = UserProgress(
            user_id=str(current_user.id),
            last_activity=datetime.now()
        )

        if user_progress_path.exists():
            try:
                with open(user_progress_path, encoding='utf-8') as f:
                    progress_data = json.load(f)

                    # Convert datetime string back to datetime object
                    if progress_data.get('last_activity'):
                        progress_data['last_activity'] = datetime.fromisoformat(progress_data['last_activity'])

                    # Merge with defaults
                    for key, value in progress_data.items():
                        if hasattr(default_progress, key):
                            setattr(default_progress, key, value)

            except Exception as e:
                logger.warning(f"Error loading user progress: {e!s}")

        # Calculate current streak based on last activity
        if default_progress.last_activity:
            days_since_activity = (datetime.now() - default_progress.last_activity).days
            if days_since_activity > 1:
                default_progress.current_streak = 0

        logger.info(f"Retrieved progress for user {current_user.id}")
        return default_progress

    except Exception as e:
        logger.error(f"Error getting user progress: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving user progress: {e!s}")


@router.post("/update", name="progress_update_user")
async def update_user_progress(
    progress_update: dict[str, Any],
    current_user: User = Depends(current_active_user)
):
    """Update user progress data"""
    try:
        # Get current progress
        current_progress = await get_user_progress(current_user)

        # Update fields
        for key, value in progress_update.items():
            if hasattr(current_progress, key):
                setattr(current_progress, key, value)

        # Update last activity
        current_progress.last_activity = datetime.now()

        # Ensure user data directory exists
        user_data_path = settings.get_data_path() / str(current_user.id)
        user_data_path.mkdir(parents=True, exist_ok=True)

        user_progress_path = user_data_path / "progress.json"

        # Save progress to file
        progress_dict = current_progress.dict()
        # Convert datetime to string for JSON serialization
        if progress_dict['last_activity']:
            progress_dict['last_activity'] = progress_dict['last_activity'].isoformat()

        with open(user_progress_path, 'w', encoding='utf-8') as f:
            json.dump(progress_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"Updated progress for user {current_user.id}")
        return {"message": "Progress updated successfully"}

    except Exception as e:
        logger.error(f"Error updating user progress: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating user progress: {e!s}")


@router.get("/daily", response_model=list[DailyProgress], name="progress_get_daily")
async def get_daily_progress(
    days: int = 7,
    current_user: User = Depends(current_active_user)
):
    """Get daily progress for the last N days"""
    try:
        # Get daily progress from database or file system
        user_daily_path = settings.get_data_path() / str(current_user.id) / "daily_progress.json"

        daily_progress = []

        if user_daily_path.exists():
            try:
                with open(user_daily_path, encoding='utf-8') as f:
                    daily_data = json.load(f)

                    # Get last N days
                    for i in range(days):
                        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                        day_data = daily_data.get(date, {})
                        daily_progress.append(DailyProgress(
                            date=date,
                            **day_data
                        ))

            except Exception as e:
                logger.warning(f"Error loading daily progress: {e!s}")

        # Fill in missing days with empty progress
        if len(daily_progress) < days:
            for i in range(len(daily_progress), days):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                daily_progress.append(DailyProgress(date=date))

        # Sort by date (most recent first)
        daily_progress.sort(key=lambda x: x.date, reverse=True)

        logger.info(f"Retrieved {len(daily_progress)} days of progress for user {current_user.id}")
        return daily_progress

    except Exception as e:
        logger.error(f"Error getting daily progress: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving daily progress: {e!s}")
