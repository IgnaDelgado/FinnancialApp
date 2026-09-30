from decimal import Decimal

from app.domain.account_totals import sum_account_balances
from app.domain.currency import Currency


def test_signed_account_totals_do_not_offset_a_positive_account_balance() -> None:
    balances = [
        (Currency.ARS, Decimal("30000.00")),
        (Currency.ARS, Decimal("-20000.00")),
    ]

    assert balances[0][1] == Decimal("30000.00")
    assert sum_account_balances(balances) == {Currency.ARS: Decimal("10000.00")}


def test_account_totals_keep_currencies_separate_and_preserve_cents() -> None:
    assert sum_account_balances(
        [
            (Currency.ARS, Decimal("0.00")),
            (Currency.ARS, Decimal("0.01")),
            (Currency.ARS, Decimal("-0.02")),
            (Currency.USD, Decimal("0.03")),
        ]
    ) == {Currency.ARS: Decimal("-0.01"), Currency.USD: Decimal("0.03")}


def test_account_totals_are_empty_without_accounts() -> None:
    assert sum_account_balances([]) == {}
