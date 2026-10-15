"""
JWT authentication utilities.

Mirrors Go: src/shared/authentication/JWTAuthentication.go

Design decisions that match the Go implementation:
  - Algorithm: HS256
  - Claims structure: { "claims": { "id": int }, ...standard_claims }
  - Access token  subject: "access-token"
  - Refresh token subject: "refresh-token"
  - Audiences: ["user", "admin"]
  - RepeatToken re-signs a refresh token preserving its original expiry

Bug fixed vs Go:
  - Go's newRefreshToken() read JWT_ACCESS_EXPIRES instead of
    JWT_REFRESH_EXPIRES. This implementation uses the correct value.
"""
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from jose import JWTError, jwt

from src.config import get_settings

_settings = get_settings()

ALGORITHM = "HS256"
AUDIENCES = ["user", "admin"]


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_payload(
    subject: str,
    user_id: int,
    expires_at: datetime,
) -> dict[str, Any]:
    """
    Build the JWT payload dict that matches Go's jwtMapClaims structure:
      { "claims": { "id": user_id }, ...registered_claims }
    """
    now = datetime.now(tz=UTC)
    return {
        "claims": {"id": user_id},   # custom claims — nested under "claims" key
        "iss": _settings.app_issuer,
        "sub": subject,
        "aud": AUDIENCES,
        "exp": expires_at,
        "nbf": now,
        "iat": now,
    }


# ---------------------------------------------------------------------------
# Token creation
# ---------------------------------------------------------------------------

def create_access_token(user_id: int) -> str:
    """
    Issue a new access token.
    Mirrors Go's newAccessToken().
    Expiry: JWT_ACCESS_EXPIRES seconds from now.
    """
    expires_at = datetime.now(tz=UTC) + timedelta(
        seconds=_settings.jwt_access_expires
    )
    payload = _build_payload("access-token", user_id, expires_at)
    return jwt.encode(payload, _settings.secret_key, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """
    Issue a new refresh token.
    Mirrors Go's newRefreshToken() — correctly uses JWT_REFRESH_EXPIRES
    (Go had a bug here, using JWT_ACCESS_EXPIRES instead).
    Expiry: JWT_REFRESH_EXPIRES seconds from now.
    """
    expires_at = datetime.now(tz=UTC) + timedelta(
        seconds=_settings.jwt_refresh_expires
    )
    payload = _build_payload("refresh-token", user_id, expires_at)
    return jwt.encode(payload, _settings.secret_key, algorithm=ALGORITHM)


def repeat_token(user_id: int, original_exp: datetime) -> str:
    """
    Re-sign a refresh token preserving its original expiry timestamp.
    Used during token refresh — the refresh window never extends.
    Mirrors Go's RepeatToken().
    """
    payload = _build_payload("refresh-token", user_id, original_exp)
    return jwt.encode(payload, _settings.secret_key, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# Token parsing
# ---------------------------------------------------------------------------

class ParsedToken:
    """Wraps the decoded JWT payload and exposes typed accessors."""

    def __init__(self, raw: dict[str, Any]) -> None:
        self._raw = raw

    @property
    def user_id(self) -> int:
        return int(self._raw["claims"]["id"])

    @property
    def subject(self) -> str:
        return str(self._raw.get("sub", ""))

    @property
    def expires_at(self) -> datetime:
        """Return the token expiry as a timezone-aware datetime."""
        exp = self._raw["exp"]
        if isinstance(exp, int | float):
            return datetime.fromtimestamp(float(exp), tz=UTC)
        # python-jose may have already parsed it to a datetime
        if isinstance(exp, datetime):
            return exp if exp.tzinfo else exp.replace(tzinfo=UTC)
        return datetime.now(tz=UTC)

    @property
    def raw(self) -> dict[str, Any]:
        return self._raw


def parse_token(token_string: str) -> ParsedToken:
    """
    Decode and fully validate a JWT string (signature + expiry + audience).
    Raises ValueError with a descriptive message on any failure.
    Mirrors Go's ParseToken().

    Note: python-jose doesn't support multi-value audience validation
    directly, so we decode without audience then verify manually.
    """
    try:
        # Decode without audience check first (jose limitation with list audiences)
        payload = jwt.decode(
            token_string,
            _settings.secret_key,
            algorithms=[ALGORITHM],
            options={"verify_aud": False},
        )
    except JWTError as exc:
        msg = str(exc).lower()
        if "expired" in msg:
            raise ValueError("token had expired") from exc
        if "invalid" in msg or "malformed" in msg:
            raise ValueError("token format is invalid") from exc
        raise ValueError(f"parse token failed: {exc}") from exc

    # Manually validate audience — at least one must match
    token_aud = payload.get("aud", [])
    if isinstance(token_aud, str):
        token_aud = [token_aud]
    if not any(a in AUDIENCES for a in token_aud):
        raise ValueError("token format is invalid")

    return ParsedToken(payload)
