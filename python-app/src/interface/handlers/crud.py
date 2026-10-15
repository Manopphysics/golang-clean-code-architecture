"""
Generic CRUD HTTP handlers.

Mirrors Go: src/interface/handlers/gofiber/modules/crud/crud.go

Routes (all under /api/v1/data, all require JWT):
  GET /{slug}/describe  → describe
  GET /{slug}/          → retrieve_list
  GET /{slug}/{id}      → retrieve
"""
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.postgres import get_session
from src.infrastructure.server.dependencies import get_crud_usecase
from src.infrastructure.server.middlewares import jwt_auth
from src.interface.handlers.response import error_response, success_response
from src.usecases.crud_usecase import ICRUDUsecase

router = APIRouter(
    prefix="/data",
    tags=["CRUD"],
    dependencies=[Depends(jwt_auth)],   # all CRUD routes require JWT
)


@router.get(
    "/{entity_model_slug}/describe",
    summary="Describe Data Source",
)
async def describe(
    entity_model_slug: str,
    usecase: ICRUDUsecase = Depends(get_crud_usecase),
    session: AsyncSession = Depends(get_session),
) -> dict:  # type: ignore[type-arg]
    """
    Return the Avro-like schema for a registered entity model slug.
    Mirrors Go's Describe() handler.
    """
    try:
        schema = await usecase.describe_data_source(
            entity_model_slug.strip(), session
        )
    except ValueError as exc:
        return error_response("error", str(exc), status.HTTP_400_BAD_REQUEST)  # type: ignore[return-value]
    return success_response(schema)  # type: ignore[return-value]


@router.get(
    "/{entity_model_slug}/",
    summary="List Records",
)
async def retrieve_list(
    entity_model_slug: str,
    request: Request,
    _page: int = Query(default=1, ge=1, alias="_page"),
    _pageSize: int = Query(default=10, ge=1, le=1000, alias="_pageSize"),
    usecase: ICRUDUsecase = Depends(get_crud_usecase),
    session: AsyncSession = Depends(get_session),
) -> dict:  # type: ignore[type-arg]
    """
    Paginated list of records for a given entity model slug.
    Mirrors Go's RetriveList() handler.
    Query params: _page (default 1), _pageSize (default 10, max 1000).
    """
    permission = getattr(request.state, "user_permission", None)
    try:
        result = await usecase.retrieve_list(
            permission,
            entity_model_slug.strip(),
            _page,
            _pageSize,
            None,    # filters — future extension, matches Go's nil
            session,
        )
    except ValueError as exc:
        return error_response("error", str(exc), status.HTTP_400_BAD_REQUEST)  # type: ignore[return-value]
    return success_response(result)  # type: ignore[return-value]


@router.get(
    "/{entity_model_slug}/{record_id}",
    summary="Get Single Record",
)
async def retrieve(
    entity_model_slug: str,
    record_id: str,
    request: Request,
    usecase: ICRUDUsecase = Depends(get_crud_usecase),
    session: AsyncSession = Depends(get_session),
) -> dict:  # type: ignore[type-arg]
    """
    Fetch a single record by id for a given entity model slug.
    Mirrors Go's Retrive() handler.
    """
    permission = getattr(request.state, "user_permission", None)
    try:
        result = await usecase.retrieve(
            permission,
            entity_model_slug.strip(),
            record_id,
            session,
        )
    except ValueError as exc:
        return error_response("error", str(exc), status.HTTP_400_BAD_REQUEST)  # type: ignore[return-value]
    return success_response(result)  # type: ignore[return-value]
