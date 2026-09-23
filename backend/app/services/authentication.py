from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    generate_session_token,
    hash_session_token,
    verify_password_or_dummy,
)
from app.models.user import User
from app.models.user_session import UserSession
from app.repositories.user_sessions import UserSessionRepository
from app.repositories.users import UserRepository


class InvalidCredentialsError(Exception):
    """Raised when login credentials cannot be authenticated."""


class InvalidSessionError(Exception):
    """Raised when a session token is missing, expired, or revoked."""


@dataclass(frozen=True)
class LoginResult:
    access_token: str
    expires_at: datetime


@dataclass(frozen=True)
class AuthenticatedSession:
    user: User
    user_session: UserSession


class AuthenticationService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._user_sessions = UserSessionRepository(session)

    def login(self, *, email: str, password: str) -> LoginResult:
        user = self._users.get_by_email(email.strip().lower())
        stored_hash = user.password_hash if user is not None else None

        if not verify_password_or_dummy(password, stored_hash) or user is None:
            raise InvalidCredentialsError

        now = datetime.now(UTC)
        expires_at = now + timedelta(days=get_settings().session_lifetime_days)
        access_token = generate_session_token()
        user_session = UserSession(
            user_id=user.id,
            token_hash=hash_session_token(access_token),
            expires_at=expires_at,
        )
        self._user_sessions.add(user_session)
        self._session.commit()

        return LoginResult(access_token=access_token, expires_at=expires_at)

    def authenticate(self, access_token: str) -> AuthenticatedSession:
        now = datetime.now(UTC)
        result = self._user_sessions.get_active_with_user(
            token_hash=hash_session_token(access_token),
            now=now,
        )
        if result is None:
            raise InvalidSessionError

        user_session, user = result
        return AuthenticatedSession(user=user, user_session=user_session)

    def logout(self, authenticated_session: AuthenticatedSession) -> None:
        authenticated_session.user_session.revoked_at = datetime.now(UTC)
        self._session.commit()
