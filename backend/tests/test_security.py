from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from app.core.config import get_settings
from app.core.security import (
    InvalidAccessTokenError,
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
    verify_password_or_dummy,
)


def test_hash_password_creates_verifiable_argon2id_hash() -> None:
    password = "synthetic passphrase 2026"

    password_hash = hash_password(password)

    assert password_hash != password
    assert password_hash.startswith("$argon2id$")
    assert verify_password(password, password_hash) is True
    assert verify_password("different synthetic passphrase", password_hash) is False


def test_verify_password_or_dummy_rejects_unknown_user() -> None:
    assert verify_password_or_dummy("synthetic passphrase", None) is False


def test_refresh_tokens_are_random_and_stored_as_sha256_hashes() -> None:
    first_token = generate_refresh_token()
    second_token = generate_refresh_token()

    assert first_token != second_token
    assert len(first_token) >= 43
    assert hash_refresh_token(first_token) != first_token
    assert len(hash_refresh_token(first_token)) == 64
    assert hash_refresh_token(first_token) == hash_refresh_token(first_token)


def test_access_jwt_contains_only_minimum_claims_and_is_verifiable() -> None:
    user_id = uuid4()
    token, expires_at = create_access_token(user_id)
    settings = get_settings()
    claims = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert set(claims) == {"sub", "iat", "exp", "type"}
    assert claims["sub"] == str(user_id)
    assert claims["type"] == "access"
    assert decode_access_token(token) == user_id
    assert expires_at > datetime.now(UTC)


def test_invalid_and_expired_access_jwts_are_rejected() -> None:
    user_id = uuid4()
    expired_token, _ = create_access_token(
        user_id,
        now=datetime.now(UTC) - timedelta(minutes=16),
    )

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token("not-a-jwt")
    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(expired_token)


def test_refresh_token_cannot_be_used_as_access_bearer() -> None:
    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(generate_refresh_token())
