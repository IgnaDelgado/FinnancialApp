from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, event, func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import (
    AccountBalanceSnapshot,
    ConfirmationCorrection,
    FinancialAccount,
    MonthlyPlan,
    MonthlyPlanChange,
    PlannedCommitment,
    PlannedIncome,
    User,
    UserSession,
)
from tests.test_financial_accounts_api import _create_account, _headers

PASSWORD = "synthetic deletion passphrase"


def _setup(
    client: TestClient, session: Session, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict[str, str], UUID]:
    for service in ("planning", "planning_maintenance", "home"):
        monkeypatch.setattr(
            f"app.services.{service}.financial_today", lambda: date(2026, 10, 5)
        )
    headers = _headers(session, "data-owner@example.com")
    user = session.scalar(select(User).where(User.email == "data-owner@example.com"))
    assert user is not None
    user.password_hash = hash_password(PASSWORD)
    session.commit()
    account = _create_account(client, headers, balance="999999999999999999.99")
    for kind, field in [("income", "expected_date"), ("commitments", "due_date")]:
        record = client.post(
            f"/api/v1/{kind}",
            headers=headers,
            json={
                "description": "Synthetic",
                "amount": "0.01",
                "currency": "ARS",
                field: "2026-10-31",
                "recurrence": "MONTHLY",
                "preferred_account_id": account["id"],
            },
        ).json()
        confirmed = client.post(
            f"/api/v1/{kind}/{record['id']}/confirm",
            headers=headers,
            json={"account_id": account["id"], "already_in_balance": True},
        ).json()
        assert (
            client.post(
                f"/api/v1/{kind}/{record['id']}/correct",
                headers=headers,
                json={"original_confirmed_at": confirmed["confirmed_at"]},
            ).status_code
            == 200
        )
        assert (
            client.post(
                f"/api/v1/{kind}/{record['id']}/confirm",
                headers=headers,
                json={"account_id": account["id"], "already_in_balance": True},
            ).status_code
            == 200
        )
        assert (
            client.post(
                f"/api/v1/monthly-plans/{record['template_id']}/edit",
                headers=headers,
                json={"amount": "10.02", "first_date": "2026-11-30"},
            ).status_code
            == 200
        )
        assert (
            client.get(
                f"/api/v1/{kind}?year=2026&month=11", headers=headers
            ).status_code
            == 200
        )
        assert (
            client.post(
                f"/api/v1/monthly-plans/{record['template_id']}/stop",
                headers=headers,
                json={"from_month": "2026-11-01"},
            ).status_code
            == 200
        )
    assert (
        client.delete(f"/api/v1/accounts/{account['id']}", headers=headers).status_code
        == 204
    )
    assert (
        client.post(
            "/api/v1/auth/login", json={"email": user.email, "password": PASSWORD}
        ).status_code
        == 200
    )
    return headers, user.id


