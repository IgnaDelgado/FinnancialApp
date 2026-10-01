from datetime import date
from uuid import UUID

from sqlalchemy import false, or_, select
from sqlalchemy.orm import Session

from app.models.planning import PlannedCommitment, PlannedIncome


class PlanningRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_income(self, income: PlannedIncome) -> None:
        self._session.add(income)

    def add_commitment(self, commitment: PlannedCommitment) -> None:
        self._session.add(commitment)

    def list_income(
        self,
        user_id: UUID,
        *,
        start: date,
        end: date,
        include_overdue: bool,
        limit: int,
        offset: int,
    ) -> list[PlannedIncome]:
        statement = (
            select(PlannedIncome)
            .where(
                PlannedIncome.user_id == user_id,
                or_(
                    PlannedIncome.expected_date.between(start, end),
                    (PlannedIncome.expected_date < start)
                    & (PlannedIncome.status == "PLANNED")
                    if include_overdue
                    else false(),
                ),
            )
            .order_by(PlannedIncome.expected_date, PlannedIncome.id)
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(statement).all())

    def list_commitments(
        self,
        user_id: UUID,
        *,
        start: date,
        end: date,
        include_overdue: bool,
        limit: int,
        offset: int,
    ) -> list[PlannedCommitment]:
        statement = (
            select(PlannedCommitment)
            .where(
                PlannedCommitment.user_id == user_id,
                or_(
                    PlannedCommitment.due_date.between(start, end),
                    (PlannedCommitment.due_date < start)
                    & (PlannedCommitment.status == "PLANNED")
                    if include_overdue
                    else false(),
                ),
            )
            .order_by(PlannedCommitment.due_date, PlannedCommitment.id)
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(statement).all())
