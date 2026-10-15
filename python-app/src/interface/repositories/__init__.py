from .crud_factory import get_crud_repository, get_registered_slugs
from .mongodb import MongoDBCRUDRepository
from .postgres import PostgresCRUDRepository, PostgresUserRepository

__all__ = [
    "PostgresUserRepository",
    "PostgresCRUDRepository",
    "MongoDBCRUDRepository",
    "get_crud_repository",
    "get_registered_slugs",
]
