"""
PostgreSQL implementation of IUserRepository.

Mirrors Go: src/interface/repositories/postgres/user/userRepository.go

All 9 methods from the interface are implemented here using
SQLAlchemy 2.0 async queries.
"""
import bcrypt
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import UserEntity, UserLoginResponse, UserRegisterRequest
from src.domain.models.user import UserModel, UserPermissionModel, UserTokenModel
from src.domain.repositories.user import IUserRepository

# bcrypt cost factor 10 — matches Go's bcrypt.GenerateFromPassword(..., 10)
_BCRYPT_ROUNDS = 10


class PostgresUserRepository(IUserRepository):
    """
    Concrete IUserRepository backed by PostgreSQL via SQLAlchemy async.
    One instance is created per request (session is injected via Depends).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def hash_password(plain: str) -> str:
        """
        Bcrypt-hash a plain-text password.
        Mirrors Go's BcryptHashing() in UserRegisterRequest.
        """
        return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)).decode()

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        """
        Verify a plain password against a bcrypt hash.
        Mirrors Go's bcrypt.CompareHashAndPassword().
        """
        return bcrypt.checkpw(plain.encode(), hashed.encode())

    # ------------------------------------------------------------------
    # IUserRepository — 9 methods
    # ------------------------------------------------------------------

    async def insert_user(self, request: UserRegisterRequest) -> UserEntity:
        """
        Hash the password then insert a new user row.
        Mirrors Go's InsertUser().
        """
        hashed = self.hash_password(request.password)
        user = UserModel(
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            password=hashed,
        )
        self._session.add(user)
        await self._session.flush()   # populate auto-generated id + timestamps
        await self._session.refresh(user)
        return user.to_entity()

    async def get_user_by_email(self, email: str) -> UserModel:
        """
        Fetch a UserModel by email address (includes hashed password).
        Mirrors Go's GetUserByEmail().
        Raises ValueError if not found.
        """
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        user = result.scalars().first()
        if user is None:
            raise ValueError(f"user with email '{email}' not found")
        return user

    async def get_user_by_user_id(self, user_id: int) -> UserModel:
        """
        Fetch a UserModel by primary key.
        Mirrors Go's GetUserByUserId().
        Raises ValueError if not found.
        """
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        user = result.scalars().first()
        if user is None:
            raise ValueError(f"user with id '{user_id}' not found")
        return user

    async def insert_oauth(self, response: UserLoginResponse) -> None:
        """
        Insert a brand-new token row.
        Mirrors Go's InsertOAuth().
        """
        token = UserTokenModel(
            user_id=response.user.id,
            access=response.token.access,
            refresh=response.token.refresh,
        )
        self._session.add(token)
        await self._session.flush()

    async def upsert_oauth(self, response: UserLoginResponse) -> None:
        """
        Update the token row for a user if it exists, otherwise insert.
        Mirrors Go's UpsertOAuth() — UPDATE ... WHERE user_id = ?,
        then CREATE if RowsAffected == 0.
        """
        result = await self._session.execute(
            select(UserTokenModel).where(UserTokenModel.user_id == response.user.id)
        )
        existing = result.scalars().first()

        if existing:
            existing.access = response.token.access
            existing.refresh = response.token.refresh
        else:
            self._session.add(
                UserTokenModel(
                    user_id=response.user.id,
                    access=response.token.access,
                    refresh=response.token.refresh,
                )
            )
        await self._session.flush()

    async def find_one_oauth_by_user_id(
        self, user_id: int
    ) -> UserTokenModel | None:
        """
        Return the token row with its joined User for the given user_id.
        Mirrors Go's FindOneOAuthByUserId() with .Joins("User").
        """
        result = await self._session.execute(
            select(UserTokenModel)
            .where(UserTokenModel.user_id == user_id)
            .join(UserTokenModel.user)  # eager-load the user relationship
        )
        return result.scalars().first()

    async def find_oauth_by_user_id_and_access_token(
        self, user_id: int, access_token: str
    ) -> UserTokenModel | None:
        """
        Return the token row where both user_id AND access token match.
        Used by the JWT middleware on every authenticated request.
        Mirrors Go's FindOAuthByUserIdAndAccessToken().
        """
        result = await self._session.execute(
            select(UserTokenModel)
            .where(
                UserTokenModel.user_id == user_id,
                UserTokenModel.access == access_token,
            )
            .join(UserTokenModel.user)
        )
        return result.scalars().first()

    async def delete_oauth_by_user_id(self, user_id: int) -> None:
        """
        Delete the token row for the given user (logout).
        Mirrors Go's DeleteOAuthByUserId().
        """
        await self._session.execute(
            delete(UserTokenModel).where(UserTokenModel.user_id == user_id)
        )
        await self._session.flush()

    async def get_user_permission_by_user_id(
        self, user_id: int
    ) -> UserPermissionModel | None:
        """
        Return the permission row for the given user, or None.
        Mirrors Go's GetUserPermissionByUserId().
        """
        result = await self._session.execute(
            select(UserPermissionModel).where(
                UserPermissionModel.user_id == user_id
            )
        )
        return result.scalars().first()
