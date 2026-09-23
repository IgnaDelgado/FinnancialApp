from app.core.security import hash_password, verify_password


def test_hash_password_creates_verifiable_argon2id_hash() -> None:
    password = "synthetic passphrase 2026"

    password_hash = hash_password(password)

    assert password_hash != password
    assert password_hash.startswith("$argon2id$")
    assert verify_password(password, password_hash) is True
    assert verify_password("different synthetic passphrase", password_hash) is False
