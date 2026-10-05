from decimal import Decimal

import pytest

from app.domain.confirmation import confirmed_balance
from app.domain.currency import Currency


@pytest.mark.parametrize("currency", [Currency.ARS, Currency.USD])
@pytest.mark.parametrize(
    ("balance", "amount", "income", "expected"),
    [
        ("0.00", "0.01", True, "0.01"),
        ("0.00", "0.01", False, "-0.01"),
        ("1250.25", "10.01", True, "1260.26"),
        ("1250.25", "10.01", False, "1240.24"),
        ("-10.00", "10.00", True, "0.00"),
        ("999999999999999999.98", "0.01", True, "999999999999999999.99"),
        ("-999999999999999999.98", "0.01", False, "-999999999999999999.99"),
    ],
)
def test_confirmed_balance_preserves_exact_money_and_signed_balances(
    currency: Currency,
    balance: str,
    amount: str,
    income: bool,
    expected: str,
) -> None:
    assert confirmed_balance(
        Decimal(balance), Decimal(amount), currency, currency, is_income=income
    ) == Decimal(expected)


@pytest.mark.parametrize(
    "amount", ["0", "-1", "1.001", "1.000", "NaN", "Infinity", "1000000000000000000"]
)
def test_confirmation_rejects_invalid_amount_without_rounding(amount: str) -> None:
    with pytest.raises(ValueError):
        confirmed_balance(
            Decimal("0.00"), Decimal(amount), Currency.ARS, Currency.ARS, is_income=True
        )


@pytest.mark.parametrize(
    ("balance", "income"),
    [
        ("999999999999999999.99", True),
        ("-999999999999999999.99", False),
        ("NaN", True),
        ("Infinity", False),
        ("1.001", True),
        ("1000000000000000000", True),
    ],
)
def test_confirmation_rejects_invalid_or_overflowing_balance(
    balance: str, income: bool
) -> None:
    with pytest.raises(ValueError):
        confirmed_balance(
            Decimal(balance),
            Decimal("0.01"),
            Currency.ARS,
            Currency.ARS,
            is_income=income,
        )


def test_confirmation_rejects_currency_mismatch() -> None:
    with pytest.raises(ValueError):
        confirmed_balance(
            Decimal("10.00"),
            Decimal("1.00"),
            Currency.ARS,
            Currency.USD,
            is_income=True,
        )
