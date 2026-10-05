from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.currency import Currency
from app.models.base import Base
from app.models.financial_account import FinancialAccount


class MonthlyPlan(Base):
    __tablename__ = "monthly_plans"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('income', 'commitments')", name="ck_monthly_plans_kind"
        ),
        CheckConstraint("amount > 0", name="ck_monthly_plans_positive_amount"),
        CheckConstraint(
            "length(trim(description)) > 0", name="ck_monthly_plans_description"
        ),
        Index("ix_monthly_plans_user_kind", "user_id", "kind"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(11))
    description: Mapped[str] = mapped_column(String(100))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency: Mapped[Currency] = mapped_column(
        Enum(
            Currency,
            name="monthly_plan_currency",
            native_enum=False,
            create_constraint=True,
        )
    )
    first_date: Mapped[date] = mapped_column(Date)
    preferred_account_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("financial_accounts.id")
    )
    generated_through: Mapped[date] = mapped_column(Date)
    stopped_from: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class PlannedIncome(Base):
    __tablename__ = "planned_income"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_planned_income_positive_amount"),
        CheckConstraint(
            "length(trim(description)) > 0", name="ck_planned_income_description"
        ),
        CheckConstraint(
            "status IN ('PLANNED', 'RECEIVED', 'CANCELLED')",
            name="ck_planned_income_status",
        ),
        CheckConstraint(
            "(status IN ('PLANNED', 'CANCELLED') AND account_id IS NULL "
            "AND confirmed_at IS NULL "
            "AND already_in_balance IS NULL) OR (status = 'RECEIVED' "
            "AND account_id IS NOT NULL AND confirmed_at IS NOT NULL "
            "AND already_in_balance IS NOT NULL)",
            name="ck_planned_income_confirmation",
        ),
        CheckConstraint(
            "recurrence IN ('ONE_TIME', 'MONTHLY')", name="ck_planned_income_recurrence"
        ),
        CheckConstraint(
            "(recurrence = 'MONTHLY' AND template_id IS NOT NULL "
            "AND recurrence_period IS NOT NULL) OR "
            "(recurrence = 'ONE_TIME' AND template_id IS NULL "
            "AND recurrence_period IS NULL)",
            name="ck_planned_income_template",
        ),
        UniqueConstraint(
            "template_id", "recurrence_period", name="uq_planned_income_template_period"
        ),
        Index("ix_planned_income_user_date_id", "user_id", "expected_date", "id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    description: Mapped[str] = mapped_column(String(100))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency: Mapped[Currency] = mapped_column(
        Enum(
            Currency,
            name="planned_income_currency",
            native_enum=False,
            create_constraint=True,
        )
    )
    expected_date: Mapped[date] = mapped_column(Date)
    preferred_account_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("financial_accounts.id")
    )
    preferred_account: Mapped[FinancialAccount | None] = relationship(
        foreign_keys=[preferred_account_id], lazy="selectin"
    )

    @property
    def preferred_account_name(self) -> str | None:
        return self.preferred_account.name if self.preferred_account else None

    remember_account: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    status: Mapped[str] = mapped_column(String(9), default="PLANNED")
    account_id: Mapped[UUID | None] = mapped_column(ForeignKey("financial_accounts.id"))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    already_in_balance: Mapped[bool | None] = mapped_column(Boolean)
    recurrence: Mapped[str] = mapped_column(String(8), default="ONE_TIME")
    template_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("monthly_plans.id", ondelete="CASCADE")
    )
    recurrence_period: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class PlannedCommitment(Base):
    __tablename__ = "planned_commitments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_planned_commitments_positive_amount"),
        CheckConstraint(
            "length(trim(description)) > 0", name="ck_planned_commitments_description"
        ),
        CheckConstraint(
            "status IN ('PLANNED', 'PAID', 'CANCELLED')",
            name="ck_planned_commitments_status",
        ),
        CheckConstraint(
            "(status IN ('PLANNED', 'CANCELLED') AND account_id IS NULL "
            "AND confirmed_at IS NULL "
            "AND already_in_balance IS NULL) OR (status = 'PAID' "
            "AND account_id IS NOT NULL AND confirmed_at IS NOT NULL "
            "AND already_in_balance IS NOT NULL)",
            name="ck_planned_commitments_confirmation",
        ),
        CheckConstraint(
            "recurrence IN ('ONE_TIME', 'MONTHLY')",
            name="ck_planned_commitments_recurrence",
        ),
        CheckConstraint(
            "(recurrence = 'MONTHLY' AND template_id IS NOT NULL "
            "AND recurrence_period IS NOT NULL) OR "
            "(recurrence = 'ONE_TIME' AND template_id IS NULL "
            "AND recurrence_period IS NULL)",
            name="ck_planned_commitments_template",
        ),
        UniqueConstraint(
            "template_id",
            "recurrence_period",
            name="uq_planned_commitments_template_period",
        ),
        Index("ix_planned_commitments_user_date_id", "user_id", "due_date", "id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    description: Mapped[str] = mapped_column(String(100))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency: Mapped[Currency] = mapped_column(
        Enum(
            Currency,
            name="planned_commitments_currency",
            native_enum=False,
            create_constraint=True,
        )
    )
    due_date: Mapped[date] = mapped_column(Date)
    preferred_account_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("financial_accounts.id")
    )
    preferred_account: Mapped[FinancialAccount | None] = relationship(
        foreign_keys=[preferred_account_id], lazy="selectin"
    )

    @property
    def preferred_account_name(self) -> str | None:
        return self.preferred_account.name if self.preferred_account else None

    remember_account: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    status: Mapped[str] = mapped_column(String(9), default="PLANNED")
    account_id: Mapped[UUID | None] = mapped_column(ForeignKey("financial_accounts.id"))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    already_in_balance: Mapped[bool | None] = mapped_column(Boolean)
    recurrence: Mapped[str] = mapped_column(String(8), default="ONE_TIME")
    template_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("monthly_plans.id", ondelete="CASCADE")
    )
    recurrence_period: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
