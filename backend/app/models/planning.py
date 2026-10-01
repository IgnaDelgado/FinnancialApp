from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.currency import Currency
from app.models.base import Base


class PlannedIncome(Base):
    __tablename__ = "planned_income"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_planned_income_positive_amount"),
        CheckConstraint(
            "length(trim(description)) > 0", name="ck_planned_income_description"
        ),
        CheckConstraint("status = 'PLANNED'", name="ck_planned_income_status"),
        CheckConstraint("recurrence = 'ONE_TIME'", name="ck_planned_income_recurrence"),
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
    status: Mapped[str] = mapped_column(String(7), default="PLANNED")
    recurrence: Mapped[str] = mapped_column(String(8), default="ONE_TIME")
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
        CheckConstraint("status = 'PLANNED'", name="ck_planned_commitments_status"),
        CheckConstraint(
            "recurrence = 'ONE_TIME'", name="ck_planned_commitments_recurrence"
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
    status: Mapped[str] = mapped_column(String(7), default="PLANNED")
    recurrence: Mapped[str] = mapped_column(String(8), default="ONE_TIME")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
