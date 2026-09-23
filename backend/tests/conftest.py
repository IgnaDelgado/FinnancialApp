from collections.abc import Iterator

import pytest
from sqlalchemy.orm import Session

from app.core.database import get_engine


@pytest.fixture
def database_session() -> Iterator[Session]:
    """Provide an isolated transaction against the migrated test database."""

    with get_engine().connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection)

        try:
            yield session
        finally:
            session.close()
            if transaction.is_active:
                transaction.rollback()
