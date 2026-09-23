from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import get_database_session
from app.main import app


@pytest.fixture
def registration_client(database_session: Session) -> Iterator[TestClient]:
    def override_database_session() -> Iterator[Session]:
        yield database_session

    app.dependency_overrides[get_database_session] = override_database_session

    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def test_register_user_returns_public_user_data(
    registration_client: TestClient,
) -> None:
    response = registration_client.post(
        "/api/v1/auth/register",
        json={
            "email": "  Learner@Example.com  ",
            "password": "synthetic passphrase 2026",
            "reference_currency": "USD",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "learner@example.com"
    assert body["reference_currency"] == "USD"
    assert "id" in body
    assert "created_at" in body
    assert "password" not in body
    assert "password_hash" not in body


@pytest.mark.parametrize(
    ("payload", "invalid_field"),
    [
        (
            {
                "email": "not-an-email",
                "password": "synthetic passphrase 2026",
            },
            "email",
        ),
        (
            {
                "email": "learner@example.com",
                "password": "too short",
            },
            "password",
        ),
        (
            {
                "email": "learner@example.com",
                "password": "synthetic passphrase 2026",
                "reference_currency": "EUR",
            },
            "reference_currency",
        ),
    ],
)
def test_register_user_rejects_invalid_input(
    registration_client: TestClient,
    payload: dict[str, str],
    invalid_field: str,
) -> None:
    response = registration_client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == invalid_field


def test_register_user_returns_generic_conflict_for_duplicate_email(
    registration_client: TestClient,
) -> None:
    payload = {
        "email": "duplicate@example.com",
        "password": "synthetic passphrase 2026",
    }
    first_response = registration_client.post(
        "/api/v1/auth/register",
        json=payload,
    )
    duplicate_response = registration_client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {
        "detail": "Registration could not be completed"
    }
