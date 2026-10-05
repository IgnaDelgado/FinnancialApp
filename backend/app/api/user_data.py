from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_database_session
from app.models.user import User
from app.services.authentication import InvalidCredentialsError
from app.services.user_data import UserDataService

router = APIRouter(prefix="/api/v1/user-data", tags=["user data"])


class DeleteAccountRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: SecretStr = Field(min_length=1, max_length=128)


@router.get("/export")
def export_user_data(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_database_session)],
    response: Response,
) -> dict[str, object]:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Disposition"] = (
        'attachment; filename="financial-plan-export.json"'
    )
    return UserDataService(session).export(user.id)


@router.delete("", status_code=204)
def delete_user_data(
    request: DeleteAccountRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_database_session)],
) -> Response:
    try:
        UserDataService(session).delete(user.id, request.password.get_secret_value())
    except InvalidCredentialsError as exc:
        session.rollback()
        # A wrong deletion password does not mean the bearer token needs refresh.
        raise HTTPException(403, "La contraseña actual no es correcta.") from exc
    return Response(status_code=204, headers={"Cache-Control": "no-store"})
