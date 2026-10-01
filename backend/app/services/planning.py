from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.currency import Currency
from app.domain.planning import validate_planned_amount
from app.models.planning import PlannedCommitment, PlannedIncome
from app.repositories.planning import PlanningRepository


class PlanningService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._records = PlanningRepository(session)

    def create_income(
        self,
        *,
        user_id: UUID,
        description: str,
        amount: Decimal,
        currency: Currency,
        expected_date: date,
    ) -> PlannedIncome:
        income = PlannedIncome(
            user_id=user_id,
            description=description,
            amount=validate_planned_amount(amount),
            currency=currency,
            expected_date=expected_date,
        )
        self._records.add_income(income)
        self._session.commit()
        self._session.refresh(income)
        return income

    def create_commitment(
        self,
        *,
        user_id: UUID,
        description: str,
        amount: Decimal,
        currency: Currency,
        due_date: date,
    ) -> PlannedCommitment:
        commitment = PlannedCommitment(
            user_id=user_id,
            description=description,
            amount=validate_planned_amount(amount),
            currency=currency,
            due_date=due_date,
        )
        self._records.add_commitment(commitment)
        self._session.commit()
        self._session.refresh(commitment)
        return commitment

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
        return self._records.list_income(
            user_id,
            start=start,
            end=end,
            include_overdue=include_overdue,
            limit=limit,
            offset=offset,
        )

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
        return self._records.list_commitments(
            user_id,
            start=start,
            end=end,
            include_overdue=include_overdue,
            limit=limit,
            offset=offset,
        )
