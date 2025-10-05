"""Tests for legacy level-oriented helpers on VocabularyService."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from core.database import Base
from database.models import User, UserVocabularyProgress, VocabularyWord
from services.vocabulary.vocabulary_service import VocabularyService


@pytest.fixture
async def in_memory_session(monkeypatch) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Provide an in-memory SQLite session maker that the service will use."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    monkeypatch.setattr("services.vocabulary_service.AsyncSessionLocal", session_maker)
    monkeypatch.setenv("TESTING", "1")

    try:
        yield session_maker
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_get_vocabulary_level_counts_known_words(in_memory_session: async_sessionmaker[AsyncSession]) -> None:
    service = VocabularyService()

    async with in_memory_session() as session:
        user = User(
            email="user@example.com",
            username="user",
            hashed_password="hashed",
            is_active=True,
            is_superuser=False,
            is_verified=True,
        )
        word = VocabularyWord(
            word="Hund",
            lemma="Hund",
            language="de",
            difficulty_level="A1",
            translation_en="dog",
        )
        session.add_all([user, word])
        await session.flush()

        session.add(
            UserVocabularyProgress(
                user_id=user.id,
                vocabulary_id=word.id,
                lemma=word.lemma,
                language=word.language,
                is_known=True,
            )
        )
        await session.commit()
        user_id = user.id

    result = await service.get_vocabulary_level("A1", target_language="de", user_id=user_id, translation_language="en")

    assert result["level"] == "A1"
    assert result["known_count"] == 1
    assert len(result["words"]) == 1
    assert result["words"][0]["is_known"] is True


@pytest.mark.asyncio
async def test_get_vocabulary_level_normalizes_requested_level(
    in_memory_session: async_sessionmaker[AsyncSession],
) -> None:
    service = VocabularyService()

    async with in_memory_session() as session:
        word = VocabularyWord(
            word="Katze",
            lemma="Katze",
            language="de",
            difficulty_level="A1",
            translation_en="cat",
        )
        session.add(word)
        await session.commit()

    result = await service.get_vocabulary_level("a1", target_language="de")

    assert result["level"] == "A1"
    assert result["total_count"] == 1
    assert result["words"]
