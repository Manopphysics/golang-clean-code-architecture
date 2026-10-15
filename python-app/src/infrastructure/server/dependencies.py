"""
FastAPI dependency providers.

Mirrors Go's constructor DI pattern from main.go:
  repo → usecase → handler

In FastAPI, Depends() replaces manual constructor injection.
These functions are the single wiring point for the whole app.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.postgres import get_session
from src.interface.repositories.postgres.user_repository import PostgresUserRepository
from src.usecases.crud_usecase import CrudUsecase, ICRUDUsecase
from src.usecases.user_usecase import IUserUsecase, UserUsecase


def get_user_repository(
    session: AsyncSession = Depends(get_session),
) -> PostgresUserRepository:
    """
    Provide a PostgresUserRepository scoped to the current request session.
    Mirrors Go's postgresuserrepository.UserRepository() call in main.go.
    """
    return PostgresUserRepository(session=session)


def get_user_usecase(
    repo: PostgresUserRepository = Depends(get_user_repository),
) -> IUserUsecase:
    """
    Provide a UserUsecase with its repository injected.
    Mirrors Go's userusecase.UserUsecase(userRepository).
    """
    return UserUsecase(user_repository=repo)


def get_crud_usecase() -> ICRUDUsecase:
    """
    Provide a CrudUsecase (stateless — session is passed per-call).
    Mirrors Go's crudusecase.CrudUsecase().
    """
    return CrudUsecase()
