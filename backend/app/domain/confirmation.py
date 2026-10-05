from decimal import Decimal

from app.domain.currency import Currency
from app.domain.planning import MAX_AMOUNT, validate_planned_amount


def confirmed_balance(
    balance: Decimal,
    amount: Decimal,
    account_currency: Currency,
    movement_currency: Currency,
    *,
    is_income: bool,
) -> Decimal:
    """Apply one full cash movement without rounding or currency conversion."""
    validate_planned_amount(amount)
    if account_currency != movement_currency:
        raise ValueError("La cuenta y el movimiento deben tener la misma moneda.")
    if not balance.is_finite() or abs(balance) > MAX_AMOUNT:
        raise ValueError("Saldo inválido.")
    exponent = balance.as_tuple().exponent
    if not isinstance(exponent, int) or exponent < -2:
        raise ValueError("El saldo admite como máximo dos decimales.")
    result = balance + amount if is_income else balance - amount
    if abs(result) > MAX_AMOUNT:
        raise ValueError("El saldo resultante supera el límite admitido.")
    return result
