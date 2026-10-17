"""
Shared pytest fixtures.

Provides:
  - Overridden Settings with test values (no .env file, fast JWT)
  - A test FastAPI app with dependency overrides
  - An httpx.AsyncClient for API integration tests
  - Helper factories for domain objects
"""
import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

# Patch settings BEFORE any app code is imported so modules that call
# get_settings() at import time (e.g. jwt.py) pick up the test values.
os.environ.setdefault("APP_NAME", "Test App")
os.environ.setdefault("APP_VERSION", "0.0.1-test")
os.environ.setdefault("SECRET_KEY", "testsecret1234567890")
os.environ.setdefault("JWT_ACCESS_EXPIRES", "3600")
os.environ.setdefault("JWT_REFRESH_EXPIRES", "7200")
os.environ.setdefault("POSTGRES_DB_HOST", "localhost")
os.environ.setdefault("MONGODB_ATLAS_URI", "mongodb://localhost:27017")


# ---------------------------------------------------------------------------
# Settings fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def settings():
    """Return a fresh Settings instance with test values, bypassing .env."""
    from src.config import get_settings
    get_settings.cache_clear()
    s = get_settings()
    yield s
    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Domain object factories
# ---------------------------------------------------------------------------

@pytest.fixture()
def user_entity():
    from src.domain.entities.user import UserEntity
    return UserEntity(
        id=1,
        email="test@example.com",
        first_name="Test",
        last_name="User",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


@pytest.fixture()
def user_model():
    """A UserModel ORM instance (not saved to DB)."""
    from src.domain.models.user import UserModel
    m = UserModel(
        id=1,
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password="$2b$10$hashed",
    )
    m.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    m.updated_at = datetime(2026, 1, 1, tzinfo=UTC)
    return m


@pytest.fixture()
def user_token_model(user_model):
    from src.domain.models.user import UserTokenModel
    tok = UserTokenModel(
        id=1,
        user_id=1,
        access="access.token.here",
        refresh="refresh.token.here",
    )
    tok.updated_at = datetime(2026, 1, 1, tzinfo=UTC)
    tok.user = user_model
    return tok


# ---------------------------------------------------------------------------
# Mock repository
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_user_repo():
    """AsyncMock implementation of IUserRepository."""
    repo = AsyncMock()
    return repo


# ---------------------------------------------------------------------------
# FastAPI test app + AsyncClient
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_usecase(user_entity, user_token_model):
    """A mock IUserUsecase with sensible defaults for handler tests."""
    from src.domain.entities.user import UserLoginResponse, UserTokenEntity
    uc = AsyncMock()
    uc.register_user.return_value = user_entity
    uc.user_login.return_value = UserLoginResponse(
        user=user_entity,
        token=UserTokenEntity(access="acc.tok", refresh="ref.tok"),
    )
    uc.user_logout.return_value = None
    uc.user_refresh_token.return_value = UserLoginResponse(
        user=user_entity,
        token=UserTokenEntity(access="new.acc", refresh="new.ref"),
    )
    uc.user_authentication.return_value = (user_entity, None)
    uc.get_user_profile.return_value = user_entity
    return uc


@pytest.fixture()
def mock_crud_usecase():
    """A mock ICRUDUsecase."""
    from src.domain.entities.crud import DataListResponse, DataResponse
    uc = AsyncMock()
    uc.retrieve.return_value = DataResponse(
        code=200, data={"id": 1}, message="success",
        data_schema={"type": "record", "name": "users", "fields": []},
    )
    uc.retrieve_list.return_value = DataListResponse(
        code=200, data=[{"id": 1}], page=1, page_size=10,
        total_page=1, total_data=1, message="success",
        data_schema={"type": "record", "name": "users", "fields": []},
    )
    uc.describe_data_source.return_value = {
        "type": "record", "name": "users", "fields": []
    }
    return uc


@pytest.fixture()
async def async_client(mock_usecase, mock_crud_usecase):
    """
    Async HTTP client wired against the real FastAPI app with
    all DB/usecase dependencies overridden by mocks.
    """
    from main import app
    from src.infrastructure.server.dependencies import (
        get_crud_usecase,
        get_user_usecase,
    )

    app.dependency_overrides[get_user_usecase] = lambda: mock_usecase
    app.dependency_overrides[get_crud_usecase] = lambda: mock_crud_usecase

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()
