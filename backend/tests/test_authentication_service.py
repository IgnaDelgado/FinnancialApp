from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.database import get_engine
from app.core.security import decode_access_token, hash_refresh_token
from app.domain.currency import Currency
from app.models.user import User
from app.models.user_session import UserSession
from app.services.authentication import (
    AuthenticationService,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    ReusedRefreshTokenError,
)
from app.services.user_registration import UserRegistrationService

PASSWORD = "synthetic passphrase 2026"


def fixed_now(moment: datetime) -> Callable[[], datetime]:
    return lambda: moment


def register_test_user(
    database_session: Session,
    *,
    email: str = "authenticated@example.com",
) -> User:
    return UserRegistrationService(database_session).register(
        email=email,
        password=PASSWORD,
        reference_currency=Currency.ARS,
    )


def test_login_creates_jwt_and_persists_only_refresh_token_hash(
    database_session: Session,
) -> None:
    user = register_test_user(database_session)
    now = datetime.now(UTC).replace(microsecond=0)

    result = AuthenticationService(
        database_session,
        now_provider=lambda: now,
    ).login(email="  AUTHENTICATED@example.com  ", password=PASSWORD)
    persisted = database_session.scalar(select(UserSession))

    assert persisted is not None
    assert decode_access_token(result.access_token) == user.id
    assert persisted.token_hash == hash_refresh_token(result.refresh_token)
    assert persisted.token_hash != result.refresh_token
    assert result.refresh_expires_at == now + timedelta(days=20)
    assert result.absolute_expires_at == now + timedelta(days=90)
    assert result.access_expires_at == now + timedelta(minutes=15)


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("unknown@example.com", PASSWORD),
        ("authenticated@example.com", "incorrect synthetic passphrase"),
    ],
)
def test_login_rejects_invalid_credentials_with_same_error(
    database_session: Session,
    email: str,
    password: str,
) -> None:
    register_test_user(database_session)

    with pytest.raises(InvalidCredentialsError):
        AuthenticationService(database_session).login(
            email=email,
            password=password,
        )


def test_refresh_rotates_token_and_extends_sliding_expiration(
    database_session: Session,
) -> None:
    register_test_user(database_session)
    login_at = datetime.now(UTC).replace(microsecond=0)
    login = AuthenticationService(
        database_session,
        now_provider=lambda: login_at,
    ).login(email="authenticated@example.com", password=PASSWORD)
    first_session = database_session.scalar(select(UserSession))
    assert first_session is not None

    refresh_at = login_at + timedelta(days=10)
    refreshed = AuthenticationService(
        database_session,
        now_provider=lambda: refresh_at,
    ).refresh(login.refresh_token)
    sessions = database_session.scalars(
        select(UserSession).order_by(UserSession.created_at)
    ).all()

    assert refreshed.refresh_token != login.refresh_token
    assert refreshed.access_token != login.access_token
    assert refreshed.refresh_expires_at == refresh_at + timedelta(days=20)
    assert refreshed.absolute_expires_at == login.absolute_expires_at
    assert sessions[0].revoked_at == refresh_at
    assert sessions[0].replaced_by_session_id == sessions[1].id
    assert sessions[0].family_id == sessions[1].family_id
    assert sessions[1].token_hash == hash_refresh_token(refreshed.refresh_token)


def test_reusing_rotated_refresh_token_revokes_entire_family(
    database_session: Session,
) -> None:
    register_test_user(database_session)
    login_at = datetime.now(UTC).replace(microsecond=0)
    login = AuthenticationService(
        database_session,
        now_provider=lambda: login_at,
    ).login(email="authenticated@example.com", password=PASSWORD)
    refresh_at = login_at + timedelta(days=1)
    AuthenticationService(
        database_session,
        now_provider=lambda: refresh_at,
    ).refresh(login.refresh_token)

    with pytest.raises(ReusedRefreshTokenError):
        AuthenticationService(
            database_session,
            now_provider=lambda: refresh_at + timedelta(seconds=1),
        ).refresh(login.refresh_token)

    sessions = database_session.scalars(select(UserSession)).all()
    assert len(sessions) == 2
    assert all(item.revoked_at is not None for item in sessions)


