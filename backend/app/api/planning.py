from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_database_session
from app.domain.planning import financial_today, month_bounds
from app.models.user import User
from app.schemas.planning import (
    CommitmentCreateRequest,
    CommitmentResponse,
    IncomeCreateRequest,
    IncomeResponse,
)
from app.services.planning import PlanningService

router = APIRouter(prefix="/api/v1", tags=["planning"])


def query_month(
    year: Annotated[int | None, Query(ge=1, le=9999)] = None,
    month: Annotated[int | None, Query(ge=1, le=12)] = None,
) -> tuple[date, date]:
    today = financial_today()
    return month_bounds(
        year if year is not None else today.year,
        month if month is not None else today.month,
    )


@router.post("/income", response_model=IncomeResponse, status_code=201)
def create_income(
    request: IncomeCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_database_session)],
) -> IncomeResponse:
    income = PlanningService(session).create_income(
        user_id=current_user.id,
        description=request.description,
        amount=request.amount,
        currency=request.currency,
        expected_date=request.expected_date,
        recurrence=request.recurrence,
    )
    return IncomeResponse.model_validate(income)


@router.post("/commitments", response_model=CommitmentResponse, status_code=201)
def create_commitment(
    request: CommitmentCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_database_session)],
) -> CommitmentResponse:
    commitment = PlanningService(session).create_commitment(
        user_id=current_user.id,
        description=request.description,
        amount=request.amount,
        currency=request.currency,
        due_date=request.due_date,
        recurrence=request.recurrence,
    )
    return CommitmentResponse.model_validate(commitment)


@router.get("/income", response_model=list[IncomeResponse])
def list_income(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_database_session)],
    bounds: Annotated[tuple[date, date], Depends(query_month)],
    include_overdue: bool = True,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[IncomeResponse]:
    entries = PlanningService(session).list_income(
        current_user.id,
        start=bounds[0],
        end=bounds[1],
        include_overdue=include_overdue,
        limit=limit,
        offset=offset,
    )
    return [IncomeResponse.model_validate(item) for item in entries]


@router.get("/commitments", response_model=list[CommitmentResponse])
def list_commitments(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_database_session)],
    bounds: Annotated[tuple[date, date], Depends(query_month)],
    include_overdue: bool = True,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[CommitmentResponse]:
    entries = PlanningService(session).list_commitments(
        current_user.id,
        start=bounds[0],
        end=bounds[1],
        include_overdue=include_overdue,
        limit=limit,
        offset=offset,
    )
    return [CommitmentResponse.model_validate(item) for item in entries]
