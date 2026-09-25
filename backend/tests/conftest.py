import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

os.environ.setdefault(
    "JWT_SECRET_KEY",
    "synthetic-test-secret-key-with-more-than-32-characters",
)

from app.api.dependencies import get_database_session  # noqa: E402
from app.core.database import get_engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def database_session() -> Iterator[Session]:
    """Provide an isolated transaction against the migrated test database."""

    with get_engine().connect() as connection:
        transaction = connection.begin()
        session = Session(
            bind=connection,
            join_transaction_mode="create_savepoint",
        )

        try:
            yield session
        finally:
            session.close()
            if transaction.is_active:
                transaction.rollback()


@pytest.fixture
def api_client(database_session: Session) -> Iterator[TestClient]:
    def override_database_session() -> Iterator[Session]:
        yield database_session

    app.dependency_overrides[get_database_session] = override_database_session

    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
