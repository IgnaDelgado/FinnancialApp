from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_database_session
from app.models.user import User
from app.schemas.auth import (
    RefreshTokenRequest,
    TokenPairResponse,
    UserLoginRequest,
    UserRegistrationRequest,
    UserResponse,
)
from app.services.authentication import (
    AuthenticationService,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    TokenPair,
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


@router.post("/login", response_model=TokenPairResponse)
def login_user(
    request: UserLoginRequest,
    session: Annotated[Session, Depends(get_database_session)],
) -> TokenPairResponse:
    try:
        result = AuthenticationService(session).login(
            email=str(request.email),
            password=request.password,
        )
    except InvalidCredentialsError as exc:
        raise _invalid_credentials_error() from exc
    return _token_response(result)


@router.post("/refresh", response_model=TokenPairResponse)
def refresh_tokens(
    request: RefreshTokenRequest,
    session: Annotated[Session, Depends(get_database_session)],
) -> TokenPairResponse:
    try:
        result = AuthenticationService(session).refresh(request.refresh_token)
    except InvalidRefreshTokenError as exc:
        raise _invalid_refresh_error() from exc
    return _token_response(result)


@router.get("/me", response_model=UserResponse)
def read_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_user(
    request: RefreshTokenRequest,
    session: Annotated[Session, Depends(get_database_session)],
) -> Response:
    try:
        AuthenticationService(session).logout(request.refresh_token)
    except InvalidRefreshTokenError as exc:
        raise _invalid_refresh_error() from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all_devices(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_database_session)],
) -> Response:
    AuthenticationService(session).logout_all(current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _token_response(result: TokenPair) -> TokenPairResponse:
    return TokenPairResponse.model_validate(result, from_attributes=True)


def _invalid_credentials_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _invalid_refresh_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
    )
