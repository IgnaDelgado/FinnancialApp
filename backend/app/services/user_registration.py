from psycopg.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.domain.currency import Currency
from app.models.user import User
from app.repositories.users import UserRepository


class EmailAlreadyRegisteredError(Exception):
    """Raised when registration conflicts with an existing email."""


class UserRegistrationService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._users = UserRepository(session)

    def register(
        self,
        *,
        email: str,
        password: str,
        reference_currency: Currency,
    ) -> User:
        user = User(
            email=email.strip().lower(),
            password_hash=hash_password(password),
            reference_currency=reference_currency,
        )
        self._users.add(user)

        try:
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            if isinstance(exc.orig, UniqueViolation):
                raise EmailAlreadyRegisteredError from exc
            raise

        self._session.refresh(user)
        return user
