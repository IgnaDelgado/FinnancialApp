from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.currency import Currency
from app.domain.planning import (
    financial_today,
    month_bounds,
    monthly_dates,
    validate_planned_amount,
)
from app.models.planning import MonthlyPlan, PlannedCommitment, PlannedIncome
from app.repositories.planning import PlanningRepository


class PlanningService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._records = PlanningRepository(session)

    def _create_monthly_plan(
        self,
        *,
        user_id: UUID,
        kind: str,
        description: str,
        amount: Decimal,
        currency: Currency,
        first_date: date,
    ) -> MonthlyPlan:
        plan = MonthlyPlan(
            user_id=user_id,
            kind=kind,
            description=description,
            amount=validate_planned_amount(amount),
            currency=currency,
            first_date=first_date,
            generated_through=first_date.replace(day=1),
        )
        self._records.add_monthly_plan(plan)
        return plan

    def _ensure_monthly_records(
        self, user_id: UUID, kind: str, start: date, end: date
    ) -> None:
        current_period = financial_today().replace(day=1)
        for plan in self._records.locked_monthly_plans(user_id, kind):
            if plan.generated_through < current_period:
                # Reinsert the checkpoint month safely, then fill every skipped
                # month so pending obligations never disappear after inactivity.
                current_end = month_bounds(current_period.year, current_period.month)[1]
                self._records.insert_occurrences(
                    plan,
                    monthly_dates(plan.first_date, plan.generated_through, current_end),
                )
                plan.generated_through = current_period
            # A future-month consultation materializes just that month, rather
            # than filling all intervening future months or advancing the checkpoint.
            self._records.insert_occurrences(
                plan, monthly_dates(plan.first_date, start, end)
            )
        self._session.commit()

    def create_income(
        self,
        *,
        user_id: UUID,
        description: str,
        amount: Decimal,
        currency: Currency,
        expected_date: date,
        recurrence: Literal["ONE_TIME", "MONTHLY"] = "ONE_TIME",
    ) -> PlannedIncome:
        plan = (
            self._create_monthly_plan(
                user_id=user_id,
                kind="income",
                description=description,
                amount=amount,
                currency=currency,
                first_date=expected_date,
            )
            if recurrence == "MONTHLY"
            else None
        )
        income = PlannedIncome(
            user_id=user_id,
            description=description,
            amount=validate_planned_amount(amount),
            currency=currency,
            expected_date=expected_date,
            recurrence=recurrence,
            template_id=plan.id if plan else None,
            recurrence_period=expected_date.replace(day=1) if plan else None,
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
        recurrence: Literal["ONE_TIME", "MONTHLY"] = "ONE_TIME",
    ) -> PlannedCommitment:
        plan = (
            self._create_monthly_plan(
                user_id=user_id,
                kind="commitments",
                description=description,
                amount=amount,
                currency=currency,
                first_date=due_date,
            )
            if recurrence == "MONTHLY"
            else None
        )
        commitment = PlannedCommitment(
            user_id=user_id,
            description=description,
            amount=validate_planned_amount(amount),
            currency=currency,
            due_date=due_date,
            recurrence=recurrence,
            template_id=plan.id if plan else None,
            recurrence_period=due_date.replace(day=1) if plan else None,
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
        self._ensure_monthly_records(user_id, "income", start, end)
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
        self._ensure_monthly_records(user_id, "commitments", start, end)
        return self._records.list_commitments(
            user_id,
            start=start,
            end=end,
            include_overdue=include_overdue,
            limit=limit,
            offset=offset,
        )
