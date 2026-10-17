"""Tests for src/usecases/user_usecase.py — all 6 methods, all branches."""
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities.user import (
    UserEntity,
    UserLoginRequest,
    UserLoginResponse,
    UserRefreshTokenRequest,
    UserRegisterRequest,
    UserTokenEntity,
)
from src.domain.models.user import UserModel, UserPermissionModel, UserTokenModel
from src.usecases.user_usecase import UserUsecase


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user_entity(user_id: int = 1) -> UserEntity:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    return UserEntity(
        id=user_id, email="a@b.com",
        first_name="A", last_name="B",
        created_at=now, updated_at=now,
    )


def _make_user_model(user_id: int = 1) -> UserModel:
    m = UserModel(
        id=user_id, email="a@b.com",
        first_name="A", last_name="B",
        password="$2b$10$hashed",
    )
    m.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    m.updated_at = datetime(2026, 1, 1, tzinfo=UTC)
    return m


def _make_token_model(user_id: int = 1) -> UserTokenModel:
    tok = UserTokenModel(
        id=1, user_id=user_id,
        access="access.token", refresh="refresh.token",
    )
    tok.updated_at = datetime(2026, 1, 1, tzinfo=UTC)
    tok.user = _make_user_model(user_id)
    return tok


# ---------------------------------------------------------------------------
# register_user
# ---------------------------------------------------------------------------

class TestRegisterUser:
    @pytest.mark.asyncio
    async def test_happy_path_calls_insert_user(self, mock_user_repo, user_entity):
        mock_user_repo.insert_user.return_value = user_entity
        usecase = UserUsecase(mock_user_repo)
        req = UserRegisterRequest(
            email="a@b.com", password="pw", first_name="A", last_name="B"
        )
        result = await usecase.register_user(req)
        mock_user_repo.insert_user.assert_awaited_once_with(req)
        assert result == user_entity

    @pytest.mark.asyncio
    async def test_propagates_repo_exception(self, mock_user_repo):
        mock_user_repo.insert_user.side_effect = ValueError("duplicate email")
        usecase = UserUsecase(mock_user_repo)
        req = UserRegisterRequest(
            email="a@b.com", password="pw", first_name="A", last_name="B"
        )
        with pytest.raises(ValueError, match="duplicate email"):
            await usecase.register_user(req)


# ---------------------------------------------------------------------------
# user_login
# ---------------------------------------------------------------------------

class TestUserLogin:
    @pytest.mark.asyncio
    async def test_happy_path_returns_login_response(self, mock_user_repo):
        user_model = _make_user_model()
        mock_user_repo.get_user_by_email.return_value = user_model
        mock_user_repo.upsert_oauth.return_value = None

        with patch(
            "src.usecases.user_usecase.PostgresUserRepository.verify_password",
            return_value=True,
        ), patch(
            "src.usecases.user_usecase.create_access_token",
            return_value="acc.tok",
        ), patch(
            "src.usecases.user_usecase.create_refresh_token",
            return_value="ref.tok",
        ):
            usecase = UserUsecase(mock_user_repo)
            req = UserLoginRequest(email="a@b.com", password="pw")
            result = await usecase.user_login(req)

        assert isinstance(result, UserLoginResponse)
        assert result.token.access == "acc.tok"
        assert result.token.refresh == "ref.tok"

    @pytest.mark.asyncio
    async def test_user_not_found_raises(self, mock_user_repo):
        mock_user_repo.get_user_by_email.side_effect = ValueError("not found")
        usecase = UserUsecase(mock_user_repo)
        req = UserLoginRequest(email="no@here.com", password="pw")
        with pytest.raises(ValueError, match="not found"):
            await usecase.user_login(req)

    @pytest.mark.asyncio
    async def test_wrong_password_raises(self, mock_user_repo):
        mock_user_repo.get_user_by_email.return_value = _make_user_model()
        with patch(
            "src.usecases.user_usecase.PostgresUserRepository.verify_password",
            return_value=False,
        ):
            usecase = UserUsecase(mock_user_repo)
            req = UserLoginRequest(email="a@b.com", password="wrong")
            with pytest.raises(ValueError, match="password is invalid"):
                await usecase.user_login(req)

    @pytest.mark.asyncio
    async def test_upsert_oauth_is_called(self, mock_user_repo):
        mock_user_repo.get_user_by_email.return_value = _make_user_model()
        mock_user_repo.upsert_oauth.return_value = None
        with patch(
            "src.usecases.user_usecase.PostgresUserRepository.verify_password",
            return_value=True,
        ), patch("src.usecases.user_usecase.create_access_token", return_value="a"), \
           patch("src.usecases.user_usecase.create_refresh_token", return_value="r"):
            usecase = UserUsecase(mock_user_repo)
            await usecase.user_login(UserLoginRequest(email="a@b.com", password="pw"))
        mock_user_repo.upsert_oauth.assert_awaited_once()


