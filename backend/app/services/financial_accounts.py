from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.account import DEFAULT_LIQUID_ACCOUNT_TYPES, AccountType
from app.domain.currency import Currency
from app.models.financial_account import AccountBalanceSnapshot, FinancialAccount
from app.repositories.financial_accounts import FinancialAccountRepository


class AccountNotFoundError(Exception):
    """No active account belongs to this user and identifier."""


class FinancialAccountService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._accounts = FinancialAccountRepository(session)

    def create(
        self,
        *,
        user_id: UUID,
        name: str,
        account_type: AccountType,
        currency: Currency,
        initial_balance: Decimal,
        is_liquid: bool | None,
    ) -> FinancialAccount:
        recorded_at = datetime.now(UTC)
        account = FinancialAccount(
            user_id=user_id,
            name=name,
            account_type=account_type,
            currency=currency,
            current_balance=initial_balance,
            is_liquid=(
                account_type in DEFAULT_LIQUID_ACCOUNT_TYPES
                if is_liquid is None
                else is_liquid
            ),
            balance_updated_at=recorded_at,
        )
        self._accounts.add(account)
        self._session.flush()
        self._accounts.add_snapshot(
            AccountBalanceSnapshot(
                account_id=account.id, balance=initial_balance, recorded_at=recorded_at
            )
        )
        self._session.commit()
        self._session.refresh(account)
        return account

    def list_active(self, user_id: UUID) -> list[FinancialAccount]:
        return self._accounts.list_active(user_id)

    def get_active(self, user_id: UUID, account_id: UUID) -> FinancialAccount:
        account = self._accounts.get_active(user_id, account_id)
        if account is None:
            raise AccountNotFoundError
        return account

    def update_balance(
        self, *, user_id: UUID, account_id: UUID, balance: Decimal
    ) -> FinancialAccount:
        account = self.get_active(user_id, account_id)
        recorded_at = datetime.now(UTC)
        account.current_balance = balance
        account.balance_updated_at = recorded_at
        self._accounts.add_snapshot(
            AccountBalanceSnapshot(
                account_id=account.id, balance=balance, recorded_at=recorded_at
            )
        )
        self._session.commit()
        self._session.refresh(account)
        return account

    def list_balance_history(
        self, *, user_id: UUID, account_id: UUID
    ) -> list[AccountBalanceSnapshot]:
        account = self.get_active(user_id, account_id)
        return self._accounts.list_snapshots(account.id)

    def archive(self, *, user_id: UUID, account_id: UUID) -> None:
        account = self.get_active(user_id, account_id)
        account.archived_at = datetime.now(UTC)
        self._session.commit()
