"""Focused behavior tests for the async `BaseRepository`."""
from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase

from services.repository.base_repository import BaseRepository


class Base(DeclarativeBase):
    pass


class DummyModel(Base):
    __tablename__ = 'dummy'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50))

    def __init__(self, id: int | None = None, name: str = "") -> None:
        self.id = id
        self.name = name


class DummyRepository(BaseRepository[DummyModel]):
    @property
    def table_name(self) -> str:
        return "dummy"

    @property
    def model_class(self):
        return DummyModel


@pytest.fixture
def session_double():
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = AsyncMock()
    session.merge = AsyncMock()
    return session


@pytest.fixture
def repository(session_double):
    repo = DummyRepository()

    @asynccontextmanager
    async def fake_session():
        yield session_double

    repo.get_session = fake_session  # type: ignore[assignment]
    repo.transaction = fake_session  # type: ignore[assignment]
    return repo


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenfind_by_idCalled_ThenReturnsmodel(repository, session_double):
    """Happy path: repository surfaces the ORM entity returned by SQLAlchemy."""
    expected = DummyModel(id=5, name="item")
    
    # Create a mock result that behaves like SQLAlchemy result
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = expected
    session_double.execute.return_value = result_mock

    result = await repository.find_by_id(5)

    assert result is expected
    session_double.execute.assert_called()


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenfind_by_id_propagates_errorsCalled_ThenSucceeds(repository, session_double):
    """Invalid scenario: database errors bubble up for caller handling."""
    session_double.execute.side_effect = RuntimeError("db down")

    with pytest.raises(RuntimeError):
        await repository.find_by_id(1)


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whensave_inserts_new_entityCalled_ThenSucceeds(repository, session_double):
    """Happy path: saving a new entity adds it and flushes for an ID."""
    entity = DummyModel(name="new")

    await repository.save(entity)

    session_double.add.assert_called_once_with(entity)
    session_double.flush.assert_called_once()


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhensaveCalled_ThenUpdatesexisting_entity(repository, session_double):
    """Boundary: entities with IDs should be merged instead of inserted."""
    entity = DummyModel(id=10, name="existing")
    session_double.merge.return_value = entity

    await repository.save(entity)

    session_double.merge.assert_called_once_with(entity)
    session_double.add.assert_not_called()


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whendelete_by_idCalled_ThenReturnsboolean(repository, session_double):
    """Happy/boundary: delete returns True when rows were affected, otherwise False."""
    # Create a mock result with rowcount
    delete_result = MagicMock()
    delete_result.rowcount = 1
    session_double.execute.return_value = delete_result

    assert await repository.delete_by_id(1) is True

    delete_result.rowcount = 0
    assert await repository.delete_by_id(2) is False


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whencount_with_criteria_filtersCalled_ThenSucceeds(repository, session_double):
    """Boundary: count forwards criteria to SQLAlchemy query builder."""
    # Create a mock result for scalar
    result_mock = MagicMock()
    result_mock.scalar.return_value = 3
    session_double.execute.return_value = result_mock

    total = await repository.count({"name": "foo"})

    assert total == 3
    session_double.execute.assert_called()
