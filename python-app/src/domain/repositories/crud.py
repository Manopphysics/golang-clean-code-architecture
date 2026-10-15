"""
ICRUDRepository — abstract repository interface (port).

Mirrors Go: src/domain/repositories/crud.go

Concrete implementations (added in PR-05):
  src/interface/repositories/postgres/crud_repository.py  — PostgreSQL
  src/interface/repositories/mongodb/crud_repository.py   — MongoDB
"""
from abc import ABC, abstractmethod
from typing import Any

from src.domain.entities.crud import DataListResponse, DataResponse


class ICRUDRepository(ABC):
    """
    Port for generic CRUD operations on any registered model.
    The slug passed to the factory selects which model/table to target.
    Mirrors Go's ICRUDRepository.
    """

    @abstractmethod
    async def get_one_by_id(self, record_id: str) -> DataResponse:
        """
        Fetch a single record by its primary key.
        Mirrors Go's GetOneById().
        """
        ...

    @abstractmethod
    async def get_list(
        self,
        page: int,
        page_size: int,
        filters: dict[str, Any] | None = None,
    ) -> DataListResponse:
        """
        Fetch a paginated list of records.
        page is 1-indexed; page_size defaults to 10 (max 1000).
        Mirrors Go's GetList().
        """
        ...

    @abstractmethod
    async def create(self, data: dict[str, Any]) -> DataResponse:
        """
        Insert a new record.
        Mirrors Go's Create().
        """
        ...

    @abstractmethod
    async def update(self, record_id: str, data: dict[str, Any]) -> DataResponse:
        """
        Update an existing record by id.
        Mirrors Go's Update().
        """
        ...

    @abstractmethod
    async def upsert(
        self, filters: dict[str, Any], data: dict[str, Any]
    ) -> Any:
        """
        Insert or update based on the filter criteria.
        Mirrors Go's UpSert().
        """
        ...

    @abstractmethod
    async def delete(self, record_id: str) -> None:
        """
        Delete a record by id.
        Mirrors Go's Delete().
        """
        ...

    @abstractmethod
    def describe_data_source(self) -> dict[str, Any]:
        """
        Return an Avro-like schema dict describing this model's fields.
        Generated from Pydantic model introspection (replaces Go's reflection).
        Mirrors Go's DescribeDataSource().
        """
        ...
