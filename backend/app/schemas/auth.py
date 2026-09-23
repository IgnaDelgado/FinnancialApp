from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.domain.currency import Currency


class UserRegistrationRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=15, max_length=128)
    reference_currency: Currency = Currency.ARS

    @field_validator("email", mode="before")
    @classmethod
    def strip_email_whitespace(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    reference_currency: Currency
    created_at: datetime
