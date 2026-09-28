from collections.abc import Iterator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def test_health_reports_healthy_without_database(client: TestClient) -> None:
    with patch(
        "app.api.health.check_database_connection",
        side_effect=AssertionError("Health must not query PostgreSQL"),
    ):
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_readiness_reports_ready_when_database_is_available(client: TestClient) -> None:
    with patch("app.api.health.check_database_connection") as database_check:
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    database_check.assert_called_once_with()


def test_readiness_reports_unavailable_when_database_connection_fails(
    client: TestClient,
) -> None:
    database_error = OperationalError("SELECT 1", {}, Exception("unavailable"))

    with patch(
        "app.api.health.check_database_connection",
        side_effect=database_error,
    ):
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
