"""
MongoDB implementation of ICRUDRepository.

Mirrors Go: src/interface/repositories/mongodb/crud/crudRepository.go

Uses Motor (async MongoDB driver). The collection name comes from
the model's __tablename__ attribute, matching Go's TableName().
"""
import math
from datetime import UTC
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection

from src.domain.entities.crud import DataListResponse, DataResponse
from src.domain.repositories.crud import ICRUDRepository
from src.shared.crud.schema_generator import generate_avro_schema


class MongoDBCRUDRepository(ICRUDRepository):
    """
    Concrete ICRUDRepository backed by MongoDB via Motor async.
    A collection and model_class are bound at construction time by the factory.
    Mirrors Go's mongodbCRUDRepository struct.
    """

    def __init__(
        self,
        collection: AsyncIOMotorCollection,  # type: ignore[type-arg]
        model_class: Any,
    ) -> None:
        self._collection = collection
        self._model = model_class

    # ------------------------------------------------------------------
    # ICRUDRepository — 7 methods
    # ------------------------------------------------------------------

    async def get_one_by_id(self, record_id: str) -> DataResponse:
        """
        Fetch a single document by ObjectId.
        Mirrors Go's GetOneById() using primitive.ObjectIDFromHex.
        """
        try:
            oid = ObjectId(record_id)
        except InvalidId as exc:
            raise ValueError(f"invalid id format: '{record_id}'") from exc

        doc = await self._collection.find_one({"_id": oid})
        if doc is None:
            raise ValueError(f"document '{record_id}' not found")

        return DataResponse(
            code=200,
            data=self._serialize(doc),
            message="success",
            data_schema=self.describe_data_source(),
        )

    async def get_list(
        self,
        page: int,
        page_size: int,
        filters: dict[str, Any] | None = None,
    ) -> DataListResponse:
        """
        Paginated list sorted by _id ascending.
        Mirrors Go's GetList() with sort, skip, limit, and CountDocuments.
        """
        page = max(1, page)
        page_size = min(max(1, page_size), 1000)
        skip = (page - 1) * page_size
        query = filters or {}

        total_data = await self._collection.count_documents(query)
        total_page = math.ceil(total_data / page_size) if total_data else 1

        cursor = (
            self._collection.find(query)
            .sort("_id", 1)
            .skip(skip)
            .limit(page_size)
        )
        docs = await cursor.to_list(length=page_size)

        return DataListResponse(
            code=200,
            data=[self._serialize(d) for d in docs],
            page=page,
            page_size=page_size,
            total_page=total_page,
            total_data=total_data,
            message="success",
            data_schema=self.describe_data_source(),
        )

    async def create(self, data: dict[str, Any]) -> DataResponse:
        """Insert a new document. Mirrors Go's Create() (stub → now implemented)."""
        result = await self._collection.insert_one(data)
        doc = await self._collection.find_one({"_id": result.inserted_id})
        return DataResponse(
            code=201,
            data=self._serialize(doc),
            message="created",
            data_schema=self.describe_data_source(),
        )

    async def update(self, record_id: str, data: dict[str, Any]) -> DataResponse:
        """Update a document by ObjectId. Mirrors Go's Update() (stub → now implemented)."""
        try:
            oid = ObjectId(record_id)
        except InvalidId as exc:
            raise ValueError(f"invalid id format: '{record_id}'") from exc

        await self._collection.update_one({"_id": oid}, {"$set": data})
        doc = await self._collection.find_one({"_id": oid})
        if doc is None:
            raise ValueError(f"document '{record_id}' not found")
        return DataResponse(
            code=200,
            data=self._serialize(doc),
            message="updated",
            data_schema=self.describe_data_source(),
        )

    async def upsert(
        self, filters: dict[str, Any], data: dict[str, Any]
    ) -> Any:
        """
        Upsert using $set + $setOnInsert.
        Mirrors Go's UpSert() with FindOneAndUpdate + upsert:true.
        """
        from datetime import datetime
        result = await self._collection.find_one_and_update(
            filters,
            {
                "$set": data,
                "$currentDate": {"updated_at": True},
                "$setOnInsert": {"created_at": datetime.now(tz=UTC)},
            },
            upsert=True,
            return_document=True,
        )
        return self._serialize(result) if result else None

    async def delete(self, record_id: str) -> None:
        """Delete a document by ObjectId. Mirrors Go's Delete() (stub → now implemented)."""
        try:
            oid = ObjectId(record_id)
        except InvalidId as exc:
            raise ValueError(f"invalid id format: '{record_id}'") from exc
        await self._collection.delete_one({"_id": oid})

    def describe_data_source(self) -> dict[str, Any]:
        """
        Return Avro-like schema for the bound model.
        Mirrors Go's DescribeDataSource().
        """
        return generate_avro_schema(self._model)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _serialize(doc: dict[str, Any] | None) -> dict[str, Any]:
        """Convert MongoDB doc to JSON-serialisable dict (_id → str)."""
        if not doc:
            return {}
        result = dict(doc)
        if "_id" in result:
            result["_id"] = str(result["_id"])
        return result
