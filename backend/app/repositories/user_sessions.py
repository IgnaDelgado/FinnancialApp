from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_session import UserSession


class UserSessionRepository:
    """Persist and resolve server-side authentication sessions."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, user_session: UserSession) -> None:
        self._session.add(user_session)

    def get_active_with_user(
        self,
        *,
        token_hash: str,
        now: datetime,
    ) -> tuple[UserSession, User] | None:
        statement = (
            select(UserSession, User)
            .join(User, User.id == UserSession.user_id)
            .where(
                UserSession.token_hash == token_hash,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > now,
            )
        )
        row = self._session.execute(statement).one_or_none()
        if row is None:
            return None
        return row[0], row[1]
