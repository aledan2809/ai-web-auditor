"""
Database connection and session management
"""

import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/auditor.db")

# Convert postgres:// to postgresql+asyncpg:// for async support
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

_is_sqlite = DATABASE_URL.startswith("sqlite")

# Engine kwargs based on backend
_engine_kwargs = {
    "echo": os.getenv("DEBUG", "false").lower() == "true",
    "future": True,
    "pool_pre_ping": True,
}

if _is_sqlite:
    # Use NullPool for SQLite so each session gets its own connection.
    # StaticPool shares a single connection which causes the background task
    # and HTTP requests to interfere with each other's transactions.
    _engine_kwargs["poolclass"] = NullPool
else:
    # PostgreSQL: proper connection pool
    _engine_kwargs["pool_size"] = 5
    _engine_kwargs["max_overflow"] = 10
    _engine_kwargs["pool_recycle"] = 300

# Create async engine
engine = create_async_engine(DATABASE_URL, **_engine_kwargs)

# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Base class for models
Base = declarative_base()


async def get_db():
    """Dependency for getting database session.

    Yields a session, then commits on success or rolls back on error.
    Routes that call db.commit() explicitly are fine — the final commit
    here is a no-op when nothing is pending.
    """
    session = async_session()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Enable WAL mode for SQLite — allows concurrent readers + single writer
        if _is_sqlite:
            await conn.execute(text("PRAGMA journal_mode=WAL"))
            await conn.execute(text("PRAGMA busy_timeout=5000"))
            logger.info("SQLite WAL mode enabled")


async def close_db():
    """Close database connection"""
    await engine.dispose()
