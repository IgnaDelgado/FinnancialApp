from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.database import get_engine
from app.domain.account import AccountType
from app.domain.currency import Currency
from app.models.financial_account import AccountBalanceSnapshot, FinancialAccount
from app.models.planning import PlannedIncome
from app.models.user import User
from app.services.financial_accounts import FinancialAccountService
from app.services.planning import PlanningService
from tests.test_financial_accounts_api import _create_account, _headers

RESOURCES = [
    ("income", "expected_date", "RECEIVED"),
    ("commitments", "due_date", "PAID"),
]


def _record(
    client: TestClient,
    headers: dict[str, str],
    kind: str,
    field: str,
    *,
    amount: str = "10.01",
    recurrence: str = "ONE_TIME",
) -> str:
    result = client.post(
        f"/api/v1/{kind}",
        headers=headers,
        json={
            "description": "Synthetic movement",
            "amount": amount,
            "currency": "ARS",
            field: "2026-10-01",
            "recurrence": recurrence,
        },
    )
    assert result.status_code == 201
    return str(result.json()["id"])


@pytest.mark.parametrize(("kind", "field", "status"), RESOURCES)
@pytest.mark.parametrize("included", [False, True])
@pytest.mark.parametrize("recurrence", ["ONE_TIME", "MONTHLY"])
def test_confirmation_updates_account_once_or_preserves_reconciled_balance(
    api_client: TestClient,
    database_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
    field: str,
    status: str,
    included: bool,
    recurrence: str,
) -> None:
    monkeypatch.setattr(
        "app.services.planning.financial_today", lambda: date(2026, 10, 5)
    )
    headers = _headers(database_session, "confirm-owner@example.com")
    account = _create_account(api_client, headers)
    record_id = _record(api_client, headers, kind, field, recurrence=recurrence)
    path = f"/api/v1/{kind}/{record_id}/confirm"
    payload = {"account_id": account["id"], "already_in_balance": included}
    response = api_client.post(path, headers=headers, json=payload)
    assert response.status_code == 200
    confirmed = response.json()
    assert confirmed["status"] == status
    assert confirmed["account_id"] == account["id"]
    assert confirmed["already_in_balance"] is included
    assert confirmed["confirmed_at"] is not None
    assert api_client.post(path, headers=headers, json=payload).json() == confirmed
    persisted = api_client.get(
        f"/api/v1/accounts/{account['id']}", headers=headers
    ).json()
    expected = "1250.25" if included else "1260.26" if kind == "income" else "1240.24"
    assert persisted["current_balance"] == expected
    if included:
        assert persisted["balance_updated_at"] == account["balance_updated_at"]
    history = api_client.get(
        f"/api/v1/accounts/{account['id']}/balance-history", headers=headers
    ).json()
    assert len(history) == (1 if included else 2)
    assert history[-1]["balance"] == expected
    assert (
        api_client.post(
            path, headers=headers, json={**payload, "already_in_balance": not included}
        ).status_code
        == 409
    )
    assert (
        api_client.get(f"/api/v1/{kind}?year=2026&month=10", headers=headers).json()[0][
            "status"
        ]
        == status
    )
    # Completed records no longer appear as overdue in subsequent months.
    november = api_client.get(
        f"/api/v1/{kind}?year=2026&month=11", headers=headers
    ).json()
    assert all(item["id"] != record_id for item in november)
    assert all(item["status"] == "PLANNED" for item in november)
    # A retry remains safe after archival; a different account is a conflict.
    another = _create_account(api_client, headers)
    assert (
        api_client.post(
            path, headers=headers, json={**payload, "account_id": another["id"]}
        ).status_code
        == 409
    )
    assert (
        api_client.delete(
            f"/api/v1/accounts/{account['id']}", headers=headers
        ).status_code
        == 204
    )
    assert api_client.post(path, headers=headers, json=payload).json() == confirmed


@pytest.mark.parametrize(("kind", "field", "status"), RESOURCES)
def test_confirmation_rejects_unauthorized_archived_or_mixed_currency_resources(
    api_client: TestClient,
    database_session: Session,
    kind: str,
    field: str,
    status: str,
) -> None:
    headers = _headers(database_session, "confirmation-owner@example.com")
    other = _headers(database_session, "confirmation-other@example.com")
    own = _create_account(api_client, headers)
    foreign = _create_account(api_client, other)
    usd = _create_account(api_client, headers, currency="USD")
    archived = _create_account(api_client, headers)
    api_client.delete(f"/api/v1/accounts/{archived['id']}", headers=headers)
    record_id = _record(api_client, headers, kind, field)
    path = f"/api/v1/{kind}/{record_id}/confirm"
    payload = {"account_id": own["id"], "already_in_balance": False}
    assert api_client.post(path, json=payload).status_code == 401
    assert api_client.post(path, headers=other, json=payload).status_code == 404
    for account in [foreign, archived]:
        assert (
            api_client.post(
                path, headers=headers, json={**payload, "account_id": account["id"]}
            ).status_code
            == 404
        )
    for included in [False, True]:
        assert (
            api_client.post(
                path,
                headers=headers,
                json={"account_id": usd["id"], "already_in_balance": included},
            ).status_code
            == 422
        )
    assert (
        api_client.post(
            f"/api/v1/{kind}/{uuid4()}/confirm", headers=headers, json=payload
        ).status_code
        == 404
    )
    assert (
        api_client.get(f"/api/v1/accounts/{own['id']}", headers=headers).json()[
            "current_balance"
        ]
        == "1250.25"
    )
    assert (
        api_client.get(f"/api/v1/{kind}?year=2026&month=10", headers=headers).json()[0][
            "status"
        ]
        == "PLANNED"
    )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"already_in_balance": False},
        {"account_id": "not-a-uuid", "already_in_balance": False},
        {"account_id": str(uuid4()), "already_in_balance": "false"},
        {"account_id": str(uuid4()), "already_in_balance": 0},
        {"account_id": str(uuid4()), "already_in_balance": False, "amount": "1.00"},
    ],
)
def test_confirmation_requires_an_explicit_account_and_boolean(
    api_client: TestClient,
    database_session: Session,
    payload: dict[str, object],
) -> None:
    headers = _headers(database_session, "confirmation-invalid@example.com")
    record_id = _record(api_client, headers, "income", "expected_date")
    assert (
        api_client.post(
            f"/api/v1/income/{record_id}/confirm", headers=headers, json=payload
        ).status_code
        == 422
    )


