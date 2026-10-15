"""
Name conversion utilities.

Mirrors Go:
  src/shared/converter.go        — CamelToSnake
  src/shared/crud/converter.go   — ConvertNameToCRUDSlug
"""
import re


def camel_to_snake(name: str) -> str:
    """
    Convert CamelCase or PascalCase to snake_case.
    Mirrors Go's CamelToSnake().

    Examples:
        UserTokenModel  → user_token_model
        UserTokens      → user_tokens
    """
    s1 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return s1.lower()


def convert_name_to_crud_slug(name: str) -> str:
    """
    Convert a table name to its CRUD URL slug.
    Mirrors Go's ConvertNameToCRUDSlug():
      snake_case → replace underscores with hyphens.

    Examples:
        users            → users
        user_tokens      → user-tokens
        user_permissions → user-permissions
    """
    return camel_to_snake(name).replace("_", "-")
