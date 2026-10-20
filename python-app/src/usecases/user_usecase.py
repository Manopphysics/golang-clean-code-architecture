"""
User use case — business logic layer.

Mirrors Go: src/usecases/user/userUsecase.go

IUserUsecase interface + UserUsecase implementation.
All 5 methods from the Go interface are implemented, plus GetUserProfile
(which existed in Go's implementation but was missing from the interface).

This layer has zero knowledge of HTTP or databases — it only depends on
the IUserRepository port and the shared JWT utilities.
"""
from abc import ABC, abstractmethod

from src.domain.entities.user import (
    UserEntity,
    UserLoginRequest,
    UserLoginResponse,
    UserRefreshTokenRequest,
    UserRegisterRequest,
    UserTokenEntity,
)
from src.domain.models.user import UserPermissionModel
from src.domain.repositories.user import IUserRepository
from src.shared.authentication.jwt import (
    create_access_token,
    create_refresh_token,
    parse_token,
    repeat_token,
)
from src.shared.password import verify_password

# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------

class IUserUsecase(ABC):
    """
    Port for user business logic.
    Mirrors Go's IUserUsecase interface.
    """

    @abstractmethod
    async def register_user(
        self, request: UserRegisterRequest
    ) -> UserEntity:
        """Hash password and insert a new user. Mirrors Go's RegisterUser()."""
        ...

    @abstractmethod
    async def user_login(
        self, request: UserLoginRequest
    ) -> UserLoginResponse:
        """
        Verify credentials, issue JWT pair, upsert tokens in DB.
        Mirrors Go's UserLogin().
        """
        ...

    @abstractmethod
    async def user_logout(
        self, request: UserRefreshTokenRequest
    ) -> None:
        """
        Parse refresh token, validate it exists in DB, delete it.
        Mirrors Go's UserLogout().
        """
        ...

    @abstractmethod
    async def user_refresh_token(
        self, request: UserRefreshTokenRequest
    ) -> UserLoginResponse:
        """
        Validate refresh token, issue new access token, re-sign refresh
        token preserving original expiry, upsert in DB.
        Mirrors Go's UserRefreshToken().
        """
        ...

    @abstractmethod
    async def user_authentication(
        self, token: str
    ) -> tuple[UserEntity, UserPermissionModel | None]:
        """
        Parse access token, verify it exists in DB, return user + permissions.
        Called by the JWT middleware on every authenticated request.
        Mirrors Go's UserAuthentication().
        """
        ...

    @abstractmethod
    async def get_user_profile(self, user_id: int) -> UserEntity:
        """
        Fetch user entity by id.
        Mirrors Go's GetUserProfile() (was in impl but not in Go interface).
        """
        ...


# ---------------------------------------------------------------------------
# Implementation
# ---------------------------------------------------------------------------

class UserUsecase(IUserUsecase):
    """
    Concrete user use case implementation.
    Receives IUserRepository via constructor injection (mirrors Go's
    UserUsecase(userRepository) factory function).
    """

    def __init__(self, user_repository: IUserRepository) -> None:
        self._repo = user_repository

    async def register_user(
        self, request: UserRegisterRequest
    ) -> UserEntity:
        """
        Mirrors Go's RegisterUser():
          1. Validate email (done at schema layer via Pydantic)
          2. Hash password — delegated to repository (keeps hashing logic
             in one place; Go called BcryptHashing on the request object)
          3. Insert user and return the public entity
        """
        # We pass the plain-text request; the repository handles hashing
        # so the use case stays free of bcrypt knowledge.
        return await self._repo.insert_user(request)

    async def user_login(
        self, request: UserLoginRequest
    ) -> UserLoginResponse:
        """
        Mirrors Go's UserLogin():
          1. Fetch user by email (raises if not found)
          2. Verify bcrypt hash (raises if wrong)
          3. Issue access + refresh tokens
          4. Upsert token row in DB
          5. Return UserLoginResponse
        """
        user_model = await self._repo.get_user_by_email(request.email)

        # Verify password against bcrypt hash
        if not verify_password(request.password, user_model.password):
            raise ValueError("password is invalid")

        access = create_access_token(user_model.id)
        refresh = create_refresh_token(user_model.id)

        token_entity = UserTokenEntity(access=access, refresh=refresh)
        user_entity = user_model.to_entity()
        response = UserLoginResponse(user=user_entity, token=token_entity)

        await self._repo.upsert_oauth(response)
        return response

    async def user_logout(
        self, request: UserRefreshTokenRequest
    ) -> None:
        """
        Mirrors Go's UserLogout():
          1. Parse + validate refresh token
          2. Confirm matching token exists in DB
          3. Delete it
        """
        parsed = parse_token(request.refresh_token)

        token_row = await self._repo.find_one_oauth_by_user_id(parsed.user_id)
        if token_row is None or token_row.refresh != request.refresh_token:
            raise ValueError("user token not found")

        await self._repo.delete_oauth_by_user_id(parsed.user_id)

    async def user_refresh_token(
        self, request: UserRefreshTokenRequest
    ) -> UserLoginResponse:
        """
        Mirrors Go's UserRefreshToken():
          1. Parse refresh token
          2. Confirm it exists in DB with matching refresh value
          3. Issue new access token
          4. Re-sign refresh token preserving original expiry (RepeatToken)
          5. Upsert new tokens
          6. Return UserLoginResponse
        """
        parsed = parse_token(request.refresh_token)

        token_row = await self._repo.find_one_oauth_by_user_id(parsed.user_id)
        if token_row is None or token_row.refresh != request.refresh_token:
            raise ValueError("user token not found")

        new_access = create_access_token(parsed.user_id)
        # Preserve the original refresh expiry — never extend it
        new_refresh = repeat_token(parsed.user_id, parsed.expires_at)

        token_entity = UserTokenEntity(access=new_access, refresh=new_refresh)
        user_entity = token_row.user.to_entity()
        response = UserLoginResponse(user=user_entity, token=token_entity)

        await self._repo.upsert_oauth(response)
        return response

    async def user_authentication(
        self, token: str
    ) -> tuple[UserEntity, UserPermissionModel | None]:
        """
        Mirrors Go's UserAuthentication() — called by the JWT middleware:
          1. Parse + validate access token
          2. Look up token row by user_id AND access token string
             (stateful auth — token must still exist in DB)
          3. Fetch permission row (may be None if user has no permission row)
          4. Return (UserEntity, UserPermissionModel | None)
        """
        parsed = parse_token(token)

        token_row = await self._repo.find_oauth_by_user_id_and_access_token(
            parsed.user_id, token
        )
        if token_row is None:
            raise ValueError("user token not found")

        permission = await self._repo.get_user_permission_by_user_id(
            token_row.user_id
        )

        return token_row.user.to_entity(), permission

    async def get_user_profile(self, user_id: int) -> UserEntity:
        """
        Mirrors Go's GetUserProfile():
          Fetch user by id and return the public entity.
        """
        user_model = await self._repo.get_user_by_user_id(user_id)
        return user_model.to_entity()