# ---------------------------------------------------------------------------
# user_logout
# ---------------------------------------------------------------------------

class TestUserLogout:
    @pytest.mark.asyncio
    async def test_happy_path_deletes_token(self, mock_user_repo):
        tok = _make_token_model()
        mock_user_repo.find_one_oauth_by_user_id.return_value = tok
        mock_user_repo.delete_oauth_by_user_id.return_value = None

        from src.shared.authentication.jwt import create_refresh_token
        refresh = create_refresh_token(1)
        tok.refresh = refresh

        usecase = UserUsecase(mock_user_repo)
        await usecase.user_logout(UserRefreshTokenRequest(refresh_token=refresh))
        mock_user_repo.delete_oauth_by_user_id.assert_awaited_once_with(1)

    @pytest.mark.asyncio
    async def test_expired_token_raises(self, mock_user_repo):
        from jose import jwt as jose_jwt
        from datetime import timedelta
        from src.shared.authentication.jwt import ALGORITHM, AUDIENCES
        from src.config import get_settings
        secret = get_settings().secret_key
        expired = jose_jwt.encode(
            {
                "claims": {"id": 1}, "iss": "test", "sub": "refresh-token",
                "aud": AUDIENCES,
                "exp": datetime.now(tz=UTC) - timedelta(seconds=1),
                "nbf": datetime.now(tz=UTC) - timedelta(seconds=10),
                "iat": datetime.now(tz=UTC) - timedelta(seconds=10),
            },
            secret, algorithm=ALGORITHM,
        )
        usecase = UserUsecase(mock_user_repo)
        with pytest.raises(ValueError, match="token had expired"):
            await usecase.user_logout(UserRefreshTokenRequest(refresh_token=expired))

    @pytest.mark.asyncio
    async def test_token_not_in_db_raises(self, mock_user_repo):
        mock_user_repo.find_one_oauth_by_user_id.return_value = None
        from src.shared.authentication.jwt import create_refresh_token
        refresh = create_refresh_token(1)
        usecase = UserUsecase(mock_user_repo)
        with pytest.raises(ValueError, match="user token not found"):
            await usecase.user_logout(UserRefreshTokenRequest(refresh_token=refresh))

    @pytest.mark.asyncio
    async def test_refresh_token_mismatch_raises(self, mock_user_repo):
        tok = _make_token_model()
        tok.refresh = "different.token"
        mock_user_repo.find_one_oauth_by_user_id.return_value = tok
        from src.shared.authentication.jwt import create_refresh_token
        refresh = create_refresh_token(1)
        usecase = UserUsecase(mock_user_repo)
        with pytest.raises(ValueError, match="user token not found"):
            await usecase.user_logout(UserRefreshTokenRequest(refresh_token=refresh))


# ---------------------------------------------------------------------------
# user_refresh_token
# ---------------------------------------------------------------------------

