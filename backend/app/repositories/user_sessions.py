from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.user_session import UserSession


class UserSessionRepository:
    """Persist and lock rotating refresh-token sessions."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, user_session: UserSession) -> None:
        self._session.add(user_session)

    def get_by_token_hash_for_update(self, token_hash: str) -> UserSession | None:
        statement = (
            select(UserSession)
            .where(UserSession.token_hash == token_hash)
            .with_for_update()
        )
        return self._session.scalar(statement)

    def revoke_family(self, family_id: UUID, *, now: datetime) -> None:
        statement = (
            update(UserSession)
            .where(
                UserSession.family_id == family_id,
                UserSession.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        self._session.execute(statement)

    def revoke_all_for_user(self, user_id: UUID, *, now: datetime) -> None:
        statement = (
            update(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        self._session.execute(statement)
