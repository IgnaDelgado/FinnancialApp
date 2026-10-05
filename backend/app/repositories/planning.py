from collections.abc import Iterable
from datetime import date
from decimal import Decimal
from typing import cast
from uuid import UUID, uuid4

from sqlalchemy import false, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.domain.planning import monthly_terms
from app.models.planning import MonthlyPlan, PlannedCommitment, PlannedIncome
from app.models.planning_maintenance import MonthlyPlanChange


class PlanningRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def lock_record(
        self, user_id: UUID, record_id: UUID, *, is_income: bool
    ) -> PlannedIncome | PlannedCommitment | None:
        model = PlannedIncome if is_income else PlannedCommitment
        return cast(
            PlannedIncome | PlannedCommitment | None,
            self._session.scalar(
                select(model)
                .where(model.id == record_id, model.user_id == user_id)
                .with_for_update()
                .execution_options(populate_existing=True)
            ),
        )

    def add_income(self, income: PlannedIncome) -> None:
        self._session.add(income)

    def get_record(
        self, user_id: UUID, record_id: UUID, *, is_income: bool
    ) -> PlannedIncome | PlannedCommitment | None:
        model = PlannedIncome if is_income else PlannedCommitment
        return cast(
            PlannedIncome | PlannedCommitment | None,
            self._session.scalar(
                select(model).where(model.id == record_id, model.user_id == user_id)
            ),
        )

    def lock_template(self, user_id: UUID, template_id: UUID) -> MonthlyPlan | None:
        return self._session.scalar(
            select(MonthlyPlan)
            .where(
                MonthlyPlan.id == template_id,
                MonthlyPlan.user_id == user_id,
            )
            .with_for_update()
            .execution_options(populate_existing=True)
        )

    def pending_occurrences(
        self, user_id: UUID, template_id: UUID, *, is_income: bool
    ) -> list[PlannedIncome | PlannedCommitment]:
        model = PlannedIncome if is_income else PlannedCommitment
        return list(
            cast(
                Iterable[PlannedIncome | PlannedCommitment],
                self._session.scalars(
                    select(model)
                    .where(
                        model.user_id == user_id,
                        model.template_id == template_id,
                        model.status == "PLANNED",
                    )
                    .order_by(model.id)
                    .with_for_update()
                    .execution_options(populate_existing=True)
                ).all(),
            )
        )

    def add_commitment(self, commitment: PlannedCommitment) -> None:
        self._session.add(commitment)

    def add_monthly_plan(self, plan: MonthlyPlan) -> None:
        self._session.add(plan)
        self._session.flush()

    def locked_monthly_plans(
        self, user_id: UUID, kind: str | None, through: date
    ) -> list[MonthlyPlan]:
        statement = (
            select(MonthlyPlan)
            .where(MonthlyPlan.user_id == user_id)
            .where(MonthlyPlan.generated_through < through)
            .where(
                or_(
                    MonthlyPlan.stopped_from.is_(None),
                    MonthlyPlan.generated_through < MonthlyPlan.stopped_from,
                )
            )
            .order_by(MonthlyPlan.id)
            .with_for_update()
        )
        if kind is not None:
            statement = statement.where(MonthlyPlan.kind == kind)
        return list(self._session.scalars(statement).all())

    def insert_occurrences(self, plan: MonthlyPlan, dates: Iterable[date]) -> None:
        table = PlannedIncome if plan.kind == "income" else PlannedCommitment
        date_field = "expected_date" if plan.kind == "income" else "due_date"
        batch: list[dict[str, object]] = []
        changes = self.monthly_changes(plan.id)
        for occurrence in dates:
            if (
                plan.stopped_from is not None
                and occurrence.replace(day=1) >= plan.stopped_from
            ):
                break
            occurrence, amount = monthly_terms(
                occurrence, plan.first_date.day, plan.amount, changes
            )
            batch.append(
                {
                    "id": uuid4(),
                    "user_id": plan.user_id,
                    "description": plan.description,
                    "amount": amount,
                    "currency": plan.currency,
                    "preferred_account_id": plan.preferred_account_id,
                    date_field: occurrence,
                    "status": "PLANNED",
                    "recurrence": "MONTHLY",
                    "template_id": plan.id,
                    "recurrence_period": occurrence.replace(day=1),
                }
            )

            if len(batch) == 500:
                self._session.execute(
                    insert(table)
                    .values(batch)
                    .on_conflict_do_nothing(
                        index_elements=["template_id", "recurrence_period"]
                    )
                )
                batch.clear()
        if batch:
            self._session.execute(
                insert(table)
                .values(batch)
                .on_conflict_do_nothing(
                    index_elements=["template_id", "recurrence_period"]
                )
            )

    def monthly_changes(self, template_id: UUID) -> list[tuple[date, Decimal, int]]:
        return list(
            self._session.execute(
                select(
                    MonthlyPlanChange.effective_period,
                    MonthlyPlanChange.amount,
                    MonthlyPlanChange.day,
                )
                .where(MonthlyPlanChange.template_id == template_id)
                .order_by(MonthlyPlanChange.effective_period, MonthlyPlanChange.id)
            )
            .tuples()
            .all()
        )

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
