"""Unit tests for MongoDBCRUDRepository (mocked Motor collection)."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId

from src.domain.models.user import UserModel
from src.interface.repositories.mongodb.crud_repository import MongoDBCRUDRepository


def _make_repo(collection=None):
    if collection is None:
        collection = AsyncMock()
    return MongoDBCRUDRepository(collection=collection, model_class=UserModel)


class TestMongoDBSerialize:
    def test_converts_object_id_to_string(self):
        oid = ObjectId()
        doc = {"_id": oid, "name": "test"}
        result = MongoDBCRUDRepository._serialize(doc)
        assert isinstance(result["_id"], str)
        assert result["_id"] == str(oid)

    def test_preserves_other_fields(self):
        doc = {"_id": ObjectId(), "email": "a@b.com", "count": 42}
        result = MongoDBCRUDRepository._serialize(doc)
        assert result["email"] == "a@b.com"
        assert result["count"] == 42

    def test_empty_doc_returns_empty_dict(self):
        result = MongoDBCRUDRepository._serialize(None)
        assert result == {}

    def test_doc_without_id_passes_through(self):
        doc = {"name": "no_id"}
        result = MongoDBCRUDRepository._serialize(doc)
        assert result == {"name": "no_id"}


class TestMongoDBGetOneById:
    @pytest.mark.asyncio
    async def test_invalid_object_id_raises(self):
        repo = _make_repo()
        with pytest.raises(ValueError, match="invalid id format"):
            await repo.get_one_by_id("not-a-valid-objectid")

    @pytest.mark.asyncio
    async def test_document_not_found_raises(self):
        collection = AsyncMock()
        collection.find_one.return_value = None
        repo = _make_repo(collection)
        oid = str(ObjectId())
        with pytest.raises(ValueError, match="not found"):
            await repo.get_one_by_id(oid)

    @pytest.mark.asyncio
    async def test_returns_data_response_on_success(self):
        oid = ObjectId()
        doc = {"_id": oid, "email": "a@b.com"}
        collection = AsyncMock()
        collection.find_one.return_value = doc
        repo = _make_repo(collection)

        result = await repo.get_one_by_id(str(oid))
        assert result.code == 200
        assert result.data["email"] == "a@b.com"
        assert result.data["_id"] == str(oid)


class TestMongoDBGetList:
    def _make_cursor_mock(self, docs):
        cursor_mock = MagicMock()
        cursor_mock.sort.return_value = cursor_mock
        cursor_mock.skip.return_value = cursor_mock
        cursor_mock.limit.return_value = cursor_mock
        cursor_mock.to_list = AsyncMock(return_value=docs)
        return cursor_mock

    @pytest.mark.asyncio
    async def test_returns_data_list_response(self):
        oid = ObjectId()
        collection = MagicMock()
        collection.count_documents = AsyncMock(return_value=1)
        collection.find.return_value = self._make_cursor_mock([{"_id": oid, "email": "a@b.com"}])

        repo = _make_repo(collection)
        result = await repo.get_list(1, 10)

        assert result.code == 200
        assert result.total_data == 1
        assert result.page == 1
        assert len(result.data) == 1

    @pytest.mark.asyncio
    async def test_page_clamped_to_minimum_1(self):
        collection = MagicMock()
        collection.count_documents = AsyncMock(return_value=0)
        collection.find.return_value = self._make_cursor_mock([])

        repo = _make_repo(collection)
        result = await repo.get_list(0, 10)
        assert result.page == 1

    @pytest.mark.asyncio
    async def test_page_size_clamped_to_1000(self):
        collection = MagicMock()
        collection.count_documents = AsyncMock(return_value=0)
        collection.find.return_value = self._make_cursor_mock([])

        repo = _make_repo(collection)
        result = await repo.get_list(1, 9999)
        assert result.page_size == 1000


class TestMongoDBDescribeDataSource:
    def test_returns_avro_schema(self):
        repo = _make_repo()
        schema = repo.describe_data_source()
        assert schema["type"] == "record"
        assert "fields" in schema


class TestMongoDBDelete:
    @pytest.mark.asyncio
    async def test_invalid_object_id_raises(self):
        repo = _make_repo()
        with pytest.raises(ValueError, match="invalid id format"):
            await repo.delete("bad-id")

    @pytest.mark.asyncio
    async def test_valid_id_calls_delete_one(self):
        collection = AsyncMock()
        repo = _make_repo(collection)
        oid = str(ObjectId())
        await repo.delete(oid)
        collection.delete_one.assert_awaited_once()
