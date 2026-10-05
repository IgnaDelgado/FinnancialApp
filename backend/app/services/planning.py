from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.confirmation import confirmed_balance
from app.domain.currency import Currency
from app.domain.planning import (
    financial_today,
    month_bounds,
    monthly_dates,
    validate_planned_amount,
)
from app.models.financial_account import AccountBalanceSnapshot
from app.models.planning import MonthlyPlan, PlannedCommitment, PlannedIncome
from app.repositories.financial_accounts import FinancialAccountRepository
from app.repositories.planning import PlanningRepository


class PlanningRecordNotFoundError(Exception):
    """No planning record belongs to the user."""


class ConfirmationConflictError(Exception):
    """A previous confirmation used different parameters."""


class PlanningService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._records = PlanningRepository(session)

    def confirm(
        self,
        *,
        user_id: UUID,
        record_id: UUID,
        account_id: UUID,
        already_in_balance: bool,
        is_income: bool,
        remember_account: bool = False,
    ) -> PlannedIncome | PlannedCommitment:
        # Lock the template before its occurrences, as monthly generation does.
        template = None
        pending: list[PlannedIncome | PlannedCommitment] = []
        if remember_account:
            initial = self._records.get_record(user_id, record_id, is_income=is_income)
            if initial is None:
                raise PlanningRecordNotFoundError
            if initial.template_id is None:
                raise ValueError(
                    "Solo los movimientos mensuales pueden recordar una cuenta."
                )
            template = self._records.lock_template(user_id, initial.template_id)
            pending = self._records.pending_occurrences(
                user_id, initial.template_id, is_income=is_income
            )
        record = self._records.lock_record(user_id, record_id, is_income=is_income)
        if record is None:
            raise PlanningRecordNotFoundError
        if record.status != "PLANNED":
            if (
                record.account_id != account_id
                or record.already_in_balance != already_in_balance
                or record.remember_account != remember_account
            ):
                raise ConfirmationConflictError
            # Identical retries succeed even if the account has since been archived.
            self._session.commit()
            return record
        accounts = FinancialAccountRepository(self._session)
        account = accounts.get_active(user_id, account_id, lock=True)
        if account is None:
            raise PlanningRecordNotFoundError
        if account.currency != record.currency:
            raise ValueError("La cuenta y el movimiento deben tener la misma moneda.")
        if template is not None:
            template.preferred_account_id = account.id
            for occurrence in pending:
                occurrence.preferred_account_id = account.id
        confirmed_at = datetime.now(UTC)
        if not already_in_balance:
            account.current_balance = confirmed_balance(
                account.current_balance,
                record.amount,
                account.currency,
                record.currency,
                is_income=is_income,
            )
            account.balance_updated_at = confirmed_at
            accounts.add_snapshot(
                AccountBalanceSnapshot(
                    account_id=account.id,
                    balance=account.current_balance,
                    recorded_at=confirmed_at,
                )
            )
        record.status = "RECEIVED" if is_income else "PAID"
        record.account_id = account.id
        record.already_in_balance = already_in_balance
        record.remember_account = remember_account
        record.confirmed_at = confirmed_at
        self._session.commit()
        self._session.refresh(record)
        return record

    def _create_monthly_plan(
        self,
        *,
        user_id: UUID,
        kind: str,
        description: str,
        amount: Decimal,
        currency: Currency,
        first_date: date,
        preferred_account_id: UUID | None = None,
    ) -> MonthlyPlan:
        plan = MonthlyPlan(
            user_id=user_id,
            kind=kind,
            description=description,
            amount=validate_planned_amount(amount),
            currency=currency,
            first_date=first_date,
            preferred_account_id=preferred_account_id,
            generated_through=first_date.replace(day=1),
        )
        self._records.add_monthly_plan(plan)
        return plan

    def ensure_monthly_records(
        self, user_id: UUID, kind: str | None, start: date, end: date
    ) -> None:
        current_period = financial_today().replace(day=1)
        requested_period = start.replace(day=1)
        for plan in self._records.locked_monthly_plans(
            user_id, kind, max(current_period, requested_period)
        ):
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
            if requested_period > plan.generated_through:
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
        preferred_account_id: UUID | None = None,
    ) -> PlannedIncome:
        self._validate_preferred_account(user_id, preferred_account_id, currency)
        plan = (
            self._create_monthly_plan(
                user_id=user_id,
                kind="income",
                description=description,
                amount=amount,
                currency=currency,
                first_date=expected_date,
                preferred_account_id=preferred_account_id,
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
            preferred_account_id=preferred_account_id,
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
        preferred_account_id: UUID | None = None,
    ) -> PlannedCommitment:
        self._validate_preferred_account(user_id, preferred_account_id, currency)
        plan = (
            self._create_monthly_plan(
                user_id=user_id,
                kind="commitments",
                description=description,
                amount=amount,
                currency=currency,
                first_date=due_date,
                preferred_account_id=preferred_account_id,
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
            preferred_account_id=preferred_account_id,
            recurrence=recurrence,
            template_id=plan.id if plan else None,
            recurrence_period=due_date.replace(day=1) if plan else None,
        )
        self._records.add_commitment(commitment)
        self._session.commit()
        self._session.refresh(commitment)
        return commitment

    def _validate_preferred_account(
        self,
        user_id: UUID,
        account_id: UUID | None,
        currency: Currency,
    ) -> None:
        if account_id is None:
            return
        account = FinancialAccountRepository(self._session).get_active(
            user_id, account_id, lock=True
        )
        if account is None:
            raise PlanningRecordNotFoundError
        if account.currency != currency:
            raise ValueError("La cuenta y el movimiento deben tener la misma moneda.")

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
        self.ensure_monthly_records(user_id, "income", start, end)
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
        self.ensure_monthly_records(user_id, "commitments", start, end)
        return self._records.list_commitments(
            user_id,
            start=start,
            end=end,
            include_overdue=include_overdue,
            limit=limit,
            offset=offset,
        )
