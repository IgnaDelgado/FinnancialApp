from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.account import AccountType
from app.domain.currency import Currency
from app.models.base import Base


class FinancialAccount(Base):
    """A user's cash balance, excluding any investment positions."""

    __tablename__ = "financial_accounts"
    __table_args__ = (
        CheckConstraint(
            "current_balance >= 0", name="ck_financial_accounts_nonnegative_balance"
        ),
        CheckConstraint(
            "length(trim(name)) > 0", name="ck_financial_accounts_name_not_blank"
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    account_type: Mapped[AccountType] = mapped_column(
        Enum(
            AccountType,
            name="financial_account_type",
            native_enum=False,
            create_constraint=True,
        )
    )
    currency: Mapped[Currency] = mapped_column(
        Enum(
            Currency,
            name="financial_account_currency",
            native_enum=False,
            create_constraint=True,
        )
    )
    current_balance: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    is_liquid: Mapped[bool] = mapped_column(Boolean)
    balance_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AccountBalanceSnapshot(Base):
    """A recorded balance at the time an account was created or updated."""

    __tablename__ = "account_balance_snapshots"
    __table_args__ = (
        CheckConstraint(
            "balance >= 0", name="ck_account_balance_snapshots_nonnegative_balance"
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("financial_accounts.id", ondelete="CASCADE"), index=True
    )
    balance: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
