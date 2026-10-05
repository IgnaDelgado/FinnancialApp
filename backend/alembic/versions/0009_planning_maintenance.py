"""Preserve monthly edit versions and confirmation correction history."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009_planning_maintenance"
down_revision: str | None = "0008_preferred_accounts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("monthly_plans", sa.Column("stopped_from", sa.Date(), nullable=True))
    for table, completed in [
        ("planned_income", "RECEIVED"),
        ("planned_commitments", "PAID"),
    ]:
        op.drop_constraint(f"ck_{table}_confirmation", table, type_="check")
        op.drop_constraint(f"ck_{table}_status", table, type_="check")
        op.alter_column(
            table,
            "status",
            type_=sa.String(9),
            existing_type=sa.String(8 if completed == "RECEIVED" else 7),
        )
        op.create_check_constraint(
            f"ck_{table}_status",
            table,
            f"status IN ('PLANNED', '{completed}', 'CANCELLED')",
        )
        op.create_check_constraint(
            f"ck_{table}_confirmation",
            table,
            "(status IN ('PLANNED', 'CANCELLED') AND account_id IS NULL "
            "AND confirmed_at IS NULL "
            "AND already_in_balance IS NULL) OR "
            f"(status = '{completed}' AND account_id IS NOT NULL "
            "AND confirmed_at IS NOT NULL AND already_in_balance IS NOT NULL)",
        )
    op.create_table(
        "monthly_plan_changes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "template_id",
            sa.Uuid(),
            sa.ForeignKey("monthly_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("effective_period", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(20, 2), nullable=False),
        sa.Column("day", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("amount > 0", name="ck_monthly_changes_positive_amount"),
        sa.CheckConstraint("day BETWEEN 1 AND 31", name="ck_monthly_changes_day"),
    )
    op.create_index(
        "ix_monthly_changes_plan_period",
        "monthly_plan_changes",
        ["template_id", "effective_period", "id"],
    )
    op.create_table(
        "confirmation_corrections",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "income_id",
            sa.Uuid(),
            sa.ForeignKey("planned_income.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "commitment_id",
            sa.Uuid(),
            sa.ForeignKey("planned_commitments.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "account_id",
            sa.Uuid(),
            sa.ForeignKey("financial_accounts.id"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(20, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("already_in_balance", sa.Boolean(), nullable=False),
        sa.Column("remember_account", sa.Boolean(), nullable=False),
        sa.Column("original_confirmed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("corrected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("balance_before", sa.Numeric(20, 2), nullable=True),
        sa.Column("balance_after", sa.Numeric(20, 2), nullable=True),
        sa.CheckConstraint(
            "(income_id IS NULL) <> (commitment_id IS NULL)",
            name="ck_corrections_one_record",
        ),
        sa.CheckConstraint("amount > 0", name="ck_corrections_positive_amount"),
        sa.CheckConstraint(
            "currency IN ('ARS', 'USD')", name="ck_corrections_currency"
        ),
        sa.UniqueConstraint(
            "income_id",
            "original_confirmed_at",
            name="uq_corrections_income_confirmation",
        ),
        sa.UniqueConstraint(
            "commitment_id",
            "original_confirmed_at",
            name="uq_corrections_commitment_confirmation",
        ),
    )
    op.create_index(
        "ix_confirmation_corrections_user_id", "confirmation_corrections", ["user_id"]
    )


def downgrade() -> None:
    connection = op.get_bind()
    for table in ("monthly_plan_changes", "confirmation_corrections"):
        if connection.scalar(sa.text(f"SELECT count(*) FROM {table}")):
            raise RuntimeError("Cannot remove planning maintenance audit history")
    if connection.scalar(
        sa.text("SELECT count(*) FROM monthly_plans WHERE stopped_from IS NOT NULL")
    ):
        raise RuntimeError("Cannot remove stopped monthly plans")
    op.drop_table("confirmation_corrections")
    op.drop_table("monthly_plan_changes")
    op.drop_column("monthly_plans", "stopped_from")
    for table, completed in [
        ("planned_income", "RECEIVED"),
        ("planned_commitments", "PAID"),
    ]:
        op.drop_constraint(f"ck_{table}_confirmation", table, type_="check")
        op.drop_constraint(f"ck_{table}_status", table, type_="check")
        op.alter_column(
            table,
            "status",
            type_=sa.String(8 if completed == "RECEIVED" else 7),
            existing_type=sa.String(9),
        )
        op.create_check_constraint(
            f"ck_{table}_status", table, f"status IN ('PLANNED', '{completed}')"
        )
        op.create_check_constraint(
            f"ck_{table}_confirmation",
            table,
            "(status = 'PLANNED' AND account_id IS NULL "
            "AND confirmed_at IS NULL AND already_in_balance IS NULL) OR "
            f"(status = '{completed}' AND account_id IS NOT NULL "
            "AND confirmed_at IS NOT NULL AND already_in_balance IS NOT NULL)",
        )
