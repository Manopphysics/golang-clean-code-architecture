"""
Datasource type constants.

Mirrors Go: src/shared/crud/const.go
Used by models (datasource() method) and the CRUD repository factory
to decide whether to route to Postgres or MongoDB.
"""
from enum import Enum


class DatasourceType(str, Enum):
    """Supported datasource backends for the generic CRUD engine."""
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
