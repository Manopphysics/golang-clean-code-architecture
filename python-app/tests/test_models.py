"""Tests for src/domain/models/user.py — ORM model methods."""
from datetime import UTC, datetime

from src.domain.models.user import UserModel, UserPermissionModel, UserTokenModel


class TestUserModel:
    def _make_user(self) -> UserModel:
        m = UserModel(
            id=1,
            email="a@b.com",
            first_name="Alice",
            last_name="Smith",
            password="$2b$10$hashed",
        )
        m.created_at = datetime(2026, 1, 1, tzinfo=UTC)
        m.updated_at = datetime(2026, 1, 2, tzinfo=UTC)
        return m

    def test_to_entity_returns_user_entity(self):
        from src.domain.entities.user import UserEntity
        user = self._make_user()
        entity = user.to_entity()
        assert isinstance(entity, UserEntity)

    def test_to_entity_has_correct_id(self):
        user = self._make_user()
        assert user.to_entity().id == 1

    def test_to_entity_has_correct_email(self):
        user = self._make_user()
        assert user.to_entity().email == "a@b.com"

    def test_to_entity_excludes_password(self):
        user = self._make_user()
        entity = user.to_entity()
        assert not hasattr(entity, "password")

    def test_to_entity_preserves_timestamps(self):
        user = self._make_user()
        entity = user.to_entity()
        assert entity.created_at == datetime(2026, 1, 1, tzinfo=UTC)
        assert entity.updated_at == datetime(2026, 1, 2, tzinfo=UTC)

    def test_datasource_returns_postgresql(self):
        assert UserModel.datasource() == "postgresql"

    def test_tablename(self):
        assert UserModel.__tablename__ == "users"


class TestUserTokenModel:
    def test_datasource_returns_postgresql(self):
        assert UserTokenModel.datasource() == "postgresql"

    def test_tablename(self):
        assert UserTokenModel.__tablename__ == "user_tokens"


class TestUserPermissionModel:
    def test_datasource_returns_postgresql(self):
        assert UserPermissionModel.datasource() == "postgresql"

    def test_tablename(self):
        assert UserPermissionModel.__tablename__ == "user_permissions"
