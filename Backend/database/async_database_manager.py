#!/usr/bin/env python3
"""
Async Database Manager with Connection Pooling using SQLAlchemy
Provides proper connection pooling and async operations for better performance
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine, async_sessionmaker
from sqlalchemy import text, pool
from sqlalchemy.pool import NullPool, QueuePool
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Tuple
import logging
from pathlib import Path
import aiosqlite
from datetime import datetime

class AsyncDatabaseManager:
    """Async database manager with proper connection pooling using SQLAlchemy"""
    
    def __init__(
        self, 
        db_path: str = "vocabulary.db",
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        enable_logging: bool = False
    ):
        """
        Initialize async database manager with connection pooling.
        
        Args:
            db_path: Path to SQLite database
            pool_size: Number of persistent connections
            max_overflow: Maximum overflow connections allowed
            pool_timeout: Timeout for getting connection from pool
            enable_logging: Enable SQL query logging
        """
        self.db_path = Path(db_path)
        self.enable_logging = enable_logging
        self.logger = logging.getLogger(__name__)
        
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create async engine with connection pooling
        self.engine: AsyncEngine = create_async_engine(
            f"sqlite+aiosqlite:///{self.db_path}",
            poolclass=QueuePool,  # Use queue pool for connection pooling
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_pre_ping=True,  # Verify connections before using
            echo=enable_logging,  # SQL logging
            connect_args={
                "check_same_thread": False,
                "timeout": 10
            }
        )
        
        # Create session factory
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def initialize(self):
        """Initialize database schema if needed"""
        async with self.engine.begin() as conn:
            # Enable foreign keys and WAL mode
            await conn.execute(text("PRAGMA foreign_keys = ON"))
            await conn.execute(text("PRAGMA journal_mode = WAL"))
            await conn.execute(text("PRAGMA synchronous = NORMAL"))
            
            # Check if schema exists
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            tables = {row[0] for row in result}
            
            if not tables or 'users' not in tables:
                await self._create_schema(conn)
    
    async def _create_schema(self, conn):
        """Create database schema"""
        # Add needs_password_migration column for bcrypt migration
        schema_updates = [
            """ALTER TABLE users ADD COLUMN IF NOT EXISTS needs_password_migration BOOLEAN DEFAULT 0""",
            """ALTER TABLE users ADD COLUMN IF NOT EXISTS native_language VARCHAR(10) DEFAULT 'en'""",
            """ALTER TABLE users ADD COLUMN IF NOT EXISTS target_language VARCHAR(10) DEFAULT 'de'"""
        ]
        
        for update in schema_updates:
            try:
                await conn.execute(text(update))
            except Exception:
                pass  # Column may already exist
    
    @asynccontextmanager
    async def get_session(self):
        """Get an async database session with automatic cleanup"""
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                self.logger.error(f"Database error: {e}")
                raise
            finally:
                await session.close()
    
    async def execute_query(self, query: str, params: dict = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dicts"""
        if self.enable_logging:
            self.logger.info(f"Executing query: {query} with params: {params}")
        
        async with self.get_session() as session:
            result = await session.execute(text(query), params or {})
            rows = result.fetchall()
            if rows and result.keys():
                return [dict(zip(result.keys(), row)) for row in rows]
            return []
    
    async def execute_update(self, query: str, params: dict = None) -> int:
        """Execute an UPDATE/DELETE query and return affected rows"""
        if self.enable_logging:
            self.logger.info(f"Executing update: {query} with params: {params}")
        
        async with self.get_session() as session:
            result = await session.execute(text(query), params or {})
            await session.commit()
            return result.rowcount
    
    async def execute_insert(self, query: str, params: dict = None) -> int:
        """Execute an INSERT query and return last row ID"""
        if self.enable_logging:
            self.logger.info(f"Executing insert: {query} with params: {params}")
        
        async with self.get_session() as session:
            result = await session.execute(text(query), params or {})
            await session.commit()
            return result.lastrowid
    
    async def execute_many(self, query: str, params_list: List[dict]) -> int:
        """Execute a query with multiple parameter sets"""
        if self.enable_logging:
            self.logger.info(f"Executing batch: {query} with {len(params_list)} parameter sets")
        
        async with self.get_session() as session:
            for params in params_list:
                await session.execute(text(query), params)
            await session.commit()
            return len(params_list)
    
    async def close(self):
        """Close all database connections"""
        await self.engine.dispose()
    
    async def get_pool_status(self) -> Dict[str, Any]:
        """Get connection pool status"""
        pool = self.engine.pool
        return {
            "size": pool.size() if hasattr(pool, 'size') else 0,
            "overflow": pool.overflow() if hasattr(pool, 'overflow') else 0,
            "checked_in": pool.checkedin() if hasattr(pool, 'checkedin') else 0,
            "checked_out": pool.checkedout() if hasattr(pool, 'checkedout') else 0,
            "total": pool.total() if hasattr(pool, 'total') else 0
        }
    
    async def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            async with self.get_session() as session:
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False


class DatabaseManagerAdapter:
    """
    Adapter to make AsyncDatabaseManager compatible with existing sync code
    This allows gradual migration from sync to async
    """
    
    def __init__(self, async_manager: AsyncDatabaseManager):
        self.async_manager = async_manager
        self._loop = None
    
    def _ensure_loop(self):
        """Ensure we have an event loop for sync-to-async bridge"""
        import asyncio
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Sync wrapper for async execute_query"""
        self._ensure_loop()
        import asyncio
        
        # Convert positional params to dict for SQLAlchemy
        param_dict = {f"param{i}": v for i, v in enumerate(params)}
        # Update query to use named parameters
        for i in range(len(params)):
            query = query.replace("?", f":param{i}", 1)
        
        if self._loop.is_running():
            # If loop is already running, schedule coroutine
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.async_manager.execute_query(query, param_dict)
                )
                return future.result()
        else:
            return self._loop.run_until_complete(
                self.async_manager.execute_query(query, param_dict)
            )
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Sync wrapper for async execute_update"""
        self._ensure_loop()
        import asyncio
        
        # Convert positional params to dict
        param_dict = {f"param{i}": v for i, v in enumerate(params)}
        for i in range(len(params)):
            query = query.replace("?", f":param{i}", 1)
        
        if self._loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.async_manager.execute_update(query, param_dict)
                )
                return future.result()
        else:
            return self._loop.run_until_complete(
                self.async_manager.execute_update(query, param_dict)
            )
    
    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """Sync wrapper for async execute_insert"""
        self._ensure_loop()
        import asyncio
        
        # Convert positional params to dict
        param_dict = {f"param{i}": v for i, v in enumerate(params)}
        for i in range(len(params)):
            query = query.replace("?", f":param{i}", 1)
        
        if self._loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.async_manager.execute_insert(query, param_dict)
                )
                return future.result()
        else:
            return self._loop.run_until_complete(
                self.async_manager.execute_insert(query, param_dict)
            )
    
    @contextmanager
    def get_connection(self):
        """Compatibility method - returns self as connection-like object"""
        from contextlib import contextmanager
        yield self
    
    @contextmanager
    def transaction(self):
        """Compatibility method for transaction context"""
        from contextlib import contextmanager
        yield self