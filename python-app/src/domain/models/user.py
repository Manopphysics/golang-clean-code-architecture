"""
SQLAlchemy ORM models — the DB-aware layer.

Mirrors Go: src/domain/models/user.go
Three tables: users, user_tokens, user_permissions (all PostgreSQL).

Go's pattern was to embed UserEntity inside UserModel and add Password.
Here we replicate that by keeping all public fields on UserModel and
never exposing password through the entity conversion.
"""
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.domain.entities.user import UserEntity


class Base(DeclarativeBase):
    """Shared declarative base — all models must inherit from this."""
    pass


# ---------------------------------------------------------------------------
# users
# ---------------------------------------------------------------------------

class UserModel(Base):
    """
    ORM model for the `users` table.
    Mirrors Go's UserModel — embeds UserEntity fields + adds Password.
    Password is never included in to_entity() output (json:"-" equivalent).
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False, server_default="")
    last_name: Mapped[str] = mapped_column(String, nullable=False, server_default="")
    password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    token: Mapped["UserTokenModel"] = relationship(
        "UserTokenModel",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    permission: Mapped["UserPermissionModel"] = relationship(
        "UserPermissionModel",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def to_entity(self) -> UserEntity:
        """
        Convert to the public UserEntity (no password).
        Mirrors Go's UserModel.ToEntity().
        """
        return UserEntity(
            id=self.id,
            email=self.email,
            first_name=self.first_name,
            last_name=self.last_name,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @staticmethod
    def datasource() -> str:
        """Mirrors Go's Datasource() — used by the CRUD factory."""
        return "postgresql"


# ---------------------------------------------------------------------------
# user_tokens
# ---------------------------------------------------------------------------

class UserTokenModel(Base):
    """
    ORM model for the `user_tokens` table.
    One row per user — upserted on every login / token refresh.
    Mirrors Go's UserTokenModel.
    """
    __tablename__ = "user_tokens"
    __table_args__ = (Index("ix_user_tokens_user_id", "user_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    access: Mapped[str] = mapped_column(String, nullable=False, server_default="")
    refresh: Mapped[str] = mapped_column(String, nullable=False, server_default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[UserModel] = relationship("UserModel", back_populates="token")

    @staticmethod
    def datasource() -> str:
        return "postgresql"


# ---------------------------------------------------------------------------
# user_permissions
# ---------------------------------------------------------------------------

class UserPermissionModel(Base):
    """
    ORM model for the `user_permissions` table.
    Mirrors Go's UserPermissionModel — permission is a free-form string.
    """
    __tablename__ = "user_permissions"
    __table_args__ = (Index("ix_user_permissions_user_id", "user_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    permission: Mapped[str] = mapped_column(String, nullable=False, server_default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[UserModel] = relationship("UserModel", back_populates="permission")

    @staticmethod
    def datasource() -> str:
        return "postgresql"
