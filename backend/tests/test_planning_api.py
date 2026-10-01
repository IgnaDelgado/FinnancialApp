from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.financial_account import AccountBalanceSnapshot, FinancialAccount
from app.models.planning import PlannedCommitment, PlannedIncome
from tests.test_financial_accounts_api import _create_account, _headers

RESOURCES = [("income", "expected_date"), ("commitments", "due_date")]


@pytest.mark.parametrize(("resource", "date_field"), RESOURCES)
@pytest.mark.parametrize("day", ["0001-01-01", "2024-02-29", "9999-12-31"])
def test_accepts_past_and_future_calendar_boundaries(
    api_client: TestClient,
    database_session: Session,
    resource: str,
    date_field: str,
    day: str,
) -> None:
    headers = _headers(database_session, "calendar-boundary@example.com")
    response = api_client.post(
        f"/api/v1/{resource}",
        headers=headers,
        json={
            "description": "Synthetic boundary",
            "amount": "0.01",
            "currency": "ARS",
            date_field: day,
        },
    )
    assert response.status_code == 201
    year, month, _ = day.split("-")
    assert api_client.get(
        f"/api/v1/{resource}?year={year}&month={month}", headers=headers
    ).json() == [response.json()]


@pytest.mark.parametrize(("resource", "date_field"), RESOURCES)
@pytest.mark.parametrize("currency", ["ARS", "USD"])
@pytest.mark.parametrize("amount", ["0.01", "1250.25", "999999999999999999.99"])
def test_create_and_read_planned_records_preserves_money_dates_and_accounts(
    api_client: TestClient,
    database_session: Session,
    resource: str,
    date_field: str,
    currency: str,
    amount: str,
) -> None:
    headers = _headers(database_session, "planning@example.com")
    account = _create_account(api_client, headers)
    before = api_client.get(
        f"/api/v1/accounts/{account['id']}/balance-history", headers=headers
    ).json()
    response = api_client.post(
        f"/api/v1/{resource}",
        headers=headers,
        json={
            "description": " Synthetic record ",
            "amount": amount,
            "currency": currency,
            date_field: "2026-10-15",
            "recurrence": "ONE_TIME",
        },
    )
    assert response.status_code == 201
    created = response.json()
    assert created["description"] == "Synthetic record"
    assert created["amount"] == amount
    assert created["currency"] == currency
    assert created[date_field] == "2026-10-15"
    assert created["status"] == "PLANNED"
    assert created["recurrence"] == "ONE_TIME"
    assert "user_id" not in created
    database_session.expire_all()
    persisted = (
        database_session.get(PlannedIncome, UUID(created["id"]))
        if resource == "income"
        else database_session.get(PlannedCommitment, UUID(created["id"]))
    )
    assert persisted is not None
    assert persisted.amount == Decimal(amount)
    assert getattr(persisted, date_field) == date(2026, 10, 15)
    assert api_client.get(
        f"/api/v1/{resource}?year=2026&month=10", headers=headers
    ).json() == [created]
    persisted_account = database_session.get(FinancialAccount, UUID(str(account["id"])))
    assert persisted_account is not None
    assert persisted_account.current_balance == Decimal("1250.25")
    assert (
        api_client.get(
            f"/api/v1/accounts/{account['id']}/balance-history", headers=headers
        ).json()
        == before
    )
    assert len(database_session.scalars(select(AccountBalanceSnapshot)).all()) == 1


@pytest.mark.parametrize(("resource", "date_field"), RESOURCES)
@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("amount", "0"),
        ("amount", "-0.01"),
        ("amount", "1.001"),
        ("amount", "1.000"),
        ("amount", "1000000000000000000"),
        ("amount", "999999999999999999.999"),
        ("amount", "NaN"),
        ("amount", "Infinity"),
        ("amount", 1.25),
        ("amount", True),
        ("currency", "EUR"),
        ("currency", None),
        ("description", "   "),
        ("description", "x" * 101),
        ("date", "2026-02-30"),
        ("date", "2026-10-01T00:00:00Z"),
        ("date", 0),
        ("date", "0000-01-01"),
        ("date", "2026-1-01"),
        ("recurrence", "MONTHLY"),
        ("status", "RECEIVED"),
        ("user_id", "00000000-0000-0000-0000-000000000000"),
    ],
)
def test_rejects_invalid_planning_input(
    api_client: TestClient,
    database_session: Session,
    resource: str,
    date_field: str,
    field: str,
    invalid: object,
) -> None:
    headers = _headers(database_session, "invalid-planning@example.com")
    payload: dict[str, object] = {
        "description": "Synthetic record",
        "amount": "1.00",
        "currency": "ARS",
        date_field: "2026-10-15",
    }
    payload[date_field if field == "date" else field] = invalid
    assert (
        api_client.post(
            f"/api/v1/{resource}", headers=headers, json=payload
        ).status_code
        == 422
    )
    assert (
        api_client.get(f"/api/v1/{resource}?year=2026&month=10", headers=headers).json()
        == []
    )


