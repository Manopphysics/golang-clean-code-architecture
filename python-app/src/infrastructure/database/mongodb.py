"""
MongoDB async connector.

Mirrors Go: src/infrastructure/database/mongodb/connector.go

Uses Motor (the async MongoDB driver built on PyMongo).
The client is a lazy singleton — created on first use, Motor manages
its own internal connection pool.

Exposes:
  get_mongo_db()     — returns the Motor database instance
  get_collection()   — returns a named Motor collection
  close_mongo()      — call during app shutdown lifespan
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase

from src.config import get_settings

_settings = get_settings()

# ---------------------------------------------------------------------------
# Lazy singleton client
# Mirrors Go's MongodbHandlerDefaultConfig() connection setup.
# ---------------------------------------------------------------------------
_client: AsyncIOMotorClient | None = None


def _get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(_settings.mongodb_atlas_uri)
    return _client


def get_mongo_db() -> AsyncIOMotorDatabase:
    """Return the Motor database for the configured DB name."""
    return _get_client()[_settings.mongodb_db_name]


def get_collection(collection_name: str) -> AsyncIOMotorCollection:
    """
    Return a Motor collection by name.
    Mirrors Go's IMongodbHandler.GetCorrection(dataModel).
    """
    return get_mongo_db()[collection_name]


async def close_mongo() -> None:
    """
    Close the MongoDB client and release connections.
    Called during FastAPI lifespan shutdown.
    Mirrors Go's IMongodbHandler.Close().
    """
    global _client
    if _client is not None:
        _client.close()
        _client = None
