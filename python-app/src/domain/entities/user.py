"""
User domain entities (pure data — no DB dependencies).

Mirrors Go:
  src/domain/entities/user/user.go     — UserEntity, UserTokenEntity, UserTokenClaimsEntity
  src/domain/entities/user/request.go  — UserRegisterRequest, UserLoginRequest, UserRefreshTokenRequest
  src/domain/entities/user/response.go — UserLoginResponse
"""
import re
from datetime import datetime

from pydantic import BaseModel, field_validator

# Matches Go's regexp: ^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$
_EMAIL_REGEX = re.compile(r"^[\w\-.]+@([\w\-]+\.)+[\w\-]{2,4}$")


# ---------------------------------------------------------------------------
# Core entity — returned to clients, password intentionally excluded
# ---------------------------------------------------------------------------

class UserEntity(BaseModel):
    """
    Public user representation.
    Mirrors Go's UserEntity — never includes the password field.
    """
    id: int
    email: str
    first_name: str
    last_name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Token entities
# ---------------------------------------------------------------------------

class UserTokenEntity(BaseModel):
    """Access + refresh token pair. Mirrors Go's UserTokenEntity."""
    access: str
    refresh: str


class UserTokenClaimsEntity(BaseModel):
    """
    Payload embedded inside every JWT under the "claims" key.
    Mirrors Go's UserTokenClaimsEntity — only carries the user id.
    """
    id: int


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class UserRegisterRequest(BaseModel):
    """
    Body for POST /api/v1/users/register.
    Mirrors Go's UserRegisterRequest (including IsEmail validation).
    """
    email: str
    password: str
    first_name: str
    last_name: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not _EMAIL_REGEX.match(v):
            raise ValueError("email pattern is invalid")
        return v


class UserLoginRequest(BaseModel):
    """Body for POST /api/v1/users/login. Mirrors Go's UserLoginRequest."""
    email: str
    password: str


class UserRefreshTokenRequest(BaseModel):
    """
    Body for POST /api/v1/users/logout and POST /api/v1/users/refresh-token.
    Mirrors Go's UserRefreshTokenRequest.
    """
    refresh_token: str


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class UserLoginResponse(BaseModel):
    """
    Response for login and refresh-token endpoints.
    Mirrors Go's UserLoginResponse.
    """
    user: UserEntity
    token: UserTokenEntity
