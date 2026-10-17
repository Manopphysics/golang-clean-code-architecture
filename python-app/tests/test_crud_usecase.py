"""Tests for src/usecases/crud_usecase.py."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities.crud import DataListResponse, DataResponse
from src.usecases.crud_usecase import CrudUsecase


def _make_data_response() -> DataResponse:
    return DataResponse(
        code=200, data={"id": 1}, message="success",
        data_schema={"type": "record", "name": "users", "fields": []},
    )


def _make_list_response() -> DataListResponse:
    return DataListResponse(
        code=200, data=[{"id": 1}], page=1, page_size=10,
        total_page=1, total_data=1, message="success",
        data_schema=None,
    )


class TestCrudUsecaseRetrieve:
    @pytest.mark.asyncio
    async def test_happy_path_returns_data_response(self):
        mock_repo = AsyncMock()
        mock_repo.get_one_by_id.return_value = _make_data_response()

        with patch(
            "src.usecases.crud_usecase.get_crud_repository",
            return_value=mock_repo,
        ):
            usecase = CrudUsecase()
            session = MagicMock()
            result = await usecase.retrieve(None, "users", "1", session)

        assert result.code == 200
        mock_repo.get_one_by_id.assert_awaited_once_with("1")

    @pytest.mark.asyncio
    async def test_unknown_slug_raises(self):
        with patch(
            "src.usecases.crud_usecase.get_crud_repository",
            side_effect=ValueError("slug not found"),
        ):
            usecase = CrudUsecase()
            with pytest.raises(ValueError, match="slug not found"):
                await usecase.retrieve(None, "bad-slug", "1", MagicMock())

    @pytest.mark.asyncio
    async def test_record_not_found_propagates(self):
        mock_repo = AsyncMock()
        mock_repo.get_one_by_id.side_effect = ValueError("record not found")

        with patch(
            "src.usecases.crud_usecase.get_crud_repository",
            return_value=mock_repo,
        ):
            usecase = CrudUsecase()
            with pytest.raises(ValueError, match="record not found"):
                await usecase.retrieve(None, "users", "999", MagicMock())


class TestCrudUsecaseRetrieveList:
    @pytest.mark.asyncio
    async def test_happy_path_returns_list_response(self):
        mock_repo = AsyncMock()
        mock_repo.get_list.return_value = _make_list_response()

        with patch(
            "src.usecases.crud_usecase.get_crud_repository",
            return_value=mock_repo,
        ):
            usecase = CrudUsecase()
            result = await usecase.retrieve_list(None, "users", 1, 10, None, MagicMock())

        assert result.page == 1
        assert result.total_data == 1

    @pytest.mark.asyncio
    async def test_passes_filters_to_repo(self):
        mock_repo = AsyncMock()
        mock_repo.get_list.return_value = _make_list_response()
        filters = {"email": "a@b.com"}

        with patch(
            "src.usecases.crud_usecase.get_crud_repository",
            return_value=mock_repo,
        ):
            usecase = CrudUsecase()
            await usecase.retrieve_list(None, "users", 2, 5, filters, MagicMock())

        mock_repo.get_list.assert_awaited_once_with(2, 5, filters)

    @pytest.mark.asyncio
    async def test_unknown_slug_raises(self):
        with patch(
            "src.usecases.crud_usecase.get_crud_repository",
            side_effect=ValueError("slug not found"),
        ):
            usecase = CrudUsecase()
            with pytest.raises(ValueError):
                await usecase.retrieve_list(None, "x", 1, 10, None, MagicMock())


class TestCrudUsecaseDescribeDataSource:
    @pytest.mark.asyncio
    async def test_happy_path_returns_schema(self):
        mock_repo = MagicMock()
        mock_repo.describe_data_source.return_value = {
            "type": "record", "name": "users", "fields": []
        }

        with patch(
            "src.usecases.crud_usecase.get_crud_repository",
            return_value=mock_repo,
        ):
            usecase = CrudUsecase()
            result = await usecase.describe_data_source("users", MagicMock())

        assert result["type"] == "record"
        assert result["name"] == "users"

    @pytest.mark.asyncio
    async def test_unknown_slug_raises(self):
        with patch(
            "src.usecases.crud_usecase.get_crud_repository",
            side_effect=ValueError("not found"),
        ):
            usecase = CrudUsecase()
            with pytest.raises(ValueError):
                await usecase.describe_data_source("bad", MagicMock())
