"""Tests for src/interface/repositories/crud_factory.py."""
from unittest.mock import MagicMock, patch

import pytest

from src.interface.repositories.crud_factory import get_crud_repository, get_registered_slugs
from src.interface.repositories.postgres.crud_repository import PostgresCRUDRepository
from src.interface.repositories.mongodb.crud_repository import MongoDBCRUDRepository


class TestGetRegisteredSlugs:
    def test_returns_list(self):
        slugs = get_registered_slugs()
        assert isinstance(slugs, list)

    def test_contains_known_slugs(self):
        slugs = get_registered_slugs()
        assert "users" in slugs
        assert "user-tokens" in slugs
        assert "user-permissions" in slugs

    def test_is_sorted(self):
        slugs = get_registered_slugs()
        assert slugs == sorted(slugs)


class TestGetCrudRepository:
    def test_users_slug_returns_postgres_repo(self):
        session = MagicMock()
        repo = get_crud_repository("users", session)
        assert isinstance(repo, PostgresCRUDRepository)

    def test_user_tokens_slug_returns_postgres_repo(self):
        session = MagicMock()
        repo = get_crud_repository("user-tokens", session)
        assert isinstance(repo, PostgresCRUDRepository)

    def test_user_permissions_slug_returns_postgres_repo(self):
        session = MagicMock()
        repo = get_crud_repository("user-permissions", session)
        assert isinstance(repo, PostgresCRUDRepository)

    def test_unknown_slug_raises_value_error(self):
        with pytest.raises(ValueError, match="not found"):
            get_crud_repository("nonexistent-model", MagicMock())

    def test_error_message_lists_available_slugs(self):
        try:
            get_crud_repository("bad-slug", MagicMock())
        except ValueError as e:
            assert "users" in str(e)

    def test_mongodb_datasource_returns_mongodb_repo(self):
        """When a model reports datasource='mongodb', get MongoDB repo."""
        from src.domain.models.user import UserModel
        session = MagicMock()
        mock_collection = MagicMock()

        # get_collection is imported lazily inside get_crud_repository,
        # so patch it at its definition module.
        with patch.object(UserModel, "datasource", return_value="mongodb"), \
             patch(
                 "src.infrastructure.database.mongodb.get_collection",
                 return_value=mock_collection,
             ):
            repo = get_crud_repository("users", session)

        assert isinstance(repo, MongoDBCRUDRepository)
