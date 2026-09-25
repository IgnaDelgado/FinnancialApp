from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_refresh_token
from app.models.user import User
from app.models.user_session import UserSession

PASSWORD = "synthetic passphrase 2026"


def register_and_login(
    api_client: TestClient,
    email: str = "flow@example.com",
) -> dict[str, str]:
    registration = api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD},
    )
    assert registration.status_code == 201
    login = api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": PASSWORD},
    )
    assert login.status_code == 200
    return login.json()  # type: ignore[no-any-return]


def bearer(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def test_login_returns_token_pair_and_valid_access_authenticates_locally(
    api_client: TestClient,
    database_session: Session,
) -> None:
    tokens = register_and_login(api_client)
    current_user = api_client.get(
        "/api/v1/auth/me",
        headers=bearer(tokens["access_token"]),
    )
    persisted = database_session.scalar(select(UserSession))

    assert current_user.status_code == 200
    assert current_user.json()["email"] == "flow@example.com"
    assert tokens["token_type"] == "bearer"
    assert persisted is not None
    assert tokens["refresh_token"] not in persisted.token_hash
    assert persisted.token_hash == hash_refresh_token(tokens["refresh_token"])

    database_session.delete(persisted)
    database_session.commit()
    still_authenticated = api_client.get(
        "/api/v1/auth/me",
        headers=bearer(tokens["access_token"]),
    )
    assert still_authenticated.status_code == 200


def test_login_returns_same_error_for_unknown_user_and_wrong_password(
    api_client: TestClient,
) -> None:
    register_and_login(api_client, "known@example.com")
    unknown = api_client.post(
        "/api/v1/auth/login",
        json={"email": "unknown@example.com", "password": PASSWORD},
    )
    wrong = api_client.post(
        "/api/v1/auth/login",
        json={"email": "known@example.com", "password": "incorrect password"},
    )

    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json() == {"detail": "Invalid email or password"}


def test_invalid_expired_and_refresh_bearer_tokens_are_rejected(
    api_client: TestClient,
    database_session: Session,
) -> None:
    tokens = register_and_login(api_client)
    user = database_session.scalar(select(User).where(User.email == "flow@example.com"))
    assert user is not None
    expired, _ = create_access_token(
        user.id,
        now=datetime.now(UTC) - timedelta(minutes=16),
    )

    for token in ("not-a-jwt", expired, tokens["refresh_token"]):
        response = api_client.get("/api/v1/auth/me", headers=bearer(token))
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"


def test_refresh_endpoint_rotates_both_tokens_and_reuse_revokes_family(
    api_client: TestClient,
    database_session: Session,
) -> None:
    first = register_and_login(api_client)
    response = api_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": first["refresh_token"]},
    )
    second = response.json()

    assert response.status_code == 200
    assert second["access_token"] != first["access_token"]
    assert second["refresh_token"] != first["refresh_token"]

    reused = api_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": first["refresh_token"]},
    )
    sessions = database_session.scalars(select(UserSession)).all()
    assert reused.status_code == 401
    assert all(item.revoked_at is not None for item in sessions)


def test_logout_revokes_one_device_without_affecting_another(
    api_client: TestClient,
    database_session: Session,
) -> None:
    first = register_and_login(api_client)
    second_login = api_client.post(
        "/api/v1/auth/login",
        json={"email": "flow@example.com", "password": PASSWORD},
    ).json()
    logout = api_client.post(
        "/api/v1/auth/logout",
        headers=bearer(first["access_token"]),
        json={"refresh_token": first["refresh_token"]},
    )

    assert logout.status_code == 204
    assert (
        api_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": first["refresh_token"]},
        ).status_code
        == 401
    )
    assert (
        api_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": second_login["refresh_token"]},
        ).status_code
        == 200
    )
    sessions = database_session.scalars(select(UserSession)).all()
    assert sum(item.revoked_at is None for item in sessions) == 1


def test_logout_all_revokes_all_refresh_sessions(
    api_client: TestClient,
    database_session: Session,
) -> None:
    first = register_and_login(api_client)
    second = api_client.post(
        "/api/v1/auth/login",
        json={"email": "flow@example.com", "password": PASSWORD},
    ).json()
    response = api_client.post(
        "/api/v1/auth/logout-all",
        headers=bearer(first["access_token"]),
    )

    assert response.status_code == 204
    sessions = database_session.scalars(select(UserSession)).all()
    assert len(sessions) == 2
    assert all(item.revoked_at is not None for item in sessions)
    for refresh_token in (first["refresh_token"], second["refresh_token"]):
        assert (
            api_client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token},
            ).status_code
            == 401
        )
