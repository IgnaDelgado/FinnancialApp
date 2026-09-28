from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import check_database_connection

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["healthy", "ready"]


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Report whether the API process can serve requests."""
    return HealthResponse(status="healthy")


@router.get("/ready", response_model=HealthResponse)
def readiness() -> HealthResponse:
    """Report whether the API can reach its required database."""
    try:
        check_database_connection()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc

    return HealthResponse(status="ready")
