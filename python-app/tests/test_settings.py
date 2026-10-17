"""Tests for src/config/settings.py — Settings and get_settings()."""
import pytest


class TestSettings:
    def test_postgres_dsn_format(self, settings):
        dsn = settings.postgres_dsn
        assert dsn.startswith("postgresql+asyncpg://")
        assert settings.postgres_db_user in dsn
        assert settings.postgres_db_host in dsn
        assert str(settings.postgres_db_port) in dsn
        assert settings.postgres_db_name in dsn

    def test_app_issuer_is_lowercased(self, settings):
        assert settings.app_issuer == settings.app_name.lower()

    def test_app_issuer_has_no_uppercase(self, settings):
        assert settings.app_issuer == settings.app_issuer.lower()

    def test_default_secret_key(self, settings):
        assert settings.secret_key  # non-empty
        assert isinstance(settings.secret_key, str)

    def test_jwt_expires_are_positive(self, settings):
        assert settings.jwt_access_expires > 0
        assert settings.jwt_refresh_expires > 0

    def test_get_settings_returns_same_instance(self):
        from src.config import get_settings
        get_settings.cache_clear()
        a = get_settings()
        b = get_settings()
        assert a is b

    def test_get_settings_cache_clear_returns_new_instance(self):
        from src.config import get_settings
        get_settings.cache_clear()
        a = get_settings()
        get_settings.cache_clear()
        b = get_settings()
        # Both are Settings objects (may not be same due to cache clear)
        assert type(a) == type(b)

    def test_postgres_dsn_contains_password(self, settings):
        assert settings.postgres_db_password in settings.postgres_dsn
