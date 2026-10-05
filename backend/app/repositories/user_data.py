from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Numeric, String, cast, func, literal, select, union_all
from sqlalchemy.orm import Session

from app.models import (
    AccountBalanceSnapshot,
    ConfirmationCorrection,
    FinancialAccount,
    MonthlyPlan,
    MonthlyPlanChange,
    PlannedCommitment,
    PlannedIncome,
    User,
)


class UserDataRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def export(self, user_id: UUID) -> dict[str, object]:
        # PostgreSQL creates JSON rows in one SELECT snapshot. Cast every NUMERIC
        # to text before JSON encoding, preserving exact money at the boundary.
        owned_accounts = select(FinancialAccount.id).where(
            FinancialAccount.user_id == user_id
        )
        owned_templates = select(MonthlyPlan.id).where(MonthlyPlan.user_id == user_id)
        sources = [
            ("profile", User.__table__, User.id == user_id),
            (
                "accounts",
                FinancialAccount.__table__,
                FinancialAccount.user_id == user_id,
            ),
            (
                "balance_history",
                AccountBalanceSnapshot.__table__,
                AccountBalanceSnapshot.account_id.in_(owned_accounts),
            ),
            ("monthly_plans", MonthlyPlan.__table__, MonthlyPlan.user_id == user_id),
            (
                "monthly_plan_changes",
                MonthlyPlanChange.__table__,
                MonthlyPlanChange.template_id.in_(owned_templates),
            ),
            ("income", PlannedIncome.__table__, PlannedIncome.user_id == user_id),
            (
                "commitments",
                PlannedCommitment.__table__,
                PlannedCommitment.user_id == user_id,
            ),
            (
                "confirmation_corrections",
                ConfirmationCorrection.__table__,
                ConfirmationCorrection.user_id == user_id,
            ),
        ]
        statements = []
        for name, table, owned in sources:
            pairs = []
            for column in table.columns:
                if name == "profile" and column.name not in {
                    "id",
                    "email",
                    "reference_currency",
                    "created_at",
                    "updated_at",
                }:
                    continue
                pairs.extend(
                    [
                        literal(column.name),
                        cast(column, String)
                        if isinstance(column.type, Numeric)
                        else column,
                    ]
                )
            statements.append(
                select(
                    literal(name).label("source"),
                    func.jsonb_build_object(*pairs).label("record"),
                ).where(owned)
            )
        rows = self._session.execute(union_all(*statements))
        result: dict[str, object] = {
            "schema_version": 1,
            "exported_at": datetime.now(UTC).isoformat(),
        }
        grouped: dict[str, list[dict[str, object]]] = {
            name: [] for name, _, _ in sources
        }
        for name, record in rows:
            grouped[name].append(record)
        result.update(grouped)
        return result
