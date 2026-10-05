"""Add full account-linked confirmation without changing planned records."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_confirm_planning_records"
down_revision: str | None = "50d9fbc3f669"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table, completed in [
        ("planned_income", "RECEIVED"),
        ("planned_commitments", "PAID"),
    ]:
        op.drop_constraint(f"ck_{table}_status", table, type_="check")
        if table == "planned_income":
            op.alter_column(
                table, "status", type_=sa.String(8), existing_type=sa.String(7)
            )
        op.add_column(table, sa.Column("account_id", sa.Uuid(), nullable=True))
        op.add_column(
            table, sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True)
        )
        op.add_column(
            table, sa.Column("already_in_balance", sa.Boolean(), nullable=True)
        )
        op.create_foreign_key(
            f"fk_{table}_account_id",
            table,
            "financial_accounts",
            ["account_id"],
            ["id"],
        )
        op.create_check_constraint(
            f"ck_{table}_status", table, f"status IN ('PLANNED', '{completed}')"
        )
        op.create_check_constraint(
            f"ck_{table}_confirmation",
            table,
            "(status = 'PLANNED' AND account_id IS NULL AND confirmed_at IS NULL "
            "AND already_in_balance IS NULL) OR "
            f"(status = '{completed}' AND account_id IS NOT NULL "
            "AND confirmed_at IS NOT NULL AND already_in_balance IS NOT NULL)",
        )


def downgrade() -> None:
    # Confirmed records cannot be turned back into plans without duplicating
    # real movements. Refuse rollback rather than destroy their audit history.
    connection = op.get_bind()
    for table in ("planned_income", "planned_commitments"):
        if connection.scalar(
            sa.text(f"SELECT count(*) FROM {table} WHERE status <> 'PLANNED'")
        ):
            raise RuntimeError("Cannot downgrade while confirmed movements exist")
    for table in ("planned_income", "planned_commitments"):
        op.drop_constraint(f"ck_{table}_confirmation", table, type_="check")
        op.drop_constraint(f"ck_{table}_status", table, type_="check")
        op.drop_constraint(f"fk_{table}_account_id", table, type_="foreignkey")
        for column in ("account_id", "confirmed_at", "already_in_balance"):
            op.drop_column(table, column)
        if table == "planned_income":
            op.alter_column(
                table, "status", type_=sa.String(7), existing_type=sa.String(8)
            )
        op.create_check_constraint(f"ck_{table}_status", table, "status = 'PLANNED'")
