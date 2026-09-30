"""Create cash accounts and balance snapshots.

Revision ID: 0004_create_financial_accounts
Revises: 0003_add_refresh_token_rotation
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_create_financial_accounts"
down_revision: str | None = "0003_add_refresh_token_rotation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "financial_accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "account_type",
            sa.Enum(
                "CASH",
                "BANK",
                "DIGITAL_WALLET",
                "FOREIGN_CURRENCY",
                "INVESTMENT",
                "OTHER",
                name="financial_account_type",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "currency",
            sa.Enum(
                "ARS",
                "USD",
                name="financial_account_currency",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("current_balance", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("is_liquid", sa.Boolean(), nullable=False),
        sa.Column("balance_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "current_balance >= 0", name="ck_financial_accounts_nonnegative_balance"
        ),
        sa.CheckConstraint(
            "length(trim(name)) > 0", name="ck_financial_accounts_name_not_blank"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_financial_accounts_user_id", "financial_accounts", ["user_id"])
    op.create_table(
        "account_balance_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("balance", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "balance >= 0", name="ck_account_balance_snapshots_nonnegative_balance"
        ),
        sa.ForeignKeyConstraint(
            ["account_id"], ["financial_accounts.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_account_balance_snapshots_account_id",
        "account_balance_snapshots",
        ["account_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_account_balance_snapshots_account_id",
        table_name="account_balance_snapshots",
    )
    op.drop_table("account_balance_snapshots")
    op.drop_index("ix_financial_accounts_user_id", table_name="financial_accounts")
    op.drop_table("financial_accounts")
