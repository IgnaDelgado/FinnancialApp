from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_database_session
from app.models.user import User
from app.schemas.planning_maintenance import (
    CorrectionRequest,
    CorrectionResponse,
    MonthlyEditRequest,
    MonthlyPlanResponse,
    MonthlyStopRequest,
)
from app.services.planning import ConfirmationConflictError, PlanningRecordNotFoundError
from app.services.planning_maintenance import PlanningMaintenanceService

router = APIRouter(prefix="/api/v1", tags=["planning maintenance"])


def _run[T](session: Session, operation: Callable[[], T]) -> T:
    try:
        return operation()
    except PlanningRecordNotFoundError as exc:
        session.rollback()
        raise HTTPException(
            404, "No encontramos el movimiento o la repetición."
        ) from exc
    except ConfirmationConflictError as exc:
        session.rollback()
        raise HTTPException(
            409, "El registro cambió. Actualizá la lista antes de continuar."
        ) from exc
    except ValueError as exc:
        session.rollback()
        raise HTTPException(422, str(exc)) from exc


@router.post("/monthly-plans/{template_id}/stop", response_model=MonthlyPlanResponse)
def stop_monthly_plan(
    template_id: UUID,
    request: MonthlyStopRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_database_session)],
) -> MonthlyPlanResponse:
    plan = _run(
        session,
        lambda: PlanningMaintenanceService(session).stop(
            user.id, template_id, request.from_month
        ),
    )
    return MonthlyPlanResponse.model_validate(plan)


@router.post("/monthly-plans/{template_id}/edit", response_model=MonthlyPlanResponse)
def edit_monthly_plan(
    template_id: UUID,
    request: MonthlyEditRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_database_session)],
) -> MonthlyPlanResponse:
    plan = _run(
        session,
        lambda: PlanningMaintenanceService(session).edit(
            user.id, template_id, request.first_date, request.amount
        ),
    )
    return MonthlyPlanResponse.model_validate(plan)


@router.post("/income/{record_id}/correct", response_model=CorrectionResponse)
def correct_income(
    record_id: UUID,
    request: CorrectionRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_database_session)],
) -> CorrectionResponse:
    result = _run(
        session,
        lambda: PlanningMaintenanceService(session).correct(
            user.id, record_id, request.original_confirmed_at, is_income=True
        ),
    )
    return CorrectionResponse.model_validate(result)


@router.post("/commitments/{record_id}/correct", response_model=CorrectionResponse)
def correct_commitment(
    record_id: UUID,
    request: CorrectionRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_database_session)],
) -> CorrectionResponse:
    result = _run(
        session,
        lambda: PlanningMaintenanceService(session).correct(
            user.id, record_id, request.original_confirmed_at, is_income=False
        ),
    )
    return CorrectionResponse.model_validate(result)
