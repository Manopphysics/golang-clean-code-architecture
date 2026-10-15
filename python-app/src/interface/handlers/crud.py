"""
Generic CRUD HTTP handlers.

Mirrors Go: src/interface/handlers/gofiber/modules/crud/crud.go

Routes (all under /api/v1/data, all require JWT):
  GET /{slug}/describe  → describe
  GET /{slug}/          → retrieve_list
  GET /{slug}/{id}      → retrieve

Available slugs: users, user-tokens, user-permissions
"""
from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.postgres import get_session
from src.infrastructure.server.dependencies import get_crud_usecase
from src.infrastructure.server.middlewares import jwt_auth
from src.interface.handlers.response import error_response, success_response
from src.interface.handlers.schemas import ErrorResponse
from src.usecases.crud_usecase import ICRUDUsecase

router = APIRouter(
    prefix="/data",
    tags=["CRUD"],
    dependencies=[Depends(jwt_auth)],
)

_ERR_400 = {"model": ErrorResponse}
_ERR_401 = {
    "model": ErrorResponse,
    "content": {
        "application/json": {
            "example": {
                "trace_id": "middleware-002",
                "message": "missing authorization header",
            }
        }
    },
}


@router.get(
    "/{entity_model_slug}/describe",
    summary="Describe Data Source",
    description=(
        "Return the Avro-like schema for a registered entity model. "
        "Available slugs: `users`, `user-tokens`, `user-permissions`."
    ),
    responses={
        200: {
            "description": "Avro-like schema",
            "content": {
                "application/json": {
                    "example": {
                        "type": "record",
                        "name": "users",
                        "fields": [
                            {"name": "id", "type": "long"},
                            {"name": "email", "type": "string"},
                            {"name": "first_name", "type": "string"},
                            {"name": "last_name", "type": "string"},
                            {"name": "created_at", "type": "datetime"},
                            {"name": "updated_at", "type": "datetime"},
                        ],
                    }
                }
            },
        },
        400: _ERR_400,
        401: _ERR_401,
    },
)
async def describe(
    entity_model_slug: str,
    usecase: ICRUDUsecase = Depends(get_crud_usecase),
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """Return Avro-like schema for the given slug. Mirrors Go's Describe()."""
    try:
        schema = await usecase.describe_data_source(entity_model_slug.strip(), session)
    except ValueError as exc:
        return error_response("error", str(exc), status.HTTP_400_BAD_REQUEST)
    return success_response(schema)


@router.get(
    "/{entity_model_slug}/",
    summary="List Records",
    description=(
        "Paginated list of records for the given entity model slug. "
        "Use `_page` and `_pageSize` query params to control pagination."
    ),
    responses={
        200: {
            "description": "Paginated list",
            "content": {
                "application/json": {
                    "example": {
                        "code": 200,
                        "data": [],
                        "page": 1,
                        "page_size": 10,
                        "total_page": 1,
                        "total_data": 0,
                        "message": "success",
                        "data_schema": None,
                    }
                }
            },
        },
        400: _ERR_400,
        401: _ERR_401,
    },
)
async def retrieve_list(
    entity_model_slug: str,
    request: Request,
    _page: int = Query(default=1, ge=1, alias="_page", description="Page number (1-indexed)"),
    _pageSize: int = Query(
        default=10,
        ge=1,
        le=1000,
        alias="_pageSize",
        description="Records per page (max 1000)",
    ),
    usecase: ICRUDUsecase = Depends(get_crud_usecase),
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """Paginated record list. Mirrors Go's RetriveList()."""
    permission = getattr(request.state, "user_permission", None)
    try:
        result = await usecase.retrieve_list(
            permission, entity_model_slug.strip(), _page, _pageSize, None, session
        )
    except ValueError as exc:
        return error_response("error", str(exc), status.HTTP_400_BAD_REQUEST)
    return success_response(result)


@router.get(
    "/{entity_model_slug}/{record_id}",
    summary="Get Single Record",
    description="Fetch a single record by its primary key.",
    responses={
        200: {
            "description": "Single record",
            "content": {
                "application/json": {
                    "example": {
                        "code": 200,
                        "data": {},
                        "message": "success",
                        "data_schema": None,
                    }
                }
            },
        },
        400: _ERR_400,
        401: _ERR_401,
    },
)
async def retrieve(
    entity_model_slug: str,
    record_id: str,
    request: Request,
    usecase: ICRUDUsecase = Depends(get_crud_usecase),
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """Fetch single record. Mirrors Go's Retrive()."""
    permission = getattr(request.state, "user_permission", None)
    try:
        result = await usecase.retrieve(
            permission, entity_model_slug.strip(), record_id, session
        )
    except ValueError as exc:
        return error_response("error", str(exc), status.HTTP_400_BAD_REQUEST)
    return success_response(result)
