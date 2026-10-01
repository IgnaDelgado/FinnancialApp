from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.currency import Currency
from app.models.financial_account import FinancialAccount
from app.models.planning import PlannedCommitment, PlannedIncome


class HomeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def inputs(
        self, user_id: UUID, month_end: date
    ) -> tuple[
        list[tuple[Currency, Decimal, bool]],
        list[tuple[Currency, Decimal, date]],
        list[tuple[Currency, Decimal, date]],
    ]:
        accounts = self._session.execute(
            select(
                FinancialAccount.currency,
                FinancialAccount.current_balance,
                FinancialAccount.is_liquid,
            ).where(
                FinancialAccount.user_id == user_id,
                FinancialAccount.archived_at.is_(None),
            )
        ).all()
        bills = self._session.execute(
            select(
                PlannedCommitment.currency,
                PlannedCommitment.amount,
                PlannedCommitment.due_date,
            ).where(
                PlannedCommitment.user_id == user_id,
                PlannedCommitment.status == "PLANNED",
                PlannedCommitment.due_date <= month_end,
            )
        ).all()
        income = self._session.execute(
            select(
                PlannedIncome.currency,
                PlannedIncome.amount,
                PlannedIncome.expected_date,
            ).where(
                PlannedIncome.user_id == user_id,
                PlannedIncome.status == "PLANNED",
                PlannedIncome.expected_date <= month_end,
            )
        ).all()
        account_values = [(unit, amount, liquid) for unit, amount, liquid in accounts]
        bill_values = [(unit, amount, day) for unit, amount, day in bills]
        income_values = [(unit, amount, day) for unit, amount, day in income]
        return account_values, bill_values, income_values
