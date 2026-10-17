"""Tests for src/domain/entities/user.py — Pydantic entity validation."""
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from src.domain.entities.user import (
    UserEntity,
    UserLoginRequest,
    UserLoginResponse,
    UserRefreshTokenRequest,
    UserRegisterRequest,
    UserTokenEntity,
)


class TestUserRegisterRequest:
    """Email validator and field round-trips."""

    valid_emails = [
        "user@example.com",
        "user.name@sub.domain.org",
        "user-name@domain.io",
        "u@ex.com",
    ]

    invalid_emails = [
        "notanemail",
        "missing@",
        "@nodomain.com",
        "spaces in@email.com",
        "user@.com",
        "user@domain.toolongtld",  # TLD > 4 chars
        "user+tag@example.co",     # + not in regex character class
    ]

    @pytest.mark.parametrize("email", valid_emails)
    def test_valid_email_accepted(self, email):
        req = UserRegisterRequest(
            email=email, password="pass", first_name="A", last_name="B"
        )
        assert req.email == email

    @pytest.mark.parametrize("email", invalid_emails)
    def test_invalid_email_raises_validation_error(self, email):
        with pytest.raises(ValidationError) as exc_info:
            UserRegisterRequest(
                email=email, password="pass", first_name="A", last_name="B"
            )
        assert "email pattern is invalid" in str(exc_info.value)

    def test_all_fields_stored(self):
        req = UserRegisterRequest(
            email="a@b.com", password="secret", first_name="John", last_name="Doe"
        )
        assert req.email == "a@b.com"
        assert req.password == "secret"
        assert req.first_name == "John"
        assert req.last_name == "Doe"


class TestUserEntity:
    def test_from_dict(self):
        now = datetime(2026, 1, 1, tzinfo=UTC)
        entity = UserEntity(
            id=5,
            email="x@y.com",
            first_name="X",
            last_name="Y",
            created_at=now,
            updated_at=now,
        )
        assert entity.id == 5
        assert entity.email == "x@y.com"

    def test_no_password_field(self):
        """UserEntity must not have a password field."""
        assert not hasattr(UserEntity, "password") or "password" not in UserEntity.model_fields

    def test_model_dump_excludes_password(self):
        now = datetime(2026, 1, 1, tzinfo=UTC)
        entity = UserEntity(
            id=1, email="a@b.com", first_name="A", last_name="B",
            created_at=now, updated_at=now,
        )
        data = entity.model_dump()
        assert "password" not in data
        assert "email" in data


class TestUserTokenEntity:
    def test_fields(self):
        tok = UserTokenEntity(access="acc", refresh="ref")
        assert tok.access == "acc"
        assert tok.refresh == "ref"


class TestUserLoginRequest:
    def test_fields(self):
        req = UserLoginRequest(email="a@b.com", password="pw")
        assert req.email == "a@b.com"
        assert req.password == "pw"


class TestUserRefreshTokenRequest:
    def test_field(self):
        req = UserRefreshTokenRequest(refresh_token="tok")
        assert req.refresh_token == "tok"


class TestUserLoginResponse:
    def test_composition(self):
        now = datetime(2026, 1, 1, tzinfo=UTC)
        entity = UserEntity(
            id=1, email="a@b.com", first_name="A", last_name="B",
            created_at=now, updated_at=now,
        )
        token = UserTokenEntity(access="a", refresh="r")
        resp = UserLoginResponse(user=entity, token=token)
        assert resp.user.id == 1
        assert resp.token.access == "a"
