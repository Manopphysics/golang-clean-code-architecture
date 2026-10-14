"""
Application configuration.

Mirrors Go's src/config/config.go — loads a .env file then allows
OS environment variables to override any value (pydantic-settings
handles this automatically, env vars always win).
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All application settings.

    Values are loaded in this priority order (highest wins):
      1. Actual OS environment variables
      2. .env file in the working directory
      3. Defaults defined here
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------ App
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    app_name: str = "Python Clean Architecture API"
    app_version: str = "1.0.0"

    # ----------------------------------------------------------- PostgreSQL
    postgres_db_name: str = "postgres"
    postgres_db_user: str = "postgres"
    postgres_db_password: str = "golang-first-api"
    postgres_db_host: str = "localhost"
    postgres_db_port: int = 5432

    # --------------------------------------------------------------- MongoDB
    mongodb_atlas_uri: str = (
        "mongodb://root:golang-first-api@127.0.0.1:27017/"
        "?authMechanism=SCRAM-SHA-1&authSource=admin"
    )
    mongodb_db_name: str = "golang_cleancode_example"

    # ------------------------------------------------------------------ JWT
    secret_key: str = "1234567890"
    jwt_access_expires: int = 86400    # seconds — 1 day
    jwt_refresh_expires: int = 172800  # seconds — 2 days

    # --------------------------------------------------------------- Helpers
    @property
    def postgres_dsn(self) -> str:
        """Async DSN for SQLAlchemy + asyncpg driver."""
        return (
            f"postgresql+asyncpg://{self.postgres_db_user}:{self.postgres_db_password}"
            f"@{self.postgres_db_host}:{self.postgres_db_port}/{self.postgres_db_name}"
        )

    @property
    def app_issuer(self) -> str:
        """JWT issuer — lowercased app name, matching Go's getIssuerName()."""
        return self.app_name.lower()


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings singleton.
    Use this everywhere instead of constructing Settings() directly,
    so config is only loaded once per process.
    """
    return Settings()
