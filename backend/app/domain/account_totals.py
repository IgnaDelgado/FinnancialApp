from collections.abc import Iterable
from decimal import Decimal

from app.domain.currency import Currency


def sum_account_balances(
    balances: Iterable[tuple[Currency, Decimal]],
) -> dict[Currency, Decimal]:
    """Sum signed cash balances independently for each currency."""
    totals: dict[Currency, Decimal] = {}
    for currency, balance in balances:
        totals[currency] = totals.get(currency, Decimal("0.00")) + balance
    return totals