class TestUserRefreshToken:
    @pytest.mark.asyncio
    async def test_happy_path_returns_new_tokens(self, mock_user_repo):
        from src.shared.authentication.jwt import create_refresh_token
        refresh = create_refresh_token(1)
        tok = _make_token_model()
        tok.refresh = refresh
        mock_user_repo.find_one_oauth_by_user_id.return_value = tok
        mock_user_repo.upsert_oauth.return_value = None

        usecase = UserUsecase(mock_user_repo)
        result = await usecase.user_refresh_token(
            UserRefreshTokenRequest(refresh_token=refresh)
        )
        assert isinstance(result, UserLoginResponse)
        assert result.token.refresh  # new refresh token present
        assert result.user.id == 1

    @pytest.mark.asyncio
    async def test_token_not_found_raises(self, mock_user_repo):
        mock_user_repo.find_one_oauth_by_user_id.return_value = None
        from src.shared.authentication.jwt import create_refresh_token
        refresh = create_refresh_token(1)
        usecase = UserUsecase(mock_user_repo)
        with pytest.raises(ValueError, match="user token not found"):
            await usecase.user_refresh_token(
                UserRefreshTokenRequest(refresh_token=refresh)
            )

    @pytest.mark.asyncio
    async def test_token_mismatch_raises(self, mock_user_repo):
        tok = _make_token_model()
        tok.refresh = "some.other.token"
        mock_user_repo.find_one_oauth_by_user_id.return_value = tok
        from src.shared.authentication.jwt import create_refresh_token
        refresh = create_refresh_token(1)
        usecase = UserUsecase(mock_user_repo)
        with pytest.raises(ValueError, match="user token not found"):
            await usecase.user_refresh_token(
                UserRefreshTokenRequest(refresh_token=refresh)
            )

    @pytest.mark.asyncio
    async def test_upsert_is_called(self, mock_user_repo):
        from src.shared.authentication.jwt import create_refresh_token
        refresh = create_refresh_token(1)
        tok = _make_token_model()
        tok.refresh = refresh
        mock_user_repo.find_one_oauth_by_user_id.return_value = tok
        mock_user_repo.upsert_oauth.return_value = None

        usecase = UserUsecase(mock_user_repo)
        await usecase.user_refresh_token(
            UserRefreshTokenRequest(refresh_token=refresh)
        )
        mock_user_repo.upsert_oauth.assert_awaited_once()


# ---------------------------------------------------------------------------
# user_authentication
# ---------------------------------------------------------------------------

class TestUserAuthentication:
    @pytest.mark.asyncio
    async def test_happy_path_returns_entity_and_permission(self, mock_user_repo):
        from src.shared.authentication.jwt import create_access_token
        access = create_access_token(1)
        tok = _make_token_model()
        mock_user_repo.find_oauth_by_user_id_and_access_token.return_value = tok
        mock_user_repo.get_user_permission_by_user_id.return_value = None

        usecase = UserUsecase(mock_user_repo)
        entity, permission = await usecase.user_authentication(access)
        assert entity.id == 1
        assert permission is None

    @pytest.mark.asyncio
    async def test_returns_permission_when_present(self, mock_user_repo):
        from src.shared.authentication.jwt import create_access_token
        access = create_access_token(1)
        tok = _make_token_model()
        perm = UserPermissionModel(id=1, user_id=1, permission="admin")
        mock_user_repo.find_oauth_by_user_id_and_access_token.return_value = tok
        mock_user_repo.get_user_permission_by_user_id.return_value = perm

        usecase = UserUsecase(mock_user_repo)
        entity, permission = await usecase.user_authentication(access)
        assert permission.permission == "admin"

    @pytest.mark.asyncio
    async def test_token_not_in_db_raises(self, mock_user_repo):
        from src.shared.authentication.jwt import create_access_token
        access = create_access_token(1)
        mock_user_repo.find_oauth_by_user_id_and_access_token.return_value = None

        usecase = UserUsecase(mock_user_repo)
        with pytest.raises(ValueError, match="user token not found"):
            await usecase.user_authentication(access)

    @pytest.mark.asyncio
    async def test_invalid_token_raises(self, mock_user_repo):
        usecase = UserUsecase(mock_user_repo)
        with pytest.raises(ValueError):
            await usecase.user_authentication("not.a.jwt")


# ---------------------------------------------------------------------------
# get_user_profile
# ---------------------------------------------------------------------------

class TestGetUserProfile:
    @pytest.mark.asyncio
    async def test_happy_path(self, mock_user_repo):
        mock_user_repo.get_user_by_user_id.return_value = _make_user_model()
        usecase = UserUsecase(mock_user_repo)
        entity = await usecase.get_user_profile(1)
        assert entity.id == 1

    @pytest.mark.asyncio
    async def test_not_found_raises(self, mock_user_repo):
        mock_user_repo.get_user_by_user_id.side_effect = ValueError("not found")
        usecase = UserUsecase(mock_user_repo)
        with pytest.raises(ValueError, match="not found"):
            await usecase.get_user_profile(999)
