"""
Avro-like schema generator.

Mirrors Go: src/shared/crud/avroSchema.go — GenerateAvroSchema()

Go used reflection to walk struct fields and map Go types to Avro type
strings. Here we use SQLAlchemy model inspection to achieve the same
result without reflection magic.

The output shape matches Go's:
  {
    "type":   "record",
    "name":   "table_name",
    "fields": [
      { "name": "id",    "type": "long" },
      { "name": "email", "type": "string" },
      ...
    ]
  }
"""
from typing import Any

from sqlalchemy import inspect as sa_inspect
from sqlalchemy import types as sa_types
from sqlalchemy.orm import DeclarativeBase

# ---------------------------------------------------------------------------
# SQLAlchemy column type → Avro type string
# Mirrors Go's type-switch in avroSchema.go
# ---------------------------------------------------------------------------
_TYPE_MAP: dict[type, str] = {
    sa_types.String: "string",
    sa_types.Text: "string",
    sa_types.Integer: "int",
    sa_types.BigInteger: "long",
    sa_types.SmallInteger: "int",
    sa_types.Float: "float",
    sa_types.Numeric: "float",
    sa_types.Boolean: "boolean",
    sa_types.DateTime: "datetime",
    sa_types.Date: "datetime",
    sa_types.JSON: "map",
}


def _sa_type_to_avro(col_type: sa_types.TypeEngine) -> str:  # type: ignore[type-arg]
    """Map a SQLAlchemy column type to an Avro-compatible type string."""
    for sa_type, avro_type in _TYPE_MAP.items():
        if isinstance(col_type, sa_type):
            return avro_type
    return "unknown"


def generate_avro_schema(model_class: type[DeclarativeBase]) -> dict[str, Any]:
    """
    Inspect a SQLAlchemy model and return an Avro-like schema dict.

    Mirrors Go's GenerateAvroSchema() which used reflect.TypeOf to walk
    struct fields. Here we use SQLAlchemy's mapper inspection instead.

    Skips relationship columns (foreign-key join fields) — only real
    table columns are included, matching Go's behaviour of skipping
    json:"-" fields.

    Args:
        model_class: A SQLAlchemy DeclarativeBase subclass (e.g. UserModel).

    Returns:
        {
          "type":   "record",
          "name":   "table_name",
          "fields": [ {"name": "...", "type": "..."}, ... ]
        }
    """
    mapper = sa_inspect(model_class)
    fields: list[dict[str, str]] = []

    for col in mapper.columns:
        # Skip password — mirrors Go's json:"-" tag
        if col.key == "password":
            continue
        fields.append({
            "name": col.key,
            "type": _sa_type_to_avro(col.type),
        })

    return {
        "type": "record",
        "name": model_class.__tablename__,  # type: ignore[attr-defined]
        "fields": fields,
    }
