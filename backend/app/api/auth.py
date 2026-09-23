from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_authenticated_session, get_database_session
from app.schemas.auth import (
    SessionTokenResponse,
    UserLoginRequest,
    UserRegistrationRequest,
    UserResponse,
)
from app.services.authentication import (
    AuthenticatedSession,
    AuthenticationService,
    InvalidCredentialsError,
)
from app.services.user_registration import (
    EmailAlreadyRegisteredError,
    UserRegistrationService,
)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    request: UserRegistrationRequest,
    session: Annotated[Session, Depends(get_database_session)],
) -> UserResponse:
    service = UserRegistrationService(session)

    try:
        user = service.register(
            email=str(request.email),
            password=request.password,
            reference_currency=request.reference_currency,
        )
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Registration could not be completed",
        ) from exc

    return UserResponse.model_validate(user)


@router.post("/login", response_model=SessionTokenResponse)
def login_user(
    request: UserLoginRequest,
    session: Annotated[Session, Depends(get_database_session)],
) -> SessionTokenResponse:
    try:
        result = AuthenticationService(session).login(
            email=str(request.email),
            password=request.password,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return SessionTokenResponse(
        access_token=result.access_token,
        expires_at=result.expires_at,
    )


@router.get("/me", response_model=UserResponse)
def read_current_user(
    authenticated_session: Annotated[
        AuthenticatedSession,
        Depends(get_authenticated_session),
    ],
) -> UserResponse:
    return UserResponse.model_validate(authenticated_session.user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_user(
    authenticated_session: Annotated[
        AuthenticatedSession,
        Depends(get_authenticated_session),
    ],
    session: Annotated[Session, Depends(get_database_session)],
) -> Response:
    AuthenticationService(session).logout(authenticated_session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
