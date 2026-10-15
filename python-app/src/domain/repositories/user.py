"""
IUserRepository — abstract repository interface (port).

Mirrors Go: src/domain/repositories/user.go

All 9 methods from the Go interface are defined here.
Use cases depend only on this ABC — never on a concrete implementation.
The concrete Postgres implementation lives in:
  src/interface/repositories/postgres/user_repository.py  (added in PR-05)
"""
from abc import ABC, abstractmethod

from src.domain.entities.user import UserEntity, UserLoginResponse, UserRegisterRequest
from src.domain.models.user import UserModel, UserPermissionModel, UserTokenModel


class IUserRepository(ABC):
    """
    Port for all user persistence operations.
    Follows Clean Architecture: the inner layer (use cases) depends on this
    interface, never on the outer layer (database implementations).
    """

    @abstractmethod
    async def insert_user(self, request: UserRegisterRequest) -> UserEntity:
        """
        Insert a new user row and return the public entity.
        The password in `request` must already be bcrypt-hashed before calling.
        Mirrors Go's InsertUser().
        """
        ...

    @abstractmethod
    async def get_user_by_email(self, email: str) -> UserModel:
        """
        Fetch a UserModel (including hashed password) by email address.
        Raises an exception if not found.
        Mirrors Go's GetUserByEmail().
        """
        ...

    @abstractmethod
    async def get_user_by_user_id(self, user_id: int) -> UserModel:
        """
        Fetch a UserModel by primary key.
        Raises an exception if not found.
        Mirrors Go's GetUserByUserId().
        """
        ...

    @abstractmethod
    async def insert_oauth(self, response: UserLoginResponse) -> None:
        """
        Insert a brand-new token row (assumes no existing row for this user).
        Mirrors Go's InsertOAuth().
        """
        ...

    @abstractmethod
    async def upsert_oauth(self, response: UserLoginResponse) -> None:
        """
        Update the token row for a user if one exists, otherwise insert.
        Called on every login and token refresh.
        Mirrors Go's UpsertOAuth().
        """
        ...

    @abstractmethod
    async def find_one_oauth_by_user_id(self, user_id: int) -> UserTokenModel | None:
        """
        Return the token row (with joined User) for the given user_id, or None.
        Mirrors Go's FindOneOAuthByUserId().
        """
        ...

    @abstractmethod
    async def find_oauth_by_user_id_and_access_token(
        self, user_id: int, access_token: str
    ) -> UserTokenModel | None:
        """
        Return the token row where both user_id AND access token string match.
        Used by the JWT auth middleware to validate every authenticated request.
        Mirrors Go's FindOAuthByUserIdAndAccessToken().
        """
        ...

    @abstractmethod
    async def delete_oauth_by_user_id(self, user_id: int) -> None:
        """
        Delete the token row for the given user (logout).
        Mirrors Go's DeleteOAuthByUserId().
        """
        ...

    @abstractmethod
    async def get_user_permission_by_user_id(
        self, user_id: int
    ) -> UserPermissionModel | None:
        """
        Return the permission row for the given user, or None if not found.
        Mirrors Go's GetUserPermissionByUserId().
        """
        ...
