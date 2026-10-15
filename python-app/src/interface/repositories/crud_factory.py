"""
CRUD repository factory.

Mirrors Go: src/interface/repositories/crud/crudRepository.go

GetCRUDRepository(slug) resolves a URL slug (e.g. "user-tokens") to the
correct model class, then returns either a Postgres or MongoDB repository
implementation based on the model's datasource() method.

Registered models (mirrors Go's config.EntitiyModels):
  users            → UserModel            → PostgreSQL
  user-tokens      → UserTokenModel       → PostgreSQL
  user-permissions → UserPermissionModel  → PostgreSQL
"""
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models.user import UserModel, UserPermissionModel, UserTokenModel
from src.domain.repositories.crud import ICRUDRepository
from src.interface.repositories.mongodb.crud_repository import MongoDBCRUDRepository
from src.interface.repositories.postgres.crud_repository import PostgresCRUDRepository
from src.shared.crud.constants import DatasourceType
from src.shared.crud.converter import convert_name_to_crud_slug

# ---------------------------------------------------------------------------
# Model registry — add new models here as the schema grows
# Mirrors Go's config.EntitiyModels []ICRUDDataModel
# ---------------------------------------------------------------------------
_REGISTERED_MODELS = [
    UserModel,
    UserTokenModel,
    UserPermissionModel,
]

# Build a slug → model_class lookup once at import time
_SLUG_TO_MODEL: dict[str, type] = {
    convert_name_to_crud_slug(m.__tablename__): m  # type: ignore[attr-defined]
    for m in _REGISTERED_MODELS
}


def get_crud_repository(
    slug: str,
    session: AsyncSession,
) -> ICRUDRepository:
    """
    Resolve a URL slug to a concrete ICRUDRepository.

    Args:
        slug:    Entity model slug from the URL (e.g. "users", "user-tokens").
        session: Active AsyncSession for PostgreSQL repositories.

    Returns:
        A PostgresCRUDRepository or MongoDBCRUDRepository instance.

    Raises:
        ValueError: If the slug does not match any registered model.

    Mirrors Go's GetCRUDRepository() which iterates EntitiyModels,
    converts each TableName() to a slug, and dispatches on Datasource().
    """
    model_class = _SLUG_TO_MODEL.get(slug)
    if model_class is None:
        available = ", ".join(sorted(_SLUG_TO_MODEL.keys()))
        raise ValueError(
            f"entity model slug '{slug}' not found. "
            f"Available: {available}"
        )

    datasource = model_class.datasource()  # type: ignore[attr-defined]

    if datasource == DatasourceType.MONGODB:
        from src.infrastructure.database.mongodb import get_collection
        collection = get_collection(model_class.__tablename__)  # type: ignore[attr-defined]
        return MongoDBCRUDRepository(collection=collection, model_class=model_class)

    # Default: PostgreSQL
    return PostgresCRUDRepository(session=session, model_class=model_class)


def get_registered_slugs() -> list[str]:
    """Return all registered model slugs — useful for documentation."""
    return sorted(_SLUG_TO_MODEL.keys())
