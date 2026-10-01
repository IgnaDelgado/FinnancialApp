from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.account import AccountType
from app.domain.currency import Currency


class AccountCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    account_type: AccountType
    currency: Currency
    initial_balance: Decimal = Field(max_digits=20, decimal_places=2)
    is_liquid: bool | None = None

    @field_validator("name")
    @classmethod
    def strip_and_validate_name(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("Account name cannot be blank")
        return name


class AccountBalanceUpdateRequest(BaseModel):
    balance: Decimal = Field(max_digits=20, decimal_places=2)


class AccountCashTotalResponse(BaseModel):
    currency: Currency
    balance: Decimal


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    account_type: AccountType
    currency: Currency
    current_balance: Decimal
    is_liquid: bool
    balance_updated_at: datetime
    archived_at: datetime | None
    created_at: datetime


class AccountBalanceSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    balance: Decimal
    recorded_at: datetime
