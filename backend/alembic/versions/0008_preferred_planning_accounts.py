"""Remember accounts for recurring cash movements without applying money."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008_preferred_accounts"
down_revision: str | None = "0007_confirm_planning_records"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table in ("monthly_plans", "planned_income", "planned_commitments"):
        op.add_column(
            table, sa.Column("preferred_account_id", sa.Uuid(), nullable=True)
        )
        op.create_foreign_key(
            f"fk_{table}_preferred_account",
            table,
            "financial_accounts",
            ["preferred_account_id"],
            ["id"],
        )
        if table != "monthly_plans":
            op.add_column(
                table,
                sa.Column(
                    "remember_account",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.false(),
                ),
            )


def downgrade() -> None:
    connection = op.get_bind()
    for table in ("planned_income", "planned_commitments"):
        if connection.scalar(
            sa.text(f"SELECT count(*) FROM {table} WHERE remember_account")
        ):
            raise RuntimeError("Cannot remove remembered confirmation history")
    for table in ("monthly_plans", "planned_income", "planned_commitments"):
        if table != "monthly_plans":
            op.drop_column(table, "remember_account")
        op.drop_constraint(f"fk_{table}_preferred_account", table, type_="foreignkey")
        op.drop_column(table, "preferred_account_id")
