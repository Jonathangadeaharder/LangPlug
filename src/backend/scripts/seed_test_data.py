#!/usr/bin/env python3
"""
Seed Test Data Script
Populates the database with deterministic data for testing.
Usage: python scripts/seed_test_data.py
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add backend root to path
BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings
from database.models import Base, ProcessingSession, User, UserVocabularyProgress, VocabularyWord

# Test Data
TEST_EMAIL = "e2etest@example.com"
TEST_PASSWORD = "TestPassword123!"
MOCK_VIDEO_FILENAME = "Mock_Video_Episode_1.mp4"


async def seed_data():
    print("[*] Seeding test data...")

    # Database URL
    db_url = settings.get_database_url()
    # Use sqlite+aiosqlite
    if db_url.startswith("sqlite:///"):
        db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")

    print(f"[*] Connecting to {db_url}")

    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        print("[*] Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("[*] Creating tables...")
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # 1. Create User
        print("[*] Creating test user...")
        password_hash = PasswordHash([Argon2Hasher()]).hash(TEST_PASSWORD)
        user = User(
            email=TEST_EMAIL,
            username="e2etest",
            hashed_password=password_hash,
            is_active=True,
            is_verified=True,
            native_language="en",
            target_language="de",
        )
        session.add(user)
        await session.flush()  # Get ID

        # 2. Create Vocabulary
        print("[*] Creating vocabulary words...")
        words = [
            ("Hallo", "hallo", "A1", "noun", "Hello"),
            ("Welt", "welt", "A1", "noun", "World"),
            ("Tschuss", "tschuss", "A1", "particle", "Bye"),
            ("Haus", "haus", "A1", "noun", "House"),
            ("Katze", "katze", "A1", "noun", "Cat"),
            ("Hund", "hund", "A1", "noun", "Dog"),
            ("lernen", "lernen", "A2", "verb", "to learn"),
            ("verstehen", "verstehen", "A2", "verb", "to understand"),
            ("kompliziert", "kompliziert", "B1", "adjective", "complicated"),
            ("Wissenschaft", "wissenschaft", "B2", "noun", "Science"),
        ]

        vocab_objects = []
        for word, lemma, level, pos, trans in words:
            vw = VocabularyWord(
                word=word, lemma=lemma, language="de", difficulty_level=level, part_of_speech=pos, translation_en=trans
            )
            session.add(vw)
            vocab_objects.append(vw)

        await session.flush()

        # 3. Create User Progress
        print("[*] Creating user progress...")
        # Mark first 3 as known
        for i in range(3):
            prog = UserVocabularyProgress(
                user_id=user.id,
                vocabulary_id=vocab_objects[i].id,
                lemma=vocab_objects[i].lemma,
                language="de",
                is_known=True,
                confidence_level=5,
                review_count=1,
            )
            session.add(prog)

        # 4. Create Mock Video File
        print("[*] Creating mock video file...")
        # Determine repo root relative to this script
        repo_root = BACKEND_ROOT.parent.parent
        videos_dir = repo_root / "videos"

        if not videos_dir.exists():
            videos_dir.mkdir(parents=True)

        mock_series_dir = videos_dir / "MockSeries"
        mock_series_dir.mkdir(exist_ok=True)

        mock_video_path = mock_series_dir / MOCK_VIDEO_FILENAME
        if not mock_video_path.exists():
            # Create a dummy file (non-zero to avoid crash?)
            # Actually, backend crash was due to 0 byte file.
            # I'll write some text into it.
            mock_video_path.write_text("Mock Video Content - Not playable but exists.")
            print(f"   Created {mock_video_path}")
        else:
            print(f"   Exists {mock_video_path}")

        # 5. Create Processing Session
        print("[*] Creating processing session...")
        ps = ProcessingSession(
            session_id=f"mock_session_{datetime.now().timestamp()}",
            user_id=user.id,
            content_type="video",
            content_path=str(mock_video_path),
            language="de",
            status="completed",
            processing_time_seconds=1.5,
            created_at=datetime.now(),
            completed_at=datetime.now(),
        )
        session.add(ps)

        await session.commit()
        print("[*] Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_data())
