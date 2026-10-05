from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.database import get_engine
from app.domain.account import AccountType
from app.domain.currency import Currency
from app.models.planning import MonthlyPlan, PlannedIncome
from app.models.user import User
from app.services.financial_accounts import FinancialAccountService
from app.services.planning import PlanningService
from tests.test_financial_accounts_api import _create_account, _headers


@pytest.mark.parametrize(
    ("kind", "field"), [("income", "expected_date"), ("commitments", "due_date")]
)
def test_monthly_creation_inherits_saved_account_without_changing_money(
    api_client: TestClient,
    database_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
    field: str,
) -> None:
    monkeypatch.setattr(
        "app.services.planning.financial_today", lambda: date(2026, 10, 5)
    )
    headers = _headers(database_session, "preferred-owner@example.com")
    account = _create_account(api_client, headers, currency="USD", balance="0.00")
    response = api_client.post(
        f"/api/v1/{kind}",
        headers=headers,
        json={
            "description": "Synthetic monthly",
            "amount": "0.01",
            "currency": "USD",
            field: "2026-10-05",
            "recurrence": "MONTHLY",
            "preferred_account_id": account["id"],
        },
    )
    assert response.status_code == 201
    created = response.json()
    assert created["preferred_account_id"] == account["id"]
    assert created["preferred_account_name"] == account["name"]
    assert created["account_id"] is None
    future = api_client.get(
        f"/api/v1/{kind}?year=2026&month=11", headers=headers
    ).json()
    assert len(future) == 2
    assert all(item["preferred_account_id"] == account["id"] for item in future)
    assert all(item["status"] == "PLANNED" for item in future)
    assert (
        api_client.get(f"/api/v1/accounts/{account['id']}", headers=headers).json()[
            "current_balance"
        ]
        == "0.00"
    )
    assert (
        len(
            api_client.get(
                f"/api/v1/accounts/{account['id']}/balance-history", headers=headers
            ).json()
        )
        == 1
    )
    # An archived preference stays configured but cannot be used to confirm.
    api_client.delete(f"/api/v1/accounts/{account['id']}", headers=headers)
    december = api_client.get(
        f"/api/v1/{kind}?year=2026&month=12", headers=headers
    ).json()
    assert len(december) == 3
    assert all(item["preferred_account_id"] == account["id"] for item in december)
    assert (
        api_client.post(
            f"/api/v1/{kind}/{created['id']}/confirm",
            headers=headers,
            json={"account_id": account["id"], "already_in_balance": False},
        ).status_code
        == 404
    )


@pytest.mark.parametrize(
    ("kind", "field"), [("income", "expected_date"), ("commitments", "due_date")]
)
def test_saved_account_creation_rejects_other_users_archived_and_currency_mismatch(
    api_client: TestClient,
    database_session: Session,
    kind: str,
    field: str,
) -> None:
    headers = _headers(database_session, "preferred-validation@example.com")
    other = _headers(database_session, "preferred-other@example.com")
    foreign = _create_account(api_client, other)
    archived = _create_account(api_client, headers)
    usd = _create_account(api_client, headers, currency="USD")
    api_client.delete(f"/api/v1/accounts/{archived['id']}", headers=headers)
    for account, expected in [(foreign, 404), (archived, 404), (usd, 422)]:
        result = api_client.post(
            f"/api/v1/{kind}",
            headers=headers,
            json={
                "description": "Synthetic",
                "amount": "1.00",
                "currency": "ARS",
                field: "2026-10-05",
                "recurrence": "MONTHLY",
                "preferred_account_id": account["id"],
            },
        )
        assert result.status_code == expected
    assert (
        api_client.get(f"/api/v1/{kind}?year=2026&month=10", headers=headers).json()
        == []
    )
    assert database_session.scalars(select(MonthlyPlan)).all() == []


