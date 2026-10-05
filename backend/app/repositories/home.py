from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, String, cast, false, literal, null, select, union_all
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
        # One statement gives every component the same PostgreSQL MVCC snapshot.
        # Separate reads can combine an old balance with a newly confirmed bill.
        accounts = select(
            literal("account").label("kind"),
            cast(FinancialAccount.currency, String).label("currency"),
            FinancialAccount.current_balance,
            FinancialAccount.is_liquid,
            cast(null(), Date).label("financial_date"),
        ).where(
            FinancialAccount.user_id == user_id,
            FinancialAccount.archived_at.is_(None),
        )
        bills = select(
            literal("commitment"),
            cast(PlannedCommitment.currency, String),
            PlannedCommitment.amount,
            false(),
            PlannedCommitment.due_date,
        ).where(
            PlannedCommitment.user_id == user_id,
            PlannedCommitment.status == "PLANNED",
            PlannedCommitment.due_date <= month_end,
        )
        income = select(
            literal("income"),
            cast(PlannedIncome.currency, String),
            PlannedIncome.amount,
            false(),
            PlannedIncome.expected_date,
        ).where(
            PlannedIncome.user_id == user_id,
            PlannedIncome.status == "PLANNED",
            PlannedIncome.expected_date <= month_end,
        )
        rows = self._session.execute(union_all(accounts, bills, income))
        account_values: list[tuple[Currency, Decimal, bool]] = []
        bill_values: list[tuple[Currency, Decimal, date]] = []
        income_values: list[tuple[Currency, Decimal, date]] = []
        for kind, unit, amount, liquid, day in rows:
            currency = Currency(unit)
            if kind == "account":
                account_values.append((currency, amount, liquid))
            elif kind == "commitment":
                bill_values.append((currency, amount, day))
            else:
                income_values.append((currency, amount, day))
        return account_values, bill_values, income_values
