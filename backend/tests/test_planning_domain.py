from datetime import date
from decimal import Decimal

import pytest

from app.domain.planning import month_bounds, validate_planned_amount


@pytest.mark.parametrize(
    "amount", ["0", "-1", "1.001", "1.000", "1000000000000000000", "NaN", "Infinity"]
)
def test_planned_amount_rejects_invalid_values(amount: str) -> None:
    with pytest.raises(ValueError):
        validate_planned_amount(Decimal(amount))


def test_planned_amount_preserves_exact_input_without_rounding() -> None:
    assert validate_planned_amount(Decimal("999999999999999999.99")) == Decimal(
        "999999999999999999.99"
    )
    assert validate_planned_amount(Decimal("0.01")) == Decimal("0.01")


def test_month_boundaries_include_leap_day_and_last_supported_date() -> None:
    assert month_bounds(2024, 2) == (date(2024, 2, 1), date(2024, 2, 29))
    assert month_bounds(9999, 12) == (date(9999, 12, 1), date(9999, 12, 31))
