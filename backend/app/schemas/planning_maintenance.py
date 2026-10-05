from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

from app.schemas.planning import IncomeCreateRequest, PlannedCreateRequest


class MonthlyEditRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    amount: Decimal = Field(max_digits=20, decimal_places=2)
    first_date: date

    @field_validator("amount", mode="before")
    @classmethod
    def reject_binary_float(cls, value: Any) -> Any:
        return PlannedCreateRequest.reject_binary_float(value)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        return PlannedCreateRequest.validate_amount(value)

    @field_validator("first_date", mode="before")
    @classmethod
    def validate_date_string(cls, value: Any) -> Any:
        return IncomeCreateRequest.validate_date_string(value)


class MonthlyStopRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    from_month: date

    @field_validator("from_month", mode="before")
    @classmethod
    def validate_date_string(cls, value: Any) -> Any:
        return IncomeCreateRequest.validate_date_string(value)


class CorrectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    original_confirmed_at: AwareDatetime


class MonthlyPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    stopped_from: date | None


class CorrectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    original_confirmed_at: datetime
    corrected_at: datetime
    account_id: UUID
    amount: Decimal
    currency: str
    already_in_balance: bool
    balance_before: Decimal | None
    balance_after: Decimal | None