def test_export_preserves_complete_owned_history_and_excludes_authentication_secrets(
    api_client: TestClient, database_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers, user_id = _setup(api_client, database_session, monkeypatch)
    other = _headers(database_session, "export-other@example.com")
    _create_account(api_client, other, balance="42.00")
    before = database_session.scalar(select(func.count()).select_from(PlannedIncome))
    response = api_client.get("/api/v1/user-data/export", headers=headers)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    data = response.json()
    assert data["schema_version"] == 1
    assert data["profile"][0]["id"] == str(user_id)
    assert len(data["accounts"]) == 1
    assert data["accounts"][0]["archived_at"] is not None
    assert data["accounts"][0]["current_balance"] == "999999999999999999.99"
    assert len(data["balance_history"]) == 1
    assert len(data["monthly_plan_changes"]) == 2
    assert len(data["confirmation_corrections"]) == 2
    assert {row["status"] for row in data["income"]} == {"RECEIVED", "CANCELLED"}
    assert data["income"][0]["amount"] in {"0.01", "10.02"}
    assert "password_hash" not in response.text
    assert "token_hash" not in response.text and "refresh_token" not in response.text
    assert "export-other@example.com" not in response.text
    assert (
        database_session.scalar(select(func.count()).select_from(PlannedIncome))
        == before
    )
    assert api_client.get("/api/v1/user-data/export").status_code == 401


@pytest.mark.parametrize("invalid", ["wrong password", "", "x" * 129])
def test_deletion_requires_current_password_without_changing_data(
    api_client: TestClient, database_session: Session, invalid: str
) -> None:
    headers = _headers(database_session, "password-owner@example.com")
    user = database_session.scalar(
        select(User).where(User.email == "password-owner@example.com")
    )
    assert user is not None
    user.password_hash = hash_password(PASSWORD)
    database_session.commit()
    _create_account(api_client, headers)
    response = api_client.request(
        "DELETE", "/api/v1/user-data", headers=headers, json={"password": invalid}
    )
    assert response.status_code == (403 if invalid == "wrong password" else 422)
    assert api_client.get("/api/v1/auth/me", headers=headers).status_code == 200
    assert len(api_client.get("/api/v1/accounts", headers=headers).json()) == 1


def test_deletion_cascades_all_user_data_and_invalidates_all_sessions(
    api_client: TestClient, database_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers, user_id = _setup(api_client, database_session, monkeypatch)
    login = api_client.post(
        "/api/v1/auth/login",
        json={"email": "data-owner@example.com", "password": PASSWORD},
    ).json()
    other = _headers(database_session, "delete-other@example.com")
    _create_account(api_client, other)
    assert (
        api_client.request(
            "DELETE", "/api/v1/user-data", json={"password": PASSWORD}
        ).status_code
        == 401
    )
    response = api_client.request(
        "DELETE", "/api/v1/user-data", headers=headers, json={"password": PASSWORD}
    )
    assert response.status_code == 204
    assert api_client.get("/api/v1/auth/me", headers=headers).status_code == 401
    assert (
        api_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]}
        ).status_code
        == 401
    )
    assert (
        api_client.post(
            "/api/v1/auth/login",
            json={"email": "data-owner@example.com", "password": PASSWORD},
        ).status_code
        == 401
    )
    assert api_client.get("/api/v1/auth/me", headers=other).status_code == 200
    assert len(api_client.get("/api/v1/accounts", headers=other).json()) == 1
    for model in (
        UserSession,
        FinancialAccount,
        PlannedIncome,
        PlannedCommitment,
        MonthlyPlan,
        ConfirmationCorrection,
    ):
        assert (
            database_session.scalar(
                select(func.count()).select_from(model).where(model.user_id == user_id)
            )
            == 0
        )
    assert (
        database_session.scalar(select(func.count()).select_from(MonthlyPlanChange))
        == 0
    )
    assert (
        database_session.scalar(
            select(func.count()).select_from(AccountBalanceSnapshot)
        )
        == 1
    )


def test_export_preserves_balance_and_history_consistency_during_update() -> None:
    from app.core.database import get_engine
    from app.domain.account import AccountType
    from app.domain.currency import Currency
    from app.repositories.user_data import UserDataRepository
    from app.services.financial_accounts import FinancialAccountService

    engine = get_engine()
    user_id = uuid4()
    changed = False
    try:
        with Session(engine) as session:
            session.add(
                User(
                    id=user_id,
                    email=f"export-{user_id}@example.com",
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

        def update_during_export(
            connection: Any,
            cursor: Any,
            statement: str,
            parameters: Any,
            context: Any,
            executemany: bool,
        ) -> None:
            nonlocal changed
            if (
                not changed
                and statement.startswith("SELECT")
                and "jsonb_build_object" in statement
            ):
                changed = True
                with Session(engine) as other:
                    FinancialAccountService(other).update_balance(
                        user_id=user_id, account_id=account_id, balance=Decimal("50.00")
                    )

        event.listen(engine, "after_cursor_execute", update_during_export)
        try:
            with Session(engine) as session:
                data = UserDataRepository(session).export(user_id)
                assert changed
                assert isinstance(data["accounts"], list) and isinstance(
                    data["balance_history"], list
                )
                assert data["accounts"][0]["current_balance"] == "100.00"
                assert len(data["balance_history"]) == 1
                assert data["balance_history"][0]["balance"] == "100.00"
        finally:
            event.remove(engine, "after_cursor_execute", update_during_export)
    finally:
        with Session(engine) as session:
            session.execute(delete(User).where(User.id == user_id))
            session.commit()
