from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MonthlyPlanChange(Base):
    __tablename__ = "monthly_plan_changes"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_monthly_changes_positive_amount"),
        CheckConstraint("day BETWEEN 1 AND 31", name="ck_monthly_changes_day"),
        Index(
            "ix_monthly_changes_plan_period", "template_id", "effective_period", "id"
        ),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_id: Mapped[UUID] = mapped_column(
        ForeignKey("monthly_plans.id", ondelete="CASCADE")
    )
    effective_period: Mapped[date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    day: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ConfirmationCorrection(Base):
    __tablename__ = "confirmation_corrections"
    __table_args__ = (
        CheckConstraint(
            "(income_id IS NULL) <> (commitment_id IS NULL)",
            name="ck_corrections_one_record",
        ),
        CheckConstraint("amount > 0", name="ck_corrections_positive_amount"),
        CheckConstraint("currency IN ('ARS', 'USD')", name="ck_corrections_currency"),
        UniqueConstraint(
            "income_id",
            "original_confirmed_at",
            name="uq_corrections_income_confirmation",
        ),
        UniqueConstraint(
            "commitment_id",
            "original_confirmed_at",
            name="uq_corrections_commitment_confirmation",
        ),
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    income_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("planned_income.id", ondelete="CASCADE")
    )
    commitment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("planned_commitments.id", ondelete="CASCADE")
    )
    account_id: Mapped[UUID] = mapped_column(ForeignKey("financial_accounts.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency: Mapped[str] = mapped_column(String(3))
    already_in_balance: Mapped[bool] = mapped_column(Boolean)
    remember_account: Mapped[bool] = mapped_column(Boolean)
    original_confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    corrected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    balance_before: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    balance_after: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
