from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_session_token
from app.domain.currency import Currency
from app.models.user_session import UserSession
from app.services.authentication import (
    AuthenticationService,
    InvalidCredentialsError,
    InvalidSessionError,
)
from app.services.user_registration import UserRegistrationService


def register_test_user(database_session: Session) -> None:
    UserRegistrationService(database_session).register(
        email="authenticated@example.com",
        password="synthetic passphrase 2026",
        reference_currency=Currency.ARS,
    )


def test_login_persists_only_session_token_hash(
    database_session: Session,
) -> None:
    register_test_user(database_session)
    service = AuthenticationService(database_session)

    result = service.login(
        email="  AUTHENTICATED@example.com  ",
        password="synthetic passphrase 2026",
    )

    persisted_session = database_session.scalar(select(UserSession))
    assert persisted_session is not None
    assert persisted_session.token_hash == hash_session_token(result.access_token)
    assert persisted_session.token_hash != result.access_token
    assert result.expires_at > datetime.now(UTC)


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("missing@example.com", "synthetic passphrase 2026"),
        ("authenticated@example.com", "incorrect synthetic passphrase"),
    ],
)
def test_login_rejects_invalid_credentials_with_same_error(
    database_session: Session,
    email: str,
    password: str,
) -> None:
    register_test_user(database_session)
    service = AuthenticationService(database_session)

    with pytest.raises(InvalidCredentialsError):
        service.login(email=email, password=password)


def test_logout_revokes_session_immediately(database_session: Session) -> None:
    register_test_user(database_session)
    service = AuthenticationService(database_session)
    login = service.login(
        email="authenticated@example.com",
        password="synthetic passphrase 2026",
    )
    authenticated_session = service.authenticate(login.access_token)

    service.logout(authenticated_session)

    assert authenticated_session.user_session.revoked_at is not None
    with pytest.raises(InvalidSessionError):
        service.authenticate(login.access_token)


def test_authenticate_rejects_expired_session(database_session: Session) -> None:
    register_test_user(database_session)
    service = AuthenticationService(database_session)
    login = service.login(
        email="authenticated@example.com",
        password="synthetic passphrase 2026",
    )
    persisted_session = database_session.scalar(select(UserSession))
    assert persisted_session is not None
    persisted_session.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    database_session.commit()

    with pytest.raises(InvalidSessionError):
        service.authenticate(login.access_token)


def test_deleting_user_cascades_to_user_sessions(
    database_session: Session,
) -> None:
    register_test_user(database_session)
    service = AuthenticationService(database_session)
    login = service.login(
        email="authenticated@example.com",
        password="synthetic passphrase 2026",
    )
    authenticated_session = service.authenticate(login.access_token)

    database_session.delete(authenticated_session.user)
    database_session.commit()

    assert database_session.scalar(select(UserSession)) is None
