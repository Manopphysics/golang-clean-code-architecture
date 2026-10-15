"""
Alembic migration environment.

Mirrors Go: src/infrastructure/database/postgres/migration/main.go
That binary runs GORM AutoMigrate on every registered model.
Here we use Alembic with --autogenerate to produce explicit, reviewable
migration files instead.

Usage:
    cd python-app

    # Apply all pending migrations
    alembic upgrade head

    # Generate a new revision after model changes
    alembic revision --autogenerate -m "describe the change"

    # Downgrade one step
    alembic downgrade -1
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from src.config import get_settings

# ---------------------------------------------------------------------------
# Import all models so Alembic detects them via Base.metadata.
# Every new model must be imported here (or imported by something here).
# ---------------------------------------------------------------------------
from src.domain.models.user import Base  # noqa: F401

# ---------------------------------------------------------------------------
# Alembic config object (reads alembic.ini)
# ---------------------------------------------------------------------------
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Point Alembic at our SQLAlchemy metadata for --autogenerate support
target_metadata = Base.metadata

# Override the URL from pydantic-settings so credentials never sit in alembic.ini
_settings = get_settings()
config.set_main_option("sqlalchemy.url", _settings.postgres_dsn)


# ---------------------------------------------------------------------------
# Offline mode — generates SQL script without a live DB connection
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online mode — runs migrations against a live DB connection (standard)
# ---------------------------------------------------------------------------
def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
