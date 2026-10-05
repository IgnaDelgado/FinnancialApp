from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.domain.currency import Currency


class CashFlowResponse(BaseModel):
    currency: Currency
    liquid_cash: Decimal
    pending_bills: Decimal
    expected_income: Decimal
    negative_balances: Decimal
    overdue_income_count: int
    cash_after_bills: Decimal
    forecast_after_bills: Decimal


class HomeResponse(BaseModel):
    today: date
    month_end: date
    account_count: int
    commitment_count: int
    currencies: list[CashFlowResponse]
