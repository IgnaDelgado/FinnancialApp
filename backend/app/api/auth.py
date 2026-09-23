from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_database_session
from app.schemas.auth import UserRegistrationRequest, UserResponse
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