@pytest.mark.parametrize(
    ("kind", "field"), [("income", "expected_date"), ("commitments", "due_date")]
)
@pytest.mark.parametrize("included", [False, True])
def test_remembering_account_changes_pending_and_future_instances_only(
    api_client: TestClient,
    database_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
    field: str,
    included: bool,
) -> None:
    monkeypatch.setattr(
        "app.services.planning.financial_today", lambda: date(2026, 10, 5)
    )
    headers = _headers(database_session, "remember-owner@example.com")
    old = _create_account(api_client, headers)
    new = _create_account(api_client, headers)
    created = api_client.post(
        f"/api/v1/{kind}",
        headers=headers,
        json={
            "description": "Synthetic",
            "amount": "10.01",
            "currency": "ARS",
            field: "2026-09-05",
            "recurrence": "MONTHLY",
            "preferred_account_id": old["id"],
        },
    ).json()
    path = f"/api/v1/{kind}/{created['id']}/confirm"
    first = api_client.post(
        path,
        headers=headers,
        json={"account_id": old["id"], "already_in_balance": True},
    ).json()
    october = api_client.get(
        f"/api/v1/{kind}?year=2026&month=10", headers=headers
    ).json()[0]
    api_client.get(f"/api/v1/{kind}?year=2026&month=11", headers=headers)
    payload = {
        "account_id": new["id"],
        "already_in_balance": included,
        "remember_account": True,
    }
    confirm_path = f"/api/v1/{kind}/{october['id']}/confirm"
    confirmed = api_client.post(confirm_path, headers=headers, json=payload)
    assert confirmed.status_code == 200
    assert confirmed.json()["remember_account"] is True
    assert confirmed.json()["preferred_account_id"] == new["id"]
    assert (
        api_client.post(confirm_path, headers=headers, json=payload).json()
        == confirmed.json()
    )
    assert (
        api_client.post(
            confirm_path, headers=headers, json={**payload, "remember_account": False}
        ).status_code
        == 409
    )
    for month in [11, 12]:
        records = api_client.get(
            f"/api/v1/{kind}?year=2026&month={month}", headers=headers
        ).json()
        assert all(item["preferred_account_id"] == new["id"] for item in records)
    september = api_client.get(
        f"/api/v1/{kind}?year=2026&month=9", headers=headers
    ).json()[0]
    assert september == first
    expected = "1250.25" if included else "1260.26" if kind == "income" else "1240.24"
    assert (
        api_client.get(f"/api/v1/accounts/{new['id']}", headers=headers).json()[
            "current_balance"
        ]
        == expected
    )


def test_one_time_record_cannot_remember_a_monthly_account(
    api_client: TestClient,
    database_session: Session,
) -> None:
    headers = _headers(database_session, "remember-once@example.com")
    account = _create_account(api_client, headers)
    created = api_client.post(
        "/api/v1/income",
        headers=headers,
        json={
            "description": "Synthetic",
            "amount": "1.00",
            "currency": "ARS",
            "expected_date": "2026-10-05",
        },
    ).json()
    assert (
        api_client.post(
            f"/api/v1/income/{created['id']}/confirm",
            headers=headers,
            json={
                "account_id": account["id"],
                "already_in_balance": False,
                "remember_account": True,
            },
        ).status_code
        == 422
    )
    assert (
        api_client.get(f"/api/v1/accounts/{account['id']}", headers=headers).json()[
            "current_balance"
        ]
        == "1250.25"
    )


def test_concurrent_generation_and_account_remembering_use_one_saved_account(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.services.planning.financial_today", lambda: date(2026, 10, 5)
    )
    engine = get_engine()
    user_id = uuid4()
    try:
        with Session(engine) as session:
            session.add(
                User(
                    id=user_id,
                    email=f"preference-{user_id}@example.com",
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
                    initial_balance=Decimal("0.00"),
                    is_liquid=True,
                )
                .id
            )
            record_id = (
                PlanningService(session)
                .create_income(
                    user_id=user_id,
                    description="Synthetic",
                    amount=Decimal("0.01"),
                    currency=Currency.ARS,
                    expected_date=date(2026, 10, 5),
                    recurrence="MONTHLY",
                )
                .id
            )

        def perform(operation: str) -> None:
            with Session(engine) as session:
                service = PlanningService(session)
                if operation == "confirm":
                    service.confirm(
                        user_id=user_id,
                        record_id=record_id,
                        account_id=account_id,
                        already_in_balance=False,
                        is_income=True,
                        remember_account=True,
                    )
                else:
                    service.list_income(
                        user_id,
                        start=date(2026, 11, 1),
                        end=date(2026, 11, 30),
                        include_overdue=True,
                        limit=50,
                        offset=0,
                    )

        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(perform, ["generate", "confirm"]))
        with Session(engine) as session:
            records = session.scalars(
                select(PlannedIncome).where(PlannedIncome.user_id == user_id)
            ).all()
            assert len(records) == 2
            assert all(record.preferred_account_id == account_id for record in records)
            confirmed = session.get(PlannedIncome, record_id)
            assert confirmed is not None and confirmed.status == "RECEIVED"
    finally:
        with Session(engine) as session:
            session.execute(delete(MonthlyPlan).where(MonthlyPlan.user_id == user_id))
            session.execute(delete(User).where(User.id == user_id))
            session.commit()