@pytest.mark.parametrize(("resource", "date_field"), RESOURCES)
def test_month_query_includes_overdue_and_paginates_deterministically(
    api_client: TestClient, database_session: Session, resource: str, date_field: str
) -> None:
    headers = _headers(database_session, "month-planning@example.com")
    entries = []
    for day in ["2026-09-30", "2026-10-01", "2026-10-01", "2026-10-31", "2026-11-01"]:
        response = api_client.post(
            f"/api/v1/{resource}",
            headers=headers,
            json={
                "description": "Synthetic record",
                "amount": "1.00",
                "currency": "USD",
                date_field: day,
            },
        )
        assert response.status_code == 201
        entries.append(response.json())
    expected = sorted(entries[:-1], key=lambda item: (item[date_field], item["id"]))
    url = f"/api/v1/{resource}?year=2026&month=10"
    first = api_client.get(url + "&limit=2", headers=headers).json()
    second = api_client.get(url + "&limit=2&offset=2", headers=headers).json()
    assert first + second == expected
    assert api_client.get(url + "&limit=2", headers=headers).json() == first
    assert (
        api_client.get(url + "&include_overdue=false", headers=headers).json()
        == expected[1:]
    )
    november = api_client.get(
        f"/api/v1/{resource}?year=2026&month=11", headers=headers
    ).json()
    assert len(november) == 5
    assert api_client.get(url + "&offset=99", headers=headers).json() == []


@pytest.mark.parametrize(("resource", "date_field"), RESOURCES)
def test_planning_requires_authentication_and_isolates_users(
    api_client: TestClient, database_session: Session, resource: str, date_field: str
) -> None:
    payload = {
        "description": "Synthetic record",
        "amount": "1.00",
        "currency": "ARS",
        date_field: "2026-10-01",
    }
    url = f"/api/v1/{resource}"
    assert api_client.get(url).status_code == 401
    assert api_client.post(url, json=payload).status_code == 401
    owner = _headers(database_session, "planning-owner@example.com")
    other = _headers(database_session, "planning-other@example.com")
    created = api_client.post(url, json=payload, headers=owner)
    assert created.status_code == 201
    assert api_client.get(url + "?year=2026&month=10", headers=other).json() == []
    assert len(api_client.get(url + "?year=2026&month=10", headers=owner).json()) == 1


@pytest.mark.parametrize(
    "query",
    [
        "month=0",
        "month=13",
        "year=0",
        "year=10000",
        "limit=0",
        "limit=101",
        "offset=-1",
    ],
)
@pytest.mark.parametrize(("resource", "date_field"), RESOURCES)
def test_rejects_invalid_planning_query(
    api_client: TestClient,
    database_session: Session,
    resource: str,
    date_field: str,
    query: str,
) -> None:
    headers = _headers(database_session, "query@example.com")
    assert (
        api_client.get(f"/api/v1/{resource}?{query}", headers=headers).status_code
        == 422
    )


@pytest.mark.parametrize(("resource", "date_field"), RESOURCES)
def test_current_month_uses_financial_date(
    api_client: TestClient,
    database_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    resource: str,
    date_field: str,
) -> None:
    monkeypatch.setattr("app.api.planning.financial_today", lambda: date(2026, 9, 30))
    headers = _headers(database_session, "today@example.com")
    for day in ["2026-09-30", "2026-10-01"]:
        api_client.post(
            f"/api/v1/{resource}",
            headers=headers,
            json={
                "description": "Synthetic record",
                "amount": "1.00",
                "currency": "ARS",
                date_field: day,
            },
        )
    assert [
        item[date_field]
        for item in api_client.get(f"/api/v1/{resource}", headers=headers).json()
    ] == ["2026-09-30"]
