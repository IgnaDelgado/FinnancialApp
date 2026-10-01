from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.currency import Currency
from app.models.financial_account import AccountBalanceSnapshot, FinancialAccount


class FinancialAccountRepository:
    """Access user-owned accounts and their balance history."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, account: FinancialAccount) -> None:
        self._session.add(account)

    def add_snapshot(self, snapshot: AccountBalanceSnapshot) -> None:
        self._session.add(snapshot)

    def list_active(
        self, user_id: UUID, *, limit: int, offset: int
    ) -> list[FinancialAccount]:
        statement = (
            select(FinancialAccount)
            .where(
                FinancialAccount.user_id == user_id,
                FinancialAccount.archived_at.is_(None),
            )
            .order_by(FinancialAccount.created_at.desc(), FinancialAccount.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(statement).all())

    def list_active_balances(self, user_id: UUID) -> list[tuple[Currency, Decimal]]:
        statement = select(
            FinancialAccount.currency, FinancialAccount.current_balance
        ).where(
            FinancialAccount.user_id == user_id,
            FinancialAccount.archived_at.is_(None),
        )
        return [
            (currency, balance)
            for currency, balance in self._session.execute(statement)
        ]

    def get_active(self, user_id: UUID, account_id: UUID) -> FinancialAccount | None:
        statement = select(FinancialAccount).where(
            FinancialAccount.id == account_id,
            FinancialAccount.user_id == user_id,
            FinancialAccount.archived_at.is_(None),
        )
        return self._session.scalar(statement)

    def list_snapshots(
        self, account_id: UUID, *, limit: int, offset: int
    ) -> list[AccountBalanceSnapshot]:
        statement = (
            select(AccountBalanceSnapshot)
            .where(AccountBalanceSnapshot.account_id == account_id)
            .order_by(AccountBalanceSnapshot.recorded_at, AccountBalanceSnapshot.id)
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(statement).all())
