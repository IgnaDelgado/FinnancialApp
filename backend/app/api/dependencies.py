from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_engine
from app.core.security import InvalidAccessTokenError
from app.models.user import User
from app.services.authentication import (
    AuthenticationService,
    InvalidCredentialsError,
)

_bearer_scheme = HTTPBearer(auto_error=False)


def get_database_session() -> Iterator[Session]:
    """Provide one SQLAlchemy session for the duration of a request."""

    with Session(get_engine()) as session:
        yield session


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_bearer_scheme),
    ],
    session: Annotated[Session, Depends(get_database_session)],
) -> User:
    if credentials is None:
        raise _unauthorized_error()

    try:
        return AuthenticationService(session).authenticate_access_token(
            credentials.credentials
        )
    except (InvalidAccessTokenError, InvalidCredentialsError) as exc:
        raise _unauthorized_error() from exc


def _unauthorized_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )
