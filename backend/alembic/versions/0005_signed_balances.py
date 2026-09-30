"""Allow signed account balances and balance snapshots.

Revision ID: 0005_signed_balances
Revises: 0004_create_financial_accounts
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005_signed_balances"
down_revision: str | None = "0004_create_financial_accounts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_financial_accounts_nonnegative_balance",
        "financial_accounts",
        type_="check",
    )
    op.drop_constraint(
        "ck_account_balance_snapshots_nonnegative_balance",
        "account_balance_snapshots",
        type_="check",
    )


def downgrade() -> None:
    op.create_check_constraint(
        "ck_financial_accounts_nonnegative_balance",
        "financial_accounts",
        "current_balance >= 0",
    )
    op.create_check_constraint(
        "ck_account_balance_snapshots_nonnegative_balance",
        "account_balance_snapshots",
        "balance >= 0",
    )
