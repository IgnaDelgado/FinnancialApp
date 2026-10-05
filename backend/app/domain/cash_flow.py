from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.domain.currency import Currency


@dataclass(frozen=True)
class CashFlowSnapshot:
    currency: Currency
    liquid_cash: Decimal
    pending_bills: Decimal
    expected_income: Decimal
    negative_balances: Decimal
    overdue_income_count: int

    @property
    def cash_after_bills(self) -> Decimal:
        return self.liquid_cash - self.pending_bills

    @property
    def forecast_after_bills(self) -> Decimal:
        return self.cash_after_bills + self.expected_income


def cash_flow_snapshot(
    currency: Currency,
    today: date,
    month_end: date,
    accounts: Iterable[tuple[Currency, Decimal, bool]],
    commitments: Iterable[tuple[Currency, Decimal, date]],
    income: Iterable[tuple[Currency, Decimal, date]],
) -> CashFlowSnapshot:
    """Limited cash-flow diagnostic, never the full available-money formula."""
    liquid_cash = Decimal("0.00")
    negatives = Decimal("0.00")
    bills = Decimal("0.00")
    expected = Decimal("0.00")
    overdue_income = 0
    for unit, balance, liquid in accounts:
        if unit != currency:
            continue
        if balance < 0:
            negatives += balance
        elif liquid:
            liquid_cash += balance
    for unit, amount, due_date in commitments:
        if unit == currency and due_date <= month_end:
            bills += amount
    for unit, amount, expected_date in income:
        if unit == currency:
            if today <= expected_date <= month_end:
                expected += amount
            elif expected_date < today:
                overdue_income += 1
    return CashFlowSnapshot(
        currency, liquid_cash, bills, expected, negatives, overdue_income
    )
