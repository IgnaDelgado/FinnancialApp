from datetime import date
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import delete, event
from sqlalchemy.orm import Session

from app.core.database import get_engine
from app.domain.account import AccountType
from app.domain.currency import Currency
from app.models.planning import PlannedCommitment, PlannedIncome
from app.models.user import User
from app.services.financial_accounts import FinancialAccountService
from app.services.home import HomeService
from app.services.planning import PlanningService


@pytest.mark.parametrize("is_income", [False, True])
@pytest.mark.parametrize("included", [False, True])
def test_home_reads_one_consistent_snapshot_during_confirmation(
    is_income: bool, included: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    today = date(2026, 10, 5)
    monkeypatch.setattr("app.services.home.financial_today", lambda: today)
    monkeypatch.setattr("app.services.planning.financial_today", lambda: today)
    engine = get_engine()
    user_id = uuid4()
    fired = False
    try:
        with Session(engine) as session:
            session.add(
                User(
                    id=user_id,
                    email=f"snapshot-{user_id}@example.com",
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
            service = PlanningService(session)
            if is_income:
                record_id = service.create_income(
                    user_id=user_id,
                    description="Synthetic",
                    amount=Decimal("20.00"),
                    currency=Currency.ARS,
                    expected_date=today,
                ).id
            else:
                record_id = service.create_commitment(
                    user_id=user_id,
                    description="Synthetic",
                    amount=Decimal("20.00"),
                    currency=Currency.ARS,
                    due_date=today,
                ).id

        def confirm_between_reads(
            connection: Any,
            cursor: Any,
            statement: str,
            parameters: Any,
            context: Any,
            executemany: bool,
        ) -> None:
            nonlocal fired
            if (
                not fired
                and statement.startswith("SELECT")
                and "financial_accounts.current_balance" in statement
            ):
                fired = True
                with Session(engine) as other:
                    PlanningService(other).confirm(
                        user_id=user_id,
                        record_id=record_id,
                        account_id=account_id,
                        already_in_balance=included,
                        is_income=is_income,
                    )

        event.listen(engine, "after_cursor_execute", confirm_between_reads)
        try:
            with Session(engine) as session:
                flow = HomeService(session).snapshot(user_id).currencies[0]
                assert fired
                # The SELECT started before confirmation: all components must
                # reflect that state, even though confirmation has now committed.
                assert flow.liquid_cash == Decimal("100.00")
                assert flow.pending_bills == Decimal("0.00" if is_income else "20.00")
                assert flow.expected_income == Decimal("20.00" if is_income else "0.00")
                assert flow.forecast_after_bills == Decimal(
                    "120.00" if is_income else "80.00"
                )
            with Session(engine) as session:
                after = HomeService(session).snapshot(user_id).currencies[0]
                expected = "100.00" if included else "120.00" if is_income else "80.00"
                assert after.liquid_cash == Decimal(expected)
                assert after.pending_bills == after.expected_income == Decimal("0.00")
        finally:
            event.remove(engine, "after_cursor_execute", confirm_between_reads)
    finally:
        with Session(engine) as session:
            session.execute(
                delete(PlannedIncome).where(PlannedIncome.user_id == user_id)
            )
            session.execute(
                delete(PlannedCommitment).where(PlannedCommitment.user_id == user_id)
            )
            session.execute(delete(User).where(User.id == user_id))
            session.commit()
