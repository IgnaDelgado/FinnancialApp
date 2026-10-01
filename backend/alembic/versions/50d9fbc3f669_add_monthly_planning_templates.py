"""Add monthly planning templates without modifying existing one-time records."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "50d9fbc3f669"
down_revision: str | None = "2921b44cad5b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "monthly_plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(11), nullable=False),
        sa.Column("description", sa.String(100), nullable=False),
        sa.Column("amount", sa.Numeric(20, 2), nullable=False),
        sa.Column(
            "currency",
            sa.Enum(
                "ARS",
                "USD",
                name="monthly_plan_currency",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("first_date", sa.Date(), nullable=False),
        sa.Column("generated_through", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "kind IN ('income', 'commitments')", name="ck_monthly_plans_kind"
        ),
        sa.CheckConstraint("amount > 0", name="ck_monthly_plans_positive_amount"),
        sa.CheckConstraint(
            "length(trim(description)) > 0", name="ck_monthly_plans_description"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_monthly_plans_user_kind", "monthly_plans", ["user_id", "kind"])
    for table in ("planned_income", "planned_commitments"):
        op.add_column(table, sa.Column("template_id", sa.Uuid(), nullable=True))
        op.add_column(table, sa.Column("recurrence_period", sa.Date(), nullable=True))
        op.create_foreign_key(
            f"fk_{table}_template",
            table,
            "monthly_plans",
            ["template_id"],
            ["id"],
            ondelete="CASCADE",
        )
        op.create_unique_constraint(
            f"uq_{table}_template_period", table, ["template_id", "recurrence_period"]
        )
        op.drop_constraint(f"ck_{table}_recurrence", table, type_="check")
        op.create_check_constraint(
            f"ck_{table}_recurrence", table, "recurrence IN ('ONE_TIME', 'MONTHLY')"
        )
        op.create_check_constraint(
            f"ck_{table}_template",
            table,
            "(recurrence = 'MONTHLY' AND template_id IS NOT NULL "
            "AND recurrence_period IS NOT NULL) OR "
            "(recurrence = 'ONE_TIME' AND template_id IS NULL "
            "AND recurrence_period IS NULL)",
        )


def downgrade() -> None:
    # Do not silently destroy recurring records on rollback.
    count = op.get_bind().scalar(sa.text("SELECT count(*) FROM monthly_plans"))
    if count:
        raise RuntimeError(
            "Export/migrate monthly plans before downgrading; "
            "rollback would lose records"
        )
    for table in ("planned_income", "planned_commitments"):
        op.drop_constraint(f"ck_{table}_template", table, type_="check")
        op.drop_constraint(f"ck_{table}_recurrence", table, type_="check")
        op.create_check_constraint(
            f"ck_{table}_recurrence", table, "recurrence = 'ONE_TIME'"
        )
        op.drop_constraint(f"fk_{table}_template", table, type_="foreignkey")
        op.drop_constraint(f"uq_{table}_template_period", table, type_="unique")
        op.drop_column(table, "recurrence_period")
        op.drop_column(table, "template_id")
    op.drop_index("ix_monthly_plans_user_kind", table_name="monthly_plans")
    op.drop_table("monthly_plans")
