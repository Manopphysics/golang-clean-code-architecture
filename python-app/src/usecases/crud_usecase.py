"""
CRUD use case — business logic layer.

Mirrors Go: src/usecases/crud/crudUsecase.go

ICRUDUsecase interface + CrudUsecase implementation.
Delegates entirely to the appropriate repository via the factory —
no DB logic lives here, matching Go's thin use case pattern.

Note: Go's implementation accepted a userPermissionModel parameter
but never checked it (authorization not enforced). We keep the same
signature for parity but note it as a future extension point.
"""
from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.crud import DataListResponse, DataResponse
from src.domain.models.user import UserPermissionModel
from src.interface.repositories.crud_factory import get_crud_repository

# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------

class ICRUDUsecase(ABC):
    """
    Port for generic CRUD business logic.
    Mirrors Go's ICRUDUsecase interface.
    """

    @abstractmethod
    async def retrieve(
        self,
        permission: UserPermissionModel | None,
        slug: str,
        record_id: str,
        session: AsyncSession,
    ) -> DataResponse:
        """Fetch a single record by slug + id. Mirrors Go's Retrive()."""
        ...

    @abstractmethod
    async def retrieve_list(
        self,
        permission: UserPermissionModel | None,
        slug: str,
        page: int,
        page_size: int,
        filters: dict[str, Any] | None,
        session: AsyncSession,
    ) -> DataListResponse:
        """Fetch a paginated list by slug. Mirrors Go's RetriveList()."""
        ...

    @abstractmethod
    async def describe_data_source(
        self,
        slug: str,
        session: AsyncSession,
    ) -> dict[str, Any]:
        """Return Avro-like schema for a slug. Mirrors Go's DescribeDataSource()."""
        ...


# ---------------------------------------------------------------------------
# Implementation
# ---------------------------------------------------------------------------

class CrudUsecase(ICRUDUsecase):
    """
    Concrete CRUD use case.
    Thin delegation layer — all real work is in the repository.
    Mirrors Go's crudUsecase struct and its factory function CrudUsecase().
    """

    async def retrieve(
        self,
        permission: UserPermissionModel | None,
        slug: str,
        record_id: str,
        session: AsyncSession,
    ) -> DataResponse:
        """
        Mirrors Go's Retrive():
          Resolves slug → repository → GetOneById(id).
        Permission parameter is accepted for future authorization checks
        (Go also accepted it but never checked it).
        """
        repo = get_crud_repository(slug, session)
        return await repo.get_one_by_id(record_id)

    async def retrieve_list(
        self,
        permission: UserPermissionModel | None,
        slug: str,
        page: int,
        page_size: int,
        filters: dict[str, Any] | None,
        session: AsyncSession,
    ) -> DataListResponse:
        """
        Mirrors Go's RetriveList():
          Resolves slug → repository → GetList(page, pageSize, filter).
        Note: Go passed nil as the filter; we pass it through for future use.
        """
        repo = get_crud_repository(slug, session)
        return await repo.get_list(page, page_size, filters)

    async def describe_data_source(
        self,
        slug: str,
        session: AsyncSession,
    ) -> dict[str, Any]:
        """
        Mirrors Go's DescribeDataSource():
          Resolves slug → repository → DescribeDataSource().
        """
        repo = get_crud_repository(slug, session)
        return repo.describe_data_source()
