from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from threading import Barrier
from typing import cast
from uuid import uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.database import get_engine
from app.domain.account import AccountType
from app.domain.currency import Currency
from app.models import (
    ConfirmationCorrection,
    FinancialAccount,
    MonthlyPlan,
    PlannedCommitment,
    PlannedIncome,
    User,
)
from app.services.financial_accounts import FinancialAccountService
from app.services.planning import PlanningService
from app.services.planning_maintenance import PlanningMaintenanceService


@pytest.mark.parametrize("is_income", [False, True])
def test_concurrent_stop_generation_and_correction_preserve_cash_once(
    is_income: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    for service in ("planning", "planning_maintenance"):
        monkeypatch.setattr(
            f"app.services.{service}.financial_today", lambda: date(2026, 10, 5)
        )
    engine = get_engine()
    user_id = uuid4()
    try:
        with Session(engine) as session:
            session.add(
                User(
                    id=user_id,
                    email=f"maintenance-{user_id}@example.com",
                    password_hash="synthetic",
                )
            )
            session.commit()
            account_id = (
                FinancialAccountService(session)
                .create(
                    user_id=user_id,
                    name="Synthetic",
                    account_type=AccountType.BANK,
                    currency=Currency.ARS,
                    initial_balance=Decimal("100.00"),
                    is_liquid=True,
                )
                .id
            )
            planning = PlanningService(session)
            # Keep typed branches to make the date semantics explicit.
            record: PlannedIncome | PlannedCommitment
            if is_income:
                record = planning.create_income(
                    user_id=user_id,
                    description="Synthetic",
                    amount=Decimal("0.01"),
                    currency=Currency.ARS,
                    expected_date=date(2026, 10, 5),
                    recurrence="MONTHLY",
                )
            else:
                record = planning.create_commitment(
                    user_id=user_id,
                    description="Synthetic",
                    amount=Decimal("0.01"),
                    currency=Currency.ARS,
                    due_date=date(2026, 10, 5),
                    recurrence="MONTHLY",
                )
            record_id, template_id = record.id, record.template_id
            assert template_id is not None
            confirmed = planning.confirm(
                user_id=user_id,
                record_id=record_id,
                account_id=account_id,
                already_in_balance=False,
                is_income=is_income,
            )
            confirmed_at = confirmed.confirmed_at
            assert confirmed_at is not None
        barrier = Barrier(4)

        def perform(action: str) -> None:
            barrier.wait(timeout=10)
            with Session(engine) as session:
                if action == "stop":
                    PlanningMaintenanceService(session).stop(
                        user_id, template_id, date(2026, 10, 1)
                    )
                elif action == "generate":
                    PlanningService(session).ensure_monthly_records(
                        user_id,
                        "income" if is_income else "commitments",
                        date(2026, 11, 1),
                        date(2026, 11, 30),
                    )
                else:
                    PlanningMaintenanceService(session).correct(
                        user_id, record_id, confirmed_at, is_income=is_income
                    )

        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(perform, ["correct", "correct", "stop", "generate"]))
        with Session(engine) as session:
            account = session.get(FinancialAccount, account_id)
            assert account is not None and account.current_balance == Decimal("100.00")
            model = PlannedIncome if is_income else PlannedCommitment
            records = list(
                cast(
                    Iterable[PlannedIncome | PlannedCommitment],
                    session.scalars(
                        select(model).where(model.user_id == user_id)
                    ).all(),
                )
            )
            assert records and all(record.status == "CANCELLED" for record in records)
            assert (
                len(
                    session.scalars(
                        select(ConfirmationCorrection).where(
                            ConfirmationCorrection.user_id == user_id
                        )
                    ).all()
                )
                == 1
            )
    finally:
        with Session(engine) as session:
            session.execute(delete(MonthlyPlan).where(MonthlyPlan.user_id == user_id))
            session.execute(delete(User).where(User.id == user_id))
            session.commit()
