"""
PostgreSQL implementation of ICRUDRepository.

Mirrors Go: src/interface/repositories/postgres/crud/crudRepository.go

Handles generic CRUD operations for any SQLAlchemy model registered
in the CRUD model registry.
"""
import math
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from src.domain.entities.crud import DataListResponse, DataResponse
from src.domain.repositories.crud import ICRUDRepository
from src.shared.crud.schema_generator import generate_avro_schema


class PostgresCRUDRepository(ICRUDRepository):
    """
    Concrete ICRUDRepository backed by PostgreSQL via SQLAlchemy async.
    A model_class is bound at construction time by the factory.
    Mirrors Go's postgresCRUDRepository struct.
    """

    def __init__(self, session: AsyncSession, model_class: type[DeclarativeBase]) -> None:
        self._session = session
        self._model = model_class

    # ------------------------------------------------------------------
    # ICRUDRepository — 7 methods
    # ------------------------------------------------------------------

    async def get_one_by_id(self, record_id: str) -> DataResponse:
        """
        Fetch a single record by primary key.
        Mirrors Go's GetOneById().
        """
        result = await self._session.execute(
            select(self._model).where(
                self._model.id == int(record_id)  # type: ignore[attr-defined]
            )
        )
        row = result.scalars().first()
        if row is None:
            raise ValueError(f"record '{record_id}' not found")

        return DataResponse(
            code=200,
            data=self._to_dict(row),
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
        Paginated list with LIMIT / OFFSET.
        Mirrors Go's GetList().
        page is 1-indexed.
        """
        page = max(1, page)
        page_size = min(max(1, page_size), 1000)
        offset = (page - 1) * page_size

        # Total count
        count_result = await self._session.execute(
            select(func.count()).select_from(self._model)
        )
        total_data = count_result.scalar() or 0
        total_page = math.ceil(total_data / page_size) if total_data else 1

        # Paginated rows — ordered by id for deterministic pagination
        rows_result = await self._session.execute(
            select(self._model).order_by(self._model.id).offset(offset).limit(page_size)
        )
        rows = rows_result.scalars().all()

        return DataListResponse(
            code=200,
            data=[self._to_dict(r) for r in rows],
            page=page,
            page_size=page_size,
            total_page=total_page,
            total_data=total_data,
            message="success",
            data_schema=self.describe_data_source(),
        )

    async def create(self, data: dict[str, Any]) -> DataResponse:
        """
        Insert a new record.
        Mirrors Go's Create().
        """
        instance = self._model(**data)
        self._session.add(instance)
        await self._session.flush()
        await self._session.refresh(instance)
        return DataResponse(
            code=201,
            data=self._to_dict(instance),
            message="created",
            data_schema=self.describe_data_source(),
        )

    async def update(self, record_id: str, data: dict[str, Any]) -> DataResponse:
        """
        Update an existing record by id.
        Mirrors Go's Update().
        """
        result = await self._session.execute(
            select(self._model).where(
                self._model.id == int(record_id)  # type: ignore[attr-defined]
            )
        )
        instance = result.scalars().first()
        if instance is None:
            raise ValueError(f"record '{record_id}' not found")

        for key, value in data.items():
            setattr(instance, key, value)

        await self._session.flush()
        await self._session.refresh(instance)
        return DataResponse(
            code=200,
            data=self._to_dict(instance),
            message="updated",
            data_schema=self.describe_data_source(),
        )

    async def upsert(
        self, filters: dict[str, Any], data: dict[str, Any]
    ) -> Any:
        """
        Insert or update based on filter criteria.
        Mirrors Go's UpSert() using FirstOrCreate pattern.
        """
        conditions = [
            getattr(self._model, k) == v for k, v in filters.items()
        ]
        result = await self._session.execute(
            select(self._model).where(*conditions)
        )
        instance = result.scalars().first()

        if instance:
            for key, value in data.items():
                setattr(instance, key, value)
        else:
            instance = self._model(**{**filters, **data})
            self._session.add(instance)

        await self._session.flush()
        return instance

    async def delete(self, record_id: str) -> None:
        """
        Delete a record by id.
        Mirrors Go's Delete().
        """
        result = await self._session.execute(
            select(self._model).where(
                self._model.id == int(record_id)  # type: ignore[attr-defined]
            )
        )
        instance = result.scalars().first()
        if instance:
            await self._session.delete(instance)
            await self._session.flush()

    def describe_data_source(self) -> dict[str, Any]:
        """
        Return Avro-like schema for this model.
        Mirrors Go's DescribeDataSource() using GenerateAvroSchema().
        """
        return generate_avro_schema(self._model)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_dict(instance: Any) -> dict[str, Any]:
        """Convert an ORM instance to a plain dict, skipping password."""
        from sqlalchemy import inspect as sa_inspect
        mapper = sa_inspect(type(instance))
        return {
            col.key: getattr(instance, col.key)
            for col in mapper.columns
            if col.key != "password"
        }
