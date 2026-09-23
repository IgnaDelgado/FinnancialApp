import hashlib
import secrets

from pwdlib import PasswordHash

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


def generate_session_token() -> str:
    """Generate a URL-safe session token with 256 bits of entropy."""

    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """Create the irreversible database lookup value for a session token."""

    return hashlib.sha256(token.encode("utf-8")).hexdigest()
