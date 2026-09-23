from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.core.database import get_engine


def get_database_session() -> Iterator[Session]:
    """Provide one SQLAlchemy session for the duration of a request."""

    with Session(get_engine()) as session:
        yield session
