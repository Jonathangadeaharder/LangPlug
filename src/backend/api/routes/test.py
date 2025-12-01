"""
Test utility API routes for e2e testing
"""

from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config.logging_config import get_logger
from core.database import get_async_session
from database.models import User, UserVocabularyProgress

logger = get_logger(__name__)
router = APIRouter(tags=["test"])


@router.delete("/cleanup")
async def cleanup_test_data(db: AsyncSession = Depends(get_async_session)):
    """
    Clean up test data created by e2e tests

    Deletes all users and related data that match e2e test patterns:
    - Users with emails matching e2e.*@langplug.com
    - Users with usernames starting with e2euser_

    **Authentication Required**: No (only available in debug mode)

    Returns:
        dict: Cleanup summary with counts of deleted records
    """
    try:
        # Find test users by email pattern or username pattern
        result = await db.execute(
            select(User).where((User.email.like("e2e.%@langplug.com")) | (User.username.like("e2euser_%")))
        )
        test_users = result.scalars().all()

        deleted_users = 0
        deleted_vocabulary = 0

        for user in test_users:
            # Delete user's vocabulary progress
            vocab_result = await db.execute(
                delete(UserVocabularyProgress).where(UserVocabularyProgress.user_id == user.id)
            )
            deleted_vocabulary += vocab_result.rowcount

            # Delete user
            user_result = await db.execute(delete(User).where(User.id == user.id))
            deleted_users += user_result.rowcount

        await db.commit()

        logger.info("Test cleanup completed", users=deleted_users, vocabulary=deleted_vocabulary)

        return {
            "success": True,
            "deleted_users": deleted_users,
            "deleted_vocabulary": deleted_vocabulary,
            "message": "Test data cleaned up successfully",
        }

    except Exception as e:
        await db.rollback()
        logger.error("Test cleanup failed", error=str(e), exc_info=True)
        return {"success": False, "error": str(e), "message": "Test cleanup failed"}
