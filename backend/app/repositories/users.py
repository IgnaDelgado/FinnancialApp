from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """Persist users without owning the surrounding transaction."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, user: User) -> None:
        self._session.add(user)
