from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.core.config import get_settings
from app.models import Base

metadata = Base.metadata
_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(
            get_settings().database_url,
            pool_pre_ping=True,
        )
    return _engine


def check_database_connection() -> None:
    with get_engine().connect() as connection:
        connection.execute(text("SELECT 1"))


def dispose_database_engine() -> None:
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None
