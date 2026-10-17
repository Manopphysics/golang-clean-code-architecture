"""Tests for src/shared/crud/converter.py."""
import pytest

from src.shared.crud.converter import camel_to_snake, convert_name_to_crud_slug


class TestCamelToSnake:
    @pytest.mark.parametrize("input_val,expected", [
        ("UserModel", "user_model"),
        ("UserTokenModel", "user_token_model"),
        ("UserPermissionModel", "user_permission_model"),
        ("users", "users"),
        ("user_tokens", "user_tokens"),  # already snake_case
        # Consecutive caps: the regex only inserts _ between [a-z0-9] and [A-Z]
        # so "ABC" → no separator before B or C, only before the trailing lowercase.
        ("ABCDef", "abcdef"),
        ("HTMLParser", "htmlparser"),
        ("simpleword", "simpleword"),
    ])
    def test_conversion(self, input_val, expected):
        assert camel_to_snake(input_val) == expected

    def test_all_lowercase_output(self):
        result = camel_to_snake("CamelCase")
        assert result == result.lower()


class TestConvertNameToCrudSlug:
    @pytest.mark.parametrize("input_val,expected", [
        ("users", "users"),
        ("user_tokens", "user-tokens"),
        ("user_permissions", "user-permissions"),
        ("UserModel", "user-model"),
        ("UserTokenModel", "user-token-model"),
    ])
    def test_conversion(self, input_val, expected):
        assert convert_name_to_crud_slug(input_val) == expected

    def test_no_underscores_in_output(self):
        result = convert_name_to_crud_slug("some_table_name")
        assert "_" not in result

    def test_returns_string(self):
        assert isinstance(convert_name_to_crud_slug("table"), str)
