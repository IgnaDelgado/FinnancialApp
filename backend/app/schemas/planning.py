from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.currency import Currency
from app.domain.planning import validate_planned_amount


class PlannedCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str = Field(min_length=1, max_length=100)
    amount: Decimal = Field(max_digits=20, decimal_places=2)
    currency: Currency
    recurrence: Literal["ONE_TIME", "MONTHLY"] = "ONE_TIME"

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Description cannot be blank")
        return value.strip()

    @field_validator("amount", mode="before")
    @classmethod
    def reject_binary_float(cls, value: Any) -> Any:
        if isinstance(value, (float, bool)):
            raise ValueError("Use a decimal string for money")
        return value

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        return validate_planned_amount(value)


class IncomeCreateRequest(PlannedCreateRequest):
    expected_date: date

    @field_validator("expected_date", mode="before")
    @classmethod
    def validate_date_string(cls, value: Any) -> Any:
        if not isinstance(value, str) or len(value) != 10:
            raise ValueError("Use an ISO calendar date")
        return value


class CommitmentCreateRequest(PlannedCreateRequest):
    due_date: date

    @field_validator("due_date", mode="before")
    @classmethod
    def validate_date_string(cls, value: Any) -> Any:
        if not isinstance(value, str) or len(value) != 10:
            raise ValueError("Use an ISO calendar date")
        return value


class PlannedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    description: str
    amount: Decimal
    currency: Currency
    recurrence: Literal["ONE_TIME", "MONTHLY"]
    template_id: UUID | None
    account_id: UUID | None
    confirmed_at: datetime | None
    already_in_balance: bool | None
    created_at: datetime


class IncomeResponse(PlannedResponse):
    status: Literal["PLANNED", "RECEIVED"]
    expected_date: date


class CommitmentResponse(PlannedResponse):
    status: Literal["PLANNED", "PAID"]
    due_date: date


class ConfirmationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: UUID
    already_in_balance: bool = Field(strict=True)
