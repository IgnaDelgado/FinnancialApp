from app.core.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
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


def test_session_tokens_are_random_and_stored_as_hashes() -> None:
    first_token = generate_session_token()
    second_token = generate_session_token()

    assert first_token != second_token
    assert len(first_token) >= 43
    assert hash_session_token(first_token) != first_token
    assert len(hash_session_token(first_token)) == 64
    assert hash_session_token(first_token) == hash_session_token(first_token)
