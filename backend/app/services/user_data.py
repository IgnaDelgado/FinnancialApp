from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User
from app.repositories.user_data import UserDataRepository
from app.services.authentication import InvalidCredentialsError


class UserDataService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def export(self, user_id: UUID) -> dict[str, object]:
        return UserDataRepository(self._session).export(user_id)

    def delete(self, user_id: UUID, password: str) -> None:
        user = self._session.scalar(
            select(User).where(User.id == user_id).with_for_update()
        )
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError
        # One root DELETE lets PostgreSQL cascade owned financial records and
        # sessions atomically, including archived accounts and audit events.
        self._session.execute(delete(User).where(User.id == user_id))
        self._session.commit()
