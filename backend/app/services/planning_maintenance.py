from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.confirmation import confirmed_balance
from app.domain.planning import financial_today, monthly_terms, validate_planned_amount
from app.models.financial_account import AccountBalanceSnapshot
from app.models.planning import MonthlyPlan, PlannedIncome
from app.models.planning_maintenance import ConfirmationCorrection, MonthlyPlanChange
from app.repositories.financial_accounts import FinancialAccountRepository
from app.repositories.planning import PlanningRepository
from app.services.planning import ConfirmationConflictError, PlanningRecordNotFoundError


class PlanningMaintenanceService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._records = PlanningRepository(session)

    def stop(self, user_id: UUID, template_id: UUID, from_month: date) -> MonthlyPlan:
        if from_month.day != 1:
            raise ValueError(
                "Elegí el primer día del mes desde el que querés detener la repetición."
            )
        plan = self._records.lock_template(user_id, template_id)
        if plan is None:
            raise PlanningRecordNotFoundError
        if from_month < plan.first_date.replace(day=1):
            raise ValueError("El mes no puede ser anterior al inicio de la repetición.")
        if plan.stopped_from is not None:
            if plan.stopped_from != from_month:
                raise ConfirmationConflictError
            self._session.commit()
            return plan
        pending = self._records.pending_occurrences(
            user_id, template_id, is_income=plan.kind == "income"
        )
        plan.stopped_from = from_month
        for record in pending:
            if (
                record.recurrence_period is not None
                and record.recurrence_period >= from_month
            ):
                record.status = "CANCELLED"
        self._session.commit()
        return plan

    def edit(
        self, user_id: UUID, template_id: UUID, first_date: date, amount: Decimal
    ) -> MonthlyPlan:
        amount = validate_planned_amount(amount)
        period = first_date.replace(day=1)
        if period <= financial_today().replace(day=1):
            raise ValueError("Sólo podés editar desde un mes futuro.")
        plan = self._records.lock_template(user_id, template_id)
        if plan is None:
            raise PlanningRecordNotFoundError
        if first_date < plan.first_date:
            raise ValueError(
                "El cambio no puede ser anterior al inicio de la repetición."
            )
        if plan.stopped_from is not None and period >= plan.stopped_from:
            raise ValueError("La repetición está detenida para ese mes.")
        pending = self._records.pending_occurrences(
            user_id, template_id, is_income=plan.kind == "income"
        )
        self._session.add(
            MonthlyPlanChange(
                template_id=plan.id,
                effective_period=period,
                amount=amount,
                day=first_date.day,
            )
        )
        self._session.flush()
        changes = self._records.monthly_changes(plan.id)
        for record in pending:
            if record.recurrence_period is None or record.recurrence_period < period:
                continue
            day, revised_amount = monthly_terms(
                record.recurrence_period, plan.first_date.day, plan.amount, changes
            )
            record.amount = revised_amount
            if isinstance(record, PlannedIncome):
                record.expected_date = day
            else:
                record.due_date = day
        self._session.commit()
        return plan

    def correct(
        self,
        user_id: UUID,
        record_id: UUID,
        original_confirmed_at: datetime,
        *,
        is_income: bool,
    ) -> ConfirmationCorrection:
        # Match generation/maintenance ordering before taking the occurrence lock.
        initial = self._records.get_record(user_id, record_id, is_income=is_income)
        if initial is None:
            raise PlanningRecordNotFoundError
        plan = (
            self._records.lock_template(user_id, initial.template_id)
            if initial.template_id
            else None
        )
        record = self._records.lock_record(user_id, record_id, is_income=is_income)
        if record is None:
            raise PlanningRecordNotFoundError
        key = (
            ConfirmationCorrection.income_id
            if is_income
            else ConfirmationCorrection.commitment_id
        )
        previous = self._session.scalar(
            select(ConfirmationCorrection).where(
                ConfirmationCorrection.user_id == user_id,
                key == record_id,
                ConfirmationCorrection.original_confirmed_at == original_confirmed_at,
            )
        )
        if previous is not None:
            self._session.commit()
            return previous
        if (
            record.confirmed_at != original_confirmed_at
            or record.account_id is None
            or record.already_in_balance is None
        ):
            raise ConfirmationConflictError
        correction = ConfirmationCorrection(
            user_id=user_id,
            income_id=record_id if is_income else None,
            commitment_id=None if is_income else record_id,
            account_id=record.account_id,
            amount=record.amount,
            currency=record.currency.value,
            already_in_balance=record.already_in_balance,
            remember_account=record.remember_account,
            original_confirmed_at=record.confirmed_at,
            corrected_at=datetime.now(UTC),
        )
        if not record.already_in_balance:
            accounts = FinancialAccountRepository(self._session)
            account = accounts.get_active(user_id, record.account_id, lock=True)
            if account is None:
                raise ValueError(
                    "La cuenta original está archivada; no se puede ajustar su saldo."
                )
            correction.balance_before = account.current_balance
            account.current_balance = confirmed_balance(
                account.current_balance,
                record.amount,
                account.currency,
                record.currency,
                is_income=not is_income,
            )
            correction.balance_after = account.current_balance
            account.balance_updated_at = correction.corrected_at
            accounts.add_snapshot(
                AccountBalanceSnapshot(
                    account_id=account.id,
                    balance=account.current_balance,
                    recorded_at=correction.corrected_at,
                )
            )
        record.status = "PLANNED"
        if (
            plan is not None
            and plan.stopped_from is not None
            and record.recurrence_period is not None
            and record.recurrence_period >= plan.stopped_from
        ):
            record.status = "CANCELLED"
        record.account_id = None
        record.confirmed_at = None
        record.already_in_balance = None
        record.remember_account = False
        self._session.add(correction)
        self._session.commit()
        self._session.refresh(correction)
        return correction
