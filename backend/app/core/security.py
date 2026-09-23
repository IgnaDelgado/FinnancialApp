from pwdlib import PasswordHash

_password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Create an Argon2id password hash with the recommended parameters."""

    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a candidate password against a stored hash."""

    return _password_hash.verify(password, password_hash)
