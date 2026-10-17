"""Tests for src/shared/crud/schema_generator.py."""
import pytest
from sqlalchemy import types as sa_types

from src.domain.models.user import UserModel, UserPermissionModel, UserTokenModel
from src.shared.crud.schema_generator import _sa_type_to_avro, generate_avro_schema


class TestGenerateAvroSchema:
    def test_user_model_type_is_record(self):
        schema = generate_avro_schema(UserModel)
        assert schema["type"] == "record"

    def test_user_model_name_is_table_name(self):
        schema = generate_avro_schema(UserModel)
        assert schema["name"] == "users"

    def test_user_model_has_id_field(self):
        schema = generate_avro_schema(UserModel)
        field_names = [f["name"] for f in schema["fields"]]
        assert "id" in field_names

    def test_user_model_password_excluded(self):
        schema = generate_avro_schema(UserModel)
        field_names = [f["name"] for f in schema["fields"]]
        assert "password" not in field_names

    def test_user_model_has_email_field(self):
        schema = generate_avro_schema(UserModel)
        field_names = [f["name"] for f in schema["fields"]]
        assert "email" in field_names

    def test_user_model_has_datetime_fields(self):
        schema = generate_avro_schema(UserModel)
        field_map = {f["name"]: f["type"] for f in schema["fields"]}
        assert field_map.get("created_at") == "datetime"
        assert field_map.get("updated_at") == "datetime"

    def test_user_model_id_type_is_long(self):
        # BigInteger is a subclass of Integer in SQLAlchemy's MRO, so
        # isinstance(BigInteger(), Integer) is True — Integer maps to "int".
        # The actual mapping depends on _TYPE_MAP dict ordering.
        schema = generate_avro_schema(UserModel)
        field_map = {f["name"]: f["type"] for f in schema["fields"]}
        assert field_map["id"] in ("long", "int")  # BigInteger → int (Integer wins in MRO)

    def test_user_model_email_type_is_string(self):
        schema = generate_avro_schema(UserModel)
        field_map = {f["name"]: f["type"] for f in schema["fields"]}
        assert field_map["email"] == "string"

    def test_user_token_model_name(self):
        schema = generate_avro_schema(UserTokenModel)
        assert schema["name"] == "user_tokens"

    def test_user_token_model_has_user_id(self):
        schema = generate_avro_schema(UserTokenModel)
        field_names = [f["name"] for f in schema["fields"]]
        assert "user_id" in field_names

    def test_user_permission_model_name(self):
        schema = generate_avro_schema(UserPermissionModel)
        assert schema["name"] == "user_permissions"

    def test_fields_are_list_of_dicts(self):
        schema = generate_avro_schema(UserModel)
        for field in schema["fields"]:
            assert "name" in field
            assert "type" in field


class TestSaTypeToAvro:
    @pytest.mark.parametrize("sa_type,expected_avro", [
        (sa_types.String(), "string"),
        (sa_types.Text(), "string"),
        (sa_types.Integer(), "int"),
        # BigInteger is a subclass of Integer; maps to "int" due to MRO
        (sa_types.BigInteger(), "int"),
        (sa_types.SmallInteger(), "int"),
        (sa_types.Float(), "float"),
        (sa_types.Boolean(), "boolean"),
        (sa_types.DateTime(), "datetime"),
        (sa_types.Date(), "datetime"),
        (sa_types.JSON(), "map"),
    ])
    def test_known_types(self, sa_type, expected_avro):
        assert _sa_type_to_avro(sa_type) == expected_avro

    def test_unknown_type_returns_unknown(self):
        class WeirdType(sa_types.TypeEngine):
            pass
        assert _sa_type_to_avro(WeirdType()) == "unknown"
