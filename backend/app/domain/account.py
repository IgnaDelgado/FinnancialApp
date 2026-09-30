from enum import StrEnum


class AccountType(StrEnum):
    CASH = "CASH"
    BANK = "BANK"
    DIGITAL_WALLET = "DIGITAL_WALLET"
    FOREIGN_CURRENCY = "FOREIGN_CURRENCY"
    INVESTMENT = "INVESTMENT"
    OTHER = "OTHER"


DEFAULT_LIQUID_ACCOUNT_TYPES = frozenset(
    {
        AccountType.CASH,
        AccountType.BANK,
        AccountType.DIGITAL_WALLET,
        AccountType.FOREIGN_CURRENCY,
    }
)