def test_refresh_rejects_expired_token_at_twenty_days(
    database_session: Session,
) -> None:
    register_test_user(database_session)
    login_at = datetime.now(UTC).replace(microsecond=0)
    login = AuthenticationService(
        database_session,
        now_provider=lambda: login_at,
    ).login(email="authenticated@example.com", password=PASSWORD)

    with pytest.raises(InvalidRefreshTokenError):
        AuthenticationService(
            database_session,
            now_provider=lambda: login_at + timedelta(days=20),
        ).refresh(login.refresh_token)


def test_sliding_expiration_never_exceeds_absolute_expiration(
    database_session: Session,
) -> None:
    register_test_user(database_session)
    login_at = datetime.now(UTC).replace(microsecond=0)
    result = AuthenticationService(
        database_session,
        now_provider=lambda: login_at,
    ).login(email="authenticated@example.com", password=PASSWORD)
    original_absolute_expiration = result.absolute_expires_at

    for elapsed_days in (19, 38, 57, 76, 85):
        refresh_time = login_at + timedelta(days=elapsed_days)
        result = AuthenticationService(
            database_session,
            now_provider=fixed_now(refresh_time),
        ).refresh(result.refresh_token)

    assert result.refresh_expires_at == original_absolute_expiration
    assert result.absolute_expires_at == original_absolute_expiration

    with pytest.raises(InvalidRefreshTokenError):
        AuthenticationService(
            database_session,
            now_provider=lambda: original_absolute_expiration,
        ).refresh(result.refresh_token)


def test_logout_revokes_only_supplied_device_and_logout_all_revokes_every_device(
    database_session: Session,
) -> None:
    user = register_test_user(database_session)
    service = AuthenticationService(database_session)
    first = service.login(email=user.email, password=PASSWORD)
    second = service.login(email=user.email, password=PASSWORD)

    service.logout(first.refresh_token)
    with pytest.raises(InvalidRefreshTokenError):
        service.refresh(first.refresh_token)
    second_rotated = service.refresh(second.refresh_token)
    service.logout_all(user.id)
    with pytest.raises(InvalidRefreshTokenError):
        service.refresh(second_rotated.refresh_token)


def test_deleting_user_cascades_to_refresh_sessions(
    database_session: Session,
) -> None:
    user = register_test_user(database_session)
    AuthenticationService(database_session).login(email=user.email, password=PASSWORD)

    database_session.delete(user)
    database_session.commit()

    assert database_session.scalar(select(UserSession)) is None


def test_concurrent_refresh_requests_cannot_create_two_valid_replacements() -> None:
    unique = uuid4().hex
    email = f"concurrent-{unique}@example.com"
    engine = get_engine()
    with Session(engine) as setup_session:
        user = register_test_user(setup_session, email=email)
        user_id = user.id
        login = AuthenticationService(setup_session).login(
            email=email,
            password=PASSWORD,
        )
    start_together = Barrier(2)

    def rotate() -> str:
        with Session(engine) as worker_session:
            start_together.wait()
            try:
                AuthenticationService(worker_session).refresh(login.refresh_token)
            except ReusedRefreshTokenError:
                return "reuse-detected"
            return "rotated"

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(lambda _index: rotate(), range(2)))

        assert sorted(outcomes) == ["reuse-detected", "rotated"]
        with Session(engine) as verification_session:
            sessions = verification_session.scalars(
                select(UserSession).where(UserSession.user_id == user_id)
            ).all()
            assert len(sessions) == 2
            assert all(item.revoked_at is not None for item in sessions)
    finally:
        with Session(engine) as cleanup_session:
            cleanup_session.execute(delete(User).where(User.id == user_id))
            cleanup_session.commit()
