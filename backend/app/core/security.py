import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import get_settings

_password_hash = PasswordHash.recommended()
_dummy_password_hash = _password_hash.hash("not a real account password")


def hash_password(password: str) -> str:
    """Create an Argon2id password hash with the recommended parameters."""

    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a candidate password against a stored hash."""

    return _password_hash.verify(password, password_hash)


def verify_password_or_dummy(password: str, password_hash: str | None) -> bool:
    """Always perform Argon2 verification, including for an unknown user."""

    is_valid = verify_password(password, password_hash or _dummy_password_hash)
    return password_hash is not None and is_valid


class InvalidAccessTokenError(Exception):
    """Raised when an access JWT cannot authenticate a request."""


def generate_refresh_token() -> str:
    """Generate a URL-safe refresh token with 256 bits of entropy."""

    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    """Create the fixed-size database lookup value for a random refresh token."""

    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(
    user_id: UUID,
    *,
    now: datetime | None = None,
) -> tuple[str, datetime]:
    """Create a short-lived access JWT containing only authentication claims."""

    issued_at = now or datetime.now(UTC)
    settings = get_settings()
    expires_at = issued_at + timedelta(minutes=settings.access_token_expire_minutes)
    token = jwt.encode(
        {
            "sub": str(user_id),
            "iat": issued_at.timestamp(),
            "exp": expires_at.timestamp(),
            "type": "access",
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return token, expires_at


def decode_access_token(token: str) -> UUID:
    """Verify an access JWT and return its user identifier."""

    settings = get_settings()
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "iat", "exp", "type"]},
        )
        if claims["type"] != "access":
            raise InvalidAccessTokenError
        return UUID(claims["sub"])
    except (InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise InvalidAccessTokenError from exc
