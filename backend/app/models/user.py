from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Enum, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.currency import Currency
from app.models.base import Base


class User(Base):
    """Persisted application user and authentication identity."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("email = lower(email)", name="ck_users_email_normalized"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    reference_currency: Mapped[Currency] = mapped_column(
        Enum(
            Currency,
            name="reference_currency",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            length=3,
        ),
        default=Currency.ARS,
        server_default=Currency.ARS.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
