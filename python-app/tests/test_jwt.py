"""Tests for src/shared/authentication/jwt.py."""
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from jose import jwt as jose_jwt

from src.shared.authentication.jwt import (
    ALGORITHM,
    AUDIENCES,
    ParsedToken,
    create_access_token,
    create_refresh_token,
    parse_token,
    repeat_token,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_secret() -> str:
    from src.config import get_settings
    return get_settings().secret_key


def _make_expired_token(user_id: int) -> str:
    """Produce a JWT that is already expired."""
    secret = _get_secret()
    payload = {
        "claims": {"id": user_id},
        "iss": "test app",
        "sub": "access-token",
        "aud": AUDIENCES,
        "exp": datetime.now(tz=UTC) - timedelta(seconds=1),
        "nbf": datetime.now(tz=UTC) - timedelta(seconds=10),
        "iat": datetime.now(tz=UTC) - timedelta(seconds=10),
    }
    return jose_jwt.encode(payload, secret, algorithm=ALGORITHM)


def _make_bad_audience_token(user_id: int) -> str:
    """Produce a JWT with a non-matching audience."""
    secret = _get_secret()
    payload = {
        "claims": {"id": user_id},
        "iss": "test app",
        "sub": "access-token",
        "aud": ["nobody"],
        "exp": datetime.now(tz=UTC) + timedelta(hours=1),
        "nbf": datetime.now(tz=UTC),
        "iat": datetime.now(tz=UTC),
    }
    return jose_jwt.encode(payload, secret, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# create_access_token
# ---------------------------------------------------------------------------

class TestCreateAccessToken:
    def test_returns_string(self):
        token = create_access_token(42)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_subject_is_access_token(self):
        token = create_access_token(1)
        parsed = parse_token(token)
        assert parsed.subject == "access-token"

    def test_user_id_encoded(self):
        token = create_access_token(99)
        parsed = parse_token(token)
        assert parsed.user_id == 99

    def test_expiry_is_in_future(self):
        token = create_access_token(1)
        parsed = parse_token(token)
        assert parsed.expires_at > datetime.now(tz=UTC)

    def test_different_users_produce_different_tokens(self):
        t1 = create_access_token(1)
        t2 = create_access_token(2)
        assert t1 != t2


# ---------------------------------------------------------------------------
# create_refresh_token
# ---------------------------------------------------------------------------

class TestCreateRefreshToken:
    def test_returns_string(self):
        token = create_refresh_token(1)
        assert isinstance(token, str)

    def test_subject_is_refresh_token(self):
        token = create_refresh_token(1)
        parsed = parse_token(token)
        assert parsed.subject == "refresh-token"

    def test_user_id_encoded(self):
        token = create_refresh_token(7)
        parsed = parse_token(token)
        assert parsed.user_id == 7

    def test_refresh_expires_later_than_access(self):
        acc = create_access_token(1)
        ref = create_refresh_token(1)
        acc_exp = parse_token(acc).expires_at
        ref_exp = parse_token(ref).expires_at
        assert ref_exp > acc_exp


# ---------------------------------------------------------------------------
# repeat_token
# ---------------------------------------------------------------------------

class TestRepeatToken:
    def test_preserves_original_expiry(self):
        original_exp = datetime(2030, 6, 15, 12, 0, 0, tzinfo=UTC)
        token = repeat_token(user_id=3, original_exp=original_exp)
        parsed = parse_token(token)
        # The exp in the JWT is stored as a Unix timestamp (int) and may lose
        # sub-second precision — compare to within 1 second.
        diff = abs((parsed.expires_at - original_exp).total_seconds())
        assert diff < 1.0

    def test_subject_is_refresh_token(self):
        exp = datetime(2030, 1, 1, tzinfo=UTC)
        token = repeat_token(1, exp)
        parsed = parse_token(token)
        assert parsed.subject == "refresh-token"

    def test_does_not_extend_expiry(self):
        """repeat_token must use the supplied expiry, not now+refresh_expires."""
        original_exp = datetime(2030, 1, 1, tzinfo=UTC)
        token = repeat_token(user_id=5, original_exp=original_exp)
        parsed = parse_token(token)
        assert parsed.expires_at.year == 2030


# ---------------------------------------------------------------------------
# parse_token
# ---------------------------------------------------------------------------

class TestParseToken:
    def test_happy_path(self):
        token = create_access_token(10)
        parsed = parse_token(token)
        assert parsed.user_id == 10

    def test_expired_token_raises(self):
        token = _make_expired_token(1)
        with pytest.raises(ValueError, match="token had expired"):
            parse_token(token)

    def test_wrong_secret_raises(self):
        # Encode with a different secret
        payload = {
            "claims": {"id": 1},
            "iss": "test",
            "sub": "access-token",
            "aud": AUDIENCES,
            "exp": datetime.now(tz=UTC) + timedelta(hours=1),
            "nbf": datetime.now(tz=UTC),
            "iat": datetime.now(tz=UTC),
        }
        bad_token = jose_jwt.encode(payload, "wrongsecret", algorithm=ALGORITHM)
        with pytest.raises(ValueError):
            parse_token(bad_token)

    def test_bad_audience_raises(self):
        token = _make_bad_audience_token(1)
        with pytest.raises(ValueError, match="token format is invalid"):
            parse_token(token)

    def test_garbage_string_raises(self):
        with pytest.raises(ValueError):
            parse_token("not.a.jwt")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            parse_token("")


# ---------------------------------------------------------------------------
# ParsedToken
# ---------------------------------------------------------------------------

class TestParsedToken:
    def test_user_id_property(self):
        raw = {"claims": {"id": 42}, "sub": "access-token", "exp": 9999999999}
        pt = ParsedToken(raw)
        assert pt.user_id == 42

    def test_subject_property(self):
        raw = {"claims": {"id": 1}, "sub": "refresh-token", "exp": 9999999999}
        pt = ParsedToken(raw)
        assert pt.subject == "refresh-token"

    def test_subject_defaults_to_empty_string(self):
        raw = {"claims": {"id": 1}, "exp": 9999999999}
        pt = ParsedToken(raw)
        assert pt.subject == ""

    def test_expires_at_from_int(self):
        future_ts = int((datetime.now(tz=UTC) + timedelta(hours=1)).timestamp())
        raw = {"claims": {"id": 1}, "sub": "x", "exp": future_ts}
        pt = ParsedToken(raw)
        assert pt.expires_at.tzinfo is not None
        assert pt.expires_at > datetime.now(tz=UTC)

    def test_expires_at_from_datetime(self):
        future_dt = datetime(2035, 1, 1, tzinfo=UTC)
        raw = {"claims": {"id": 1}, "sub": "x", "exp": future_dt}
        pt = ParsedToken(raw)
        assert pt.expires_at == future_dt

    def test_expires_at_from_naive_datetime_adds_utc(self):
        naive_dt = datetime(2035, 1, 1)  # no tzinfo
        raw = {"claims": {"id": 1}, "sub": "x", "exp": naive_dt}
        pt = ParsedToken(raw)
        assert pt.expires_at.tzinfo is not None

    def test_raw_property(self):
        raw = {"claims": {"id": 1}, "exp": 0}
        pt = ParsedToken(raw)
        assert pt.raw is raw
