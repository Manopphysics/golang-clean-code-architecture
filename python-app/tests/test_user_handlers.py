"""Integration tests for user HTTP handlers (mocked usecase)."""
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from src.domain.entities.user import UserEntity, UserLoginResponse, UserTokenEntity


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user_entity() -> UserEntity:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    return UserEntity(
        id=1, email="test@example.com",
        first_name="Test", last_name="User",
        created_at=now, updated_at=now,
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_returns_200(self, async_client):
        response = await async_client.get("/api/v1/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_returns_name_and_version(self, async_client):
        response = await async_client.get("/api/v1/")
        data = response.json()
        assert "name" in data
        assert "version" in data


# ---------------------------------------------------------------------------
# POST /api/v1/users/register
# ---------------------------------------------------------------------------

class TestRegisterUser:
    @pytest.mark.asyncio
    async def test_success_returns_201(self, async_client, mock_usecase):
        mock_usecase.register_user.return_value = _user_entity()
        response = await async_client.post(
            "/api/v1/users/register",
            json={
                "email": "new@example.com",
                "password": "pass123",
                "first_name": "New",
                "last_name": "User",
            },
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_success_returns_user_fields(self, async_client, mock_usecase):
        mock_usecase.register_user.return_value = _user_entity()
        response = await async_client.post(
            "/api/v1/users/register",
            json={
                "email": "new@example.com",
                "password": "pass",
                "first_name": "A",
                "last_name": "B",
            },
        )
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "password" not in data

    @pytest.mark.asyncio
    async def test_invalid_email_returns_422(self, async_client):
        response = await async_client.post(
            "/api/v1/users/register",
            json={
                "email": "not-an-email",
                "password": "pass",
                "first_name": "A",
                "last_name": "B",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_usecase_error_returns_400(self, async_client, mock_usecase):
        mock_usecase.register_user.side_effect = ValueError("duplicate email")
        response = await async_client.post(
            "/api/v1/users/register",
            json={
                "email": "a@b.com",
                "password": "pass",
                "first_name": "A",
                "last_name": "B",
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert data["trace_id"] == "users-001"

    @pytest.mark.asyncio
    async def test_missing_field_returns_422(self, async_client):
        response = await async_client.post(
            "/api/v1/users/register",
            json={"email": "a@b.com"},  # missing password, names
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/v1/users/login
# ---------------------------------------------------------------------------

class TestUserLogin:
    @pytest.mark.asyncio
    async def test_success_returns_200(self, async_client, mock_usecase):
        response = await async_client.post(
            "/api/v1/users/login",
            json={"email": "test@example.com", "password": "pass"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_success_returns_token(self, async_client, mock_usecase):
        response = await async_client.post(
            "/api/v1/users/login",
            json={"email": "test@example.com", "password": "pass"},
        )
        data = response.json()
        assert "token" in data
        assert "access" in data["token"]
        assert "refresh" in data["token"]

    @pytest.mark.asyncio
    async def test_usecase_error_returns_400(self, async_client, mock_usecase):
        mock_usecase.user_login.side_effect = ValueError("password is invalid")
        response = await async_client.post(
            "/api/v1/users/login",
            json={"email": "test@example.com", "password": "wrong"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["trace_id"] == "users-002"
        assert "password is invalid" in data["message"]


# ---------------------------------------------------------------------------
# POST /api/v1/users/logout
# ---------------------------------------------------------------------------

class TestUserLogout:
    @pytest.mark.asyncio
    async def test_success_returns_200(self, async_client, mock_usecase):
        mock_usecase.user_logout.return_value = None
        response = await async_client.post(
            "/api/v1/users/logout",
            json={"refresh_token": "some.token"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_usecase_error_returns_400(self, async_client, mock_usecase):
        mock_usecase.user_logout.side_effect = ValueError("user token not found")
        response = await async_client.post(
            "/api/v1/users/logout",
            json={"refresh_token": "bad.token"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["trace_id"] == "users-004"


# ---------------------------------------------------------------------------
# POST /api/v1/users/refresh-token
# ---------------------------------------------------------------------------

class TestRefreshToken:
    @pytest.mark.asyncio
    async def test_success_returns_200(self, async_client, mock_usecase):
        response = await async_client.post(
            "/api/v1/users/refresh-token",
            json={"refresh_token": "some.token"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_success_returns_new_tokens(self, async_client, mock_usecase):
        response = await async_client.post(
            "/api/v1/users/refresh-token",
            json={"refresh_token": "some.token"},
        )
        data = response.json()
        assert "token" in data
        assert data["token"]["access"] == "new.acc"

    @pytest.mark.asyncio
    async def test_expired_token_returns_400(self, async_client, mock_usecase):
        mock_usecase.user_refresh_token.side_effect = ValueError("token had expired")
        response = await async_client.post(
            "/api/v1/users/refresh-token",
            json={"refresh_token": "expired.token"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["trace_id"] == "users-003"


# ---------------------------------------------------------------------------
# GET /api/v1/users/profile
# ---------------------------------------------------------------------------

class TestGetUserProfile:
    @pytest.mark.asyncio
    async def test_no_auth_header_returns_401(self, async_client):
        response = await async_client.get("/api/v1/users/profile")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_token_returns_200(self, async_client, mock_usecase):
        mock_usecase.user_authentication.return_value = (_user_entity(), None)
        response = await async_client.get(
            "/api/v1/users/profile",
            headers={"Authorization": "Bearer valid.token.here"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_valid_token_returns_user_data(self, async_client, mock_usecase):
        mock_usecase.user_authentication.return_value = (_user_entity(), None)
        response = await async_client.get(
            "/api/v1/users/profile",
            headers={"Authorization": "Bearer valid.token.here"},
        )
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "password" not in data

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self, async_client, mock_usecase):
        mock_usecase.user_authentication.side_effect = ValueError("user token not found")
        response = await async_client.get(
            "/api/v1/users/profile",
            headers={"Authorization": "Bearer bad.token"},
        )
        assert response.status_code == 401
        # FastAPI wraps HTTPException detail under the "detail" key
        data = response.json()
        assert data["detail"]["trace_id"] == "middleware-002"