@pytest.mark.parametrize(
    ("kind", "field", "balance", "amount", "expected"),
    [
        ("income", "expected_date", "999999999999999999.99", "0.01", 422),
        ("commitments", "due_date", "-999999999999999999.99", "0.01", 422),
        ("income", "expected_date", "0.00", "0.01", 200),
        ("commitments", "due_date", "0.00", "0.01", 200),
    ],
)
def test_confirmation_handles_zero_negative_and_storage_boundaries_atomically(
    api_client: TestClient,
    database_session: Session,
    kind: str,
    field: str,
    balance: str,
    amount: str,
    expected: int,
) -> None:
    headers = _headers(database_session, "confirmation-limit@example.com")
    account = _create_account(api_client, headers, balance=balance)
    record_id = _record(api_client, headers, kind, field, amount=amount)
    result = api_client.post(
        f"/api/v1/{kind}/{record_id}/confirm",
        headers=headers,
        json={"account_id": account["id"], "already_in_balance": False},
    )
    assert result.status_code == expected
    history = api_client.get(
        f"/api/v1/accounts/{account['id']}/balance-history", headers=headers
    ).json()
    if expected == 422:
        assert len(history) == 1
        assert history[0]["balance"] == balance
        assert (
            api_client.get(
                f"/api/v1/{kind}?year=2026&month=10", headers=headers
            ).json()[0]["status"]
            == "PLANNED"
        )
    else:
        assert history[-1]["balance"] == ("0.01" if kind == "income" else "-0.01")


def test_home_does_not_count_confirmed_income_or_paid_commitments_twice(
    api_client: TestClient,
    database_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.services.home.financial_today", lambda: date(2026, 10, 1))
    headers = _headers(database_session, "confirmed-home@example.com")
    account = _create_account(api_client, headers, balance="100.00")
    for kind, field, _ in RESOURCES:
        record_id = _record(api_client, headers, kind, field, amount="20.00")
        assert (
            api_client.post(
                f"/api/v1/{kind}/{record_id}/confirm",
                headers=headers,
                json={"account_id": account["id"], "already_in_balance": False},
            ).status_code
            == 200
        )
    result = api_client.get("/api/v1/home", headers=headers).json()["currencies"][0]
    assert result["liquid_cash"] == "100.00"
    assert result["pending_bills"] == "0.00"
    assert result["expected_income"] == "0.00"
    assert result["forecast_after_bills"] == "100.00"


@pytest.mark.parametrize("same_record", [False, True])
def test_concurrent_confirmations_preserve_each_movement_once(
    same_record: bool,
) -> None:
    engine = get_engine()
    user_id = uuid4()
    account_id: UUID | None = None
    try:
        with Session(engine) as session:
            session.add(
                User(
                    id=user_id,
                    email=f"confirm-{user_id}@example.com",
                    password_hash="synthetic",
                )
            )
            session.commit()
            account = FinancialAccountService(session).create(
                user_id=user_id,
                name="Synthetic",
                account_type=AccountType.BANK,
                currency=Currency.ARS,
                initial_balance=Decimal("0.00"),
                is_liquid=True,
            )
            account_id = account.id
            ids = [
                PlanningService(session)
                .create_income(
                    user_id=user_id,
                    description="Synthetic",
                    amount=Decimal("0.01"),
                    currency=Currency.ARS,
                    expected_date=date(2026, 10, 1),
                )
                .id
                for _ in range(1 if same_record else 3)
            ]

        def confirm(record_id: UUID) -> str:
            assert account_id is not None
            with Session(engine) as session:
                return (
                    PlanningService(session)
                    .confirm(
                        user_id=user_id,
                        record_id=record_id,
                        account_id=account_id,
                        already_in_balance=False,
                        is_income=True,
                    )
                    .status
                )

        with ThreadPoolExecutor(max_workers=3) as pool:
            assert (
                list(pool.map(confirm, ids * 3 if same_record else ids))
                == ["RECEIVED"] * 3
            )
        with Session(engine) as session:
            persisted = session.get(FinancialAccount, account_id)
            assert persisted is not None
            assert persisted.current_balance == Decimal(
                "0.01" if same_record else "0.03"
            )
            snapshots = session.scalars(
                select(AccountBalanceSnapshot).where(
                    AccountBalanceSnapshot.account_id == account_id
                )
            ).all()
            assert len(snapshots) == (2 if same_record else 4)
            assert len(
                session.scalars(
                    select(PlannedIncome).where(
                        PlannedIncome.user_id == user_id,
                        PlannedIncome.status == "RECEIVED",
                    )
                ).all()
            ) == len(ids)
    finally:
        with Session(engine) as session:
            # Retain account references until the owner deletes their data.
            session.execute(
                delete(PlannedIncome).where(PlannedIncome.user_id == user_id)
            )
            session.execute(delete(User).where(User.id == user_id))
            session.commit()
