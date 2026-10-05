from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_database_session
from app.models.user import User
from app.schemas.home import HomeResponse
from app.services.home import HomeService

router = APIRouter(prefix="/api/v1/home", tags=["home"])


@router.get("", response_model=HomeResponse)
def home_snapshot(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_database_session)],
) -> HomeResponse:
    return HomeService(session).snapshot(current_user.id)
