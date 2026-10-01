from calendar import monthrange
from collections.abc import Iterator
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

FINANCIAL_TIMEZONE = ZoneInfo("America/Argentina/Cordoba")
MAX_AMOUNT = Decimal("999999999999999999.99")


def validate_planned_amount(amount: Decimal) -> Decimal:
    """Reject invalid input instead of rounding it to fit storage."""
    exponent = amount.as_tuple().exponent
    if (
        not amount.is_finite()
        or amount <= 0
        or amount > MAX_AMOUNT
        or not isinstance(exponent, int)
        or exponent < -2
    ):
        raise ValueError("Amount must be positive and fit NUMERIC(20,2)")
    return amount


def financial_today() -> date:
    return datetime.now(FINANCIAL_TIMEZONE).date()


def month_bounds(year: int, month: int) -> tuple[date, date]:
    """Inclusive boundaries, including December of the maximum date year."""
    return date(year, month, 1), date(year, month, monthrange(year, month)[1])


def monthly_dates(first_date: date, start: date, end: date) -> Iterator[date]:
    """Keep the original day, clamping only the occurrence in a short month."""
    period = max(first_date.replace(day=1), start.replace(day=1))
    while period <= end:
        occurrence = period.replace(
            day=min(first_date.day, monthrange(period.year, period.month)[1])
        )
        if occurrence >= first_date and start <= occurrence <= end:
            yield occurrence
        if period.year == 9999 and period.month == 12:
            break
        period = date(period.year + (period.month == 12), period.month % 12 + 1, 1)
