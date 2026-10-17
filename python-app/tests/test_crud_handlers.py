"""Integration tests for CRUD HTTP handlers (mocked usecase + jwt_auth)."""
from datetime import UTC, datetime

import pytest

from src.domain.entities.user import UserEntity


def _user_entity() -> UserEntity:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    return UserEntity(
        id=1, email="test@example.com",
        first_name="Test", last_name="User",
        created_at=now, updated_at=now,
    )


# All CRUD routes require a valid JWT. In tests, mock_usecase.user_authentication
# returns a valid user by default (set in conftest).

AUTH = {"Authorization": "Bearer valid.token"}

# ---------------------------------------------------------------------------
# GET /api/v1/data/{slug}/describe
# ---------------------------------------------------------------------------

class TestDescribeDataSource:
    @pytest.mark.asyncio
    async def test_no_auth_returns_401(self, async_client):
        response = await async_client.get("/api/v1/data/users/describe")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_slug_returns_200(self, async_client, mock_usecase):
        mock_usecase.user_authentication.return_value = (_user_entity(), None)
        response = await async_client.get("/api/v1/data/users/describe", headers=AUTH)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_returns_schema_fields(self, async_client, mock_usecase):
        mock_usecase.user_authentication.return_value = (_user_entity(), None)
        response = await async_client.get("/api/v1/data/users/describe", headers=AUTH)
        data = response.json()
        assert "type" in data
        assert data["type"] == "record"

    @pytest.mark.asyncio
    async def test_usecase_error_returns_400(self, async_client, mock_usecase, mock_crud_usecase):
        mock_usecase.user_authentication.return_value = (_user_entity(), None)
        mock_crud_usecase.describe_data_source.side_effect = ValueError("slug not found")
        response = await async_client.get("/api/v1/data/bad-slug/describe", headers=AUTH)
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/v1/data/{slug}/
# ---------------------------------------------------------------------------

class TestRetrieveList:
    @pytest.mark.asyncio
    async def test_no_auth_returns_401(self, async_client):
        response = await async_client.get("/api/v1/data/users/")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_slug_returns_200(self, async_client, mock_usecase):
        mock_usecase.user_authentication.return_value = (_user_entity(), None)
        response = await async_client.get("/api/v1/data/users/", headers=AUTH)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_returns_pagination_fields(self, async_client, mock_usecase):
        mock_usecase.user_authentication.return_value = (_user_entity(), None)
        response = await async_client.get("/api/v1/data/users/", headers=AUTH)
        data = response.json()
        assert "data" in data
        assert "total_data" in data
        assert "page" in data

    @pytest.mark.asyncio
    async def test_page_and_page_size_params(self, async_client, mock_usecase, mock_crud_usecase):
        mock_usecase.user_authentication.return_value = (_user_entity(), None)
        await async_client.get(
            "/api/v1/data/users/?_page=2&_pageSize=5", headers=AUTH
        )
        mock_crud_usecase.retrieve_list.assert_awaited()
        call_kwargs = mock_crud_usecase.retrieve_list.call_args
        assert call_kwargs is not None

    @pytest.mark.asyncio
    async def test_bad_slug_returns_400(self, async_client, mock_usecase, mock_crud_usecase):
        mock_usecase.user_authentication.return_value = (_user_entity(), None)
        mock_crud_usecase.retrieve_list.side_effect = ValueError("slug not found")
        response = await async_client.get("/api/v1/data/nope/", headers=AUTH)
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/v1/data/{slug}/{id}
# ---------------------------------------------------------------------------

class TestRetrieve:
    @pytest.mark.asyncio
    async def test_no_auth_returns_401(self, async_client):
        response = await async_client.get("/api/v1/data/users/1")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_id_returns_200(self, async_client, mock_usecase):
        mock_usecase.user_authentication.return_value = (_user_entity(), None)
        response = await async_client.get("/api/v1/data/users/1", headers=AUTH)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_returns_data_field(self, async_client, mock_usecase):
        mock_usecase.user_authentication.return_value = (_user_entity(), None)
        response = await async_client.get("/api/v1/data/users/1", headers=AUTH)
        data = response.json()
        assert "data" in data

    @pytest.mark.asyncio
    async def test_not_found_returns_400(self, async_client, mock_usecase, mock_crud_usecase):
        mock_usecase.user_authentication.return_value = (_user_entity(), None)
        mock_crud_usecase.retrieve.side_effect = ValueError("record not found")
        response = await async_client.get("/api/v1/data/users/999", headers=AUTH)
        assert response.status_code == 400
        data = response.json()
        assert data["trace_id"] == "error"
