from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_refresh_token,
    verify_password_or_dummy,
)
from app.models.user import User
from app.models.user_session import UserSession
from app.repositories.user_sessions import UserSessionRepository
from app.repositories.users import UserRepository


class InvalidCredentialsError(Exception):
    """Raised when login credentials cannot be authenticated."""


class InvalidRefreshTokenError(Exception):
    """Raised when a refresh token cannot authorize session renewal."""


class ReusedRefreshTokenError(InvalidRefreshTokenError):
    """Raised after reuse revokes the affected device-session family."""


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    access_expires_at: datetime
    refresh_token: str
    refresh_expires_at: datetime
    absolute_expires_at: datetime


class AuthenticationService:
    def __init__(
        self,
        session: Session,
        *,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._user_sessions = UserSessionRepository(session)
        self._now_provider = now_provider or (lambda: datetime.now(UTC))

    def login(self, *, email: str, password: str) -> TokenPair:
        user = self._users.get_by_email(email.strip().lower())
        stored_hash = user.password_hash if user is not None else None

        if not verify_password_or_dummy(password, stored_hash) or user is None:
            raise InvalidCredentialsError

        now = self._now_provider()
        settings = get_settings()
        absolute_expires_at = now + timedelta(
            days=settings.session_absolute_expire_days
        )
        refresh_expires_at = min(
            now + timedelta(days=settings.refresh_token_expire_days),
            absolute_expires_at,
        )
        refresh_token = generate_refresh_token()
        user_session = UserSession(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token),
            family_id=uuid4(),
            created_at=now,
            expires_at=refresh_expires_at,
            absolute_expires_at=absolute_expires_at,
        )
        self._user_sessions.add(user_session)
        access_token, access_expires_at = create_access_token(user.id, now=now)
        self._session.commit()

        return TokenPair(
            access_token=access_token,
            access_expires_at=access_expires_at,
            refresh_token=refresh_token,
            refresh_expires_at=refresh_expires_at,
            absolute_expires_at=absolute_expires_at,
        )

    def authenticate_access_token(self, access_token: str) -> User:
        user_id = decode_access_token(access_token)
        user = self._users.get_by_id(user_id)
        if user is None:
            raise InvalidCredentialsError
        return user

    def refresh(self, refresh_token: str) -> TokenPair:
        now = self._now_provider()
        token_hash = hash_refresh_token(refresh_token)
        current = self._user_sessions.get_by_token_hash_for_update(token_hash)

        if current is None:
            self._session.rollback()
            raise InvalidRefreshTokenError

        if current.replaced_by_session_id is not None:
            self._user_sessions.revoke_family(current.family_id, now=now)
            self._session.commit()
            raise ReusedRefreshTokenError

        if (
            current.revoked_at is not None
            or now >= current.expires_at
            or now >= current.absolute_expires_at
        ):
            self._session.rollback()
            raise InvalidRefreshTokenError

        settings = get_settings()
        refresh_expires_at = min(
            now + timedelta(days=settings.refresh_token_expire_days),
            current.absolute_expires_at,
        )
        new_refresh_token = generate_refresh_token()
        replacement = UserSession(
            user_id=current.user_id,
            token_hash=hash_refresh_token(new_refresh_token),
            family_id=current.family_id,
            created_at=now,
            expires_at=refresh_expires_at,
            absolute_expires_at=current.absolute_expires_at,
        )
        self._user_sessions.add(replacement)
        self._session.flush()
        current.revoked_at = now
        current.replaced_by_session_id = replacement.id
        access_token, access_expires_at = create_access_token(
            current.user_id,
            now=now,
        )
        self._session.commit()

        return TokenPair(
            access_token=access_token,
            access_expires_at=access_expires_at,
            refresh_token=new_refresh_token,
            refresh_expires_at=refresh_expires_at,
            absolute_expires_at=current.absolute_expires_at,
        )

    def logout(self, *, user_id: UUID, refresh_token: str) -> None:
        now = self._now_provider()
        current = self._user_sessions.get_by_token_hash_for_update(
            hash_refresh_token(refresh_token)
        )
        if (
            current is None
            or current.user_id != user_id
            or current.revoked_at is not None
        ):
            self._session.rollback()
            raise InvalidRefreshTokenError
        current.revoked_at = now
        self._session.commit()

    def logout_all(self, user_id: UUID) -> None:
        self._user_sessions.revoke_all_for_user(
            user_id,
            now=self._now_provider(),
        )
        self._session.commit()
