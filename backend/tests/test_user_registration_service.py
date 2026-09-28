import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.domain.currency import Currency
from app.models.user import User
from app.services.user_registration import (
    EmailAlreadyRegisteredError,
    UserRegistrationService,
)


def test_register_user_normalizes_email_and_hashes_password(
    database_session: Session,
) -> None:
    password = "synthetic passphrase 2026"
    service = UserRegistrationService(database_session)

    user = service.register(
        email="  Learner@Example.com  ",
        password=password,
        reference_currency=Currency.USD,
    )

    persisted_user = database_session.scalar(select(User).where(User.id == user.id))
    assert persisted_user is not None
    assert persisted_user.email == "learner@example.com"
    assert persisted_user.reference_currency is Currency.USD
    assert persisted_user.password_hash != password
    assert verify_password(password, persisted_user.password_hash) is True


def test_register_user_rejects_duplicate_normalized_email(
    database_session: Session,
) -> None:
    service = UserRegistrationService(database_session)
    first_password = "first synthetic passphrase"

    service.register(
        email="duplicate@example.com",
        password=first_password,
        reference_currency=Currency.ARS,
    )

    with pytest.raises(EmailAlreadyRegisteredError):
        service.register(
            email="DUPLICATE@example.com",
            password="second synthetic passphrase",
            reference_currency=Currency.ARS,
        )

    users = database_session.scalars(select(User)).all()
    assert len(users) == 1
    assert verify_password(first_password, users[0].password_hash) is True
