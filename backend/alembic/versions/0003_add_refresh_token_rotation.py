"""Evolve user sessions into rotating refresh-token sessions.

Revision ID: 0003_add_refresh_token_rotation
Revises: 0002_create_user_sessions
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_add_refresh_token_rotation"
down_revision: str | None = "0002_create_user_sessions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "user_sessions",
        sa.Column("family_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "user_sessions",
        sa.Column("absolute_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "user_sessions",
        sa.Column("replaced_by_session_id", sa.Uuid(), nullable=True),
    )

    # Preserve legacy opaque sessions as first-generation refresh sessions.
    op.execute(
        """
        UPDATE user_sessions
        SET family_id = id,
            expires_at = LEAST(expires_at, created_at + INTERVAL '20 days'),
            absolute_expires_at = created_at + INTERVAL '90 days'
        """
    )

    op.alter_column("user_sessions", "family_id", nullable=False)
    op.alter_column("user_sessions", "absolute_expires_at", nullable=False)
    op.create_foreign_key(
        "fk_user_sessions_replaced_by_session_id_user_sessions",
        "user_sessions",
        "user_sessions",
        ["replaced_by_session_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_check_constraint(
        "ck_user_sessions_expiration_order",
        "user_sessions",
        "expires_at <= absolute_expires_at",
    )
    op.create_check_constraint(
        "ck_user_sessions_replacement_requires_revocation",
        "user_sessions",
        "replaced_by_session_id IS NULL OR revoked_at IS NOT NULL",
    )
    op.create_index(
        op.f("ix_user_sessions_family_id"),
        "user_sessions",
        ["family_id"],
        unique=False,
    )


def downgrade() -> None:
    # A refresh token must never become a 20-day bearer token after rollback.
    op.execute("UPDATE user_sessions SET revoked_at = now() WHERE revoked_at IS NULL")
    op.drop_index(op.f("ix_user_sessions_family_id"), table_name="user_sessions")
    op.drop_constraint(
        "ck_user_sessions_replacement_requires_revocation",
        "user_sessions",
        type_="check",
    )
    op.drop_constraint(
        "ck_user_sessions_expiration_order",
        "user_sessions",
        type_="check",
    )
    op.drop_constraint(
        "fk_user_sessions_replaced_by_session_id_user_sessions",
        "user_sessions",
        type_="foreignkey",
    )
    op.drop_column("user_sessions", "replaced_by_session_id")
    op.drop_column("user_sessions", "absolute_expires_at")
    op.drop_column("user_sessions", "family_id")
