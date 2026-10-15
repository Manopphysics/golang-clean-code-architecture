"""
PostgreSQL async connector.

Mirrors Go: src/infrastructure/database/postgres/connector.go

Uses SQLAlchemy 2.0 async engine with asyncpg driver.
The engine is a module-level singleton (created once on first import),
matching Go's pattern of a single connection pool per process.

Exposes:
  engine             — AsyncEngine singleton
  AsyncSessionLocal  — session factory
  get_session()      — FastAPI Depends() dependency
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import get_settings

_settings = get_settings()

# ---------------------------------------------------------------------------
# Engine — created once at module import (app startup)
# Mirrors Go's PostgresHandler() which opens a GORM DB connection.
# ---------------------------------------------------------------------------
engine = create_async_engine(
    _settings.postgres_dsn,
    echo=False,          # flip to True for SQL debug logging
    pool_pre_ping=True,  # test connections before use (avoids stale pool errors)
    pool_size=10,
    max_overflow=20,
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # keep ORM objects usable after commit
    autoflush=False,
    autocommit=False,
)


# ---------------------------------------------------------------------------
# FastAPI dependency — yields one session per request
# ---------------------------------------------------------------------------
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an AsyncSession scoped to the current request.
    Commits on success, rolls back on any exception.

    Usage:
        @router.get("/")
        async def handler(session: AsyncSession = Depends(get_session)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
