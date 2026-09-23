from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_engine
from app.services.authentication import (
    AuthenticatedSession,
    AuthenticationService,
    InvalidSessionError,
)

_bearer_scheme = HTTPBearer(auto_error=False)


def get_database_session() -> Iterator[Session]:
    """Provide one SQLAlchemy session for the duration of a request."""

    with Session(get_engine()) as session:
        yield session


def get_authenticated_session(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_bearer_scheme),
    ],
    session: Annotated[Session, Depends(get_database_session)],
) -> AuthenticatedSession:
    if credentials is None:
        raise _unauthorized_error()

    try:
        return AuthenticationService(session).authenticate(credentials.credentials)
    except InvalidSessionError as exc:
        raise _unauthorized_error() from exc


def _unauthorized_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )
