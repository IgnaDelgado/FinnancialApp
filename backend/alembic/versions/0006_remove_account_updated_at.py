"""Remove unused duplicate account update timestamp.

Revision ID: 0006_remove_account_updated_at
Revises: 0005_signed_balances
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_remove_account_updated_at"
down_revision: str | None = "0005_signed_balances"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("financial_accounts", "updated_at")


def downgrade() -> None:
    op.add_column(
        "financial_accounts",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
