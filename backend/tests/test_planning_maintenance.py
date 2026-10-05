from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.planning import monthly_terms
from app.models.planning_maintenance import ConfirmationCorrection, MonthlyPlanChange
from tests.test_financial_accounts_api import _create_account, _headers


@pytest.fixture(autouse=True)
def fixed_month(monkeypatch: pytest.MonkeyPatch) -> None:
    for service in ("planning", "planning_maintenance", "home"):
        monkeypatch.setattr(
            f"app.services.{service}.financial_today", lambda: date(2026, 10, 5)
        )


def _create(
    client: TestClient,
    headers: dict[str, str],
    kind: str,
    *,
    recurrence: str = "MONTHLY",
    amount: str = "20.01",
) -> dict[str, object]:
    field = "expected_date" if kind == "income" else "due_date"
    response = client.post(
        f"/api/v1/{kind}",
        headers=headers,
        json={
            "description": "Synthetic",
            "currency": "ARS",
            "amount": amount,
            field: "2026-10-31",
            "recurrence": recurrence,
        },
    )
    assert response.status_code == 201
    return response.json()  # type: ignore[no-any-return]


def _month(
    client: TestClient, headers: dict[str, str], kind: str, month: int, year: int = 2026
) -> list[dict[str, object]]:
    response = client.get(
        f"/api/v1/{kind}?year={year}&month={month}&include_overdue=false",
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()  # type: ignore[no-any-return]


@pytest.mark.parametrize("kind", ["income", "commitments"])
def test_stop_cancels_only_pending_from_month_and_preserves_confirmed(
    api_client: TestClient,
    database_session: Session,
    kind: str,
) -> None:
    headers = _headers(database_session, "stop@example.com")
    account = _create_account(api_client, headers, balance="100.00")
    first = _create(api_client, headers, kind)
    november = _month(api_client, headers, kind, 11)[0]
    december = _month(api_client, headers, kind, 12)[0]
    confirmed = api_client.post(
        f"/api/v1/{kind}/{december['id']}/confirm",
        headers=headers,
        json={"account_id": account["id"], "already_in_balance": False},
    )
    assert confirmed.status_code == 200
    path = f"/api/v1/monthly-plans/{first['template_id']}/stop"
    assert (
        api_client.post(
            path, headers=headers, json={"from_month": "2026-11-01"}
        ).status_code
        == 200
    )
    assert (
        api_client.post(
            path, headers=headers, json={"from_month": "2026-11-01"}
        ).status_code
        == 200
    )
    assert (
        api_client.post(
            path, headers=headers, json={"from_month": "2026-12-01"}
        ).status_code
        == 409
    )
    assert _month(api_client, headers, kind, 10)[0]["status"] == "PLANNED"
    assert _month(api_client, headers, kind, 11)[0]["status"] == "CANCELLED"
    assert _month(api_client, headers, kind, 12)[0] == confirmed.json()
    assert _month(api_client, headers, kind, 1, 2027) == []
    assert (
        api_client.post(
            f"/api/v1/{kind}/{november['id']}/confirm",
            headers=headers,
            json={"account_id": account["id"], "already_in_balance": False},
        ).status_code
        == 409
    )
    # A corrected future confirmation must not resurrect a stopped occurrence.
    assert (
        api_client.post(
            f"/api/v1/{kind}/{december['id']}/correct",
            headers=headers,
            json={"original_confirmed_at": confirmed.json()["confirmed_at"]},
        ).status_code
        == 200
    )
    assert _month(api_client, headers, kind, 12)[0]["status"] == "CANCELLED"
    assert (
        api_client.get(f"/api/v1/accounts/{account['id']}", headers=headers).json()[
            "current_balance"
        ]
        == "100.00"
    )


@pytest.mark.parametrize("kind", ["income", "commitments"])
def test_future_edit_versions_preserve_completed_and_clamp_day(
    api_client: TestClient,
    database_session: Session,
    kind: str,
) -> None:
    headers = _headers(database_session, "edit@example.com")
    account = _create_account(api_client, headers)
    first = _create(api_client, headers, kind)
    _month(api_client, headers, kind, 11)
    completed = _month(api_client, headers, kind, 12)[0]
    result = api_client.post(
        f"/api/v1/{kind}/{completed['id']}/confirm",
        headers=headers,
        json={"account_id": account["id"], "already_in_balance": True},
    )
    path = f"/api/v1/monthly-plans/{first['template_id']}/edit"
    assert (
        api_client.post(
            path, headers=headers, json={"amount": "30.02", "first_date": "2026-11-15"}
        ).status_code
        == 200
    )
    field = "expected_date" if kind == "income" else "due_date"
    november = _month(api_client, headers, kind, 11)[0]
    assert november["amount"] == "30.02" and november[field] == "2026-11-15"
    assert _month(api_client, headers, kind, 10)[0] == first
    assert _month(api_client, headers, kind, 12)[0] == result.json()
    assert (
        api_client.post(
            path, headers=headers, json={"amount": "40.03", "first_date": "2027-01-31"}
        ).status_code
        == 200
    )
    february = _month(api_client, headers, kind, 2, 2027)[0]
    assert february["amount"] == "40.03" and february[field] == "2027-02-28"
    march = _month(api_client, headers, kind, 3, 2027)[0]
    assert march[field] == "2027-03-31"
    assert len(database_session.scalars(select(MonthlyPlanChange)).all()) == 2


@pytest.mark.parametrize(
    "amount", ["0", "-1", "1.001", "1000000000000000000", 1.25, True]
)
def test_edit_rejects_invalid_money(
    api_client: TestClient, database_session: Session, amount: object
) -> None:
    headers = _headers(database_session, "edit-invalid@example.com")
    first = _create(api_client, headers, "income")
    assert (
        api_client.post(
            f"/api/v1/monthly-plans/{first['template_id']}/edit",
            headers=headers,
            json={"amount": amount, "first_date": "2026-11-01"},
        ).status_code
        == 422
    )
    assert database_session.scalars(select(MonthlyPlanChange)).all() == []


def test_maintenance_rejects_past_current_stopped_and_unowned_changes(
    api_client: TestClient, database_session: Session
) -> None:
    headers = _headers(database_session, "maintenance@example.com")
    other = _headers(database_session, "maintenance-other@example.com")
    record = _create(api_client, headers, "income")
    path = f"/api/v1/monthly-plans/{record['template_id']}"
    for day in ["2026-09-01", "2026-10-31"]:
        assert (
            api_client.post(
                f"{path}/edit",
                headers=headers,
                json={"amount": "10.00", "first_date": day},
            ).status_code
            == 422
        )
    for suffix, payload in [
        ("edit", {"amount": "10.00", "first_date": "2026-11-01"}),
        ("stop", {"from_month": "2026-11-01"}),
    ]:
        assert (
            api_client.post(f"{path}/{suffix}", headers=other, json=payload).status_code
            == 404
        )
        assert api_client.post(f"{path}/{suffix}", json=payload).status_code == 401
    for day in ["2026-09-01", "2026-11-02"]:
        assert (
            api_client.post(
                f"{path}/stop", headers=headers, json={"from_month": day}
            ).status_code
            == 422
        )
    assert (
        api_client.post(
            f"{path}/stop", headers=headers, json={"from_month": "2026-11-01"}
        ).status_code
        == 200
    )
    assert (
        api_client.post(
            f"{path}/edit",
            headers=headers,
            json={"amount": "10.00", "first_date": "2026-11-01"},
        ).status_code
        == 422
    )


@pytest.mark.parametrize("kind", ["income", "commitments"])
@pytest.mark.parametrize("included", [False, True])
def test_correction_preserves_later_balances_audit_and_retry_after_reconfirmation(
    api_client: TestClient, database_session: Session, kind: str, included: bool
) -> None:
    headers = _headers(database_session, "correction@example.com")
    other = _headers(database_session, "correction-other@example.com")
    account = _create_account(api_client, headers, balance="100.00")
    first = _create(api_client, headers, kind, recurrence="ONE_TIME")
    path = f"/api/v1/{kind}/{first['id']}"
    confirmed = api_client.post(
        f"{path}/confirm",
        headers=headers,
        json={"account_id": account["id"], "already_in_balance": included},
    ).json()
    payload = {"original_confirmed_at": confirmed["confirmed_at"]}
    assert (
        api_client.post(f"{path}/correct", headers=other, json=payload).status_code
        == 404
    )
    assert api_client.post(f"{path}/correct", json=payload).status_code == 401
    assert (
        api_client.post(
            f"{path}/correct",
            headers=headers,
            json={"original_confirmed_at": "2026-01-01T00:00:00Z"},
        ).status_code
        == 409
    )
    assert (
        api_client.patch(
            f"/api/v1/accounts/{account['id']}/balance",
            headers=headers,
            json={"balance": "50.00"},
        ).status_code
        == 200
    )
    response = api_client.post(f"{path}/correct", headers=headers, json=payload)
    assert response.status_code == 200
    expected = "50.00" if included else "29.99" if kind == "income" else "70.01"
    assert (
        api_client.get(f"/api/v1/accounts/{account['id']}", headers=headers).json()[
            "current_balance"
        ]
        == expected
    )
    correction = database_session.get(
        ConfirmationCorrection, UUID(response.json()["id"])
    )
    assert correction is not None and correction.amount == Decimal("20.01")
    assert correction.already_in_balance == included
    assert _month(api_client, headers, kind, 10)[0]["status"] == "PLANNED"
    assert (
        api_client.post(
            f"{path}/confirm",
            headers=headers,
            json={"account_id": account["id"], "already_in_balance": True},
        ).status_code
        == 200
    )
    assert (
        api_client.post(f"{path}/correct", headers=headers, json=payload).json()
        == response.json()
    )
    assert _month(api_client, headers, kind, 10)[0]["status"] != "PLANNED"
    history = api_client.get(
        f"/api/v1/accounts/{account['id']}/balance-history", headers=headers
    ).json()
    assert len(history) == (2 if included else 4)


def test_correction_rejects_archived_account_and_overflow_atomically(
    api_client: TestClient, database_session: Session
) -> None:
    headers = _headers(database_session, "correction-overflow@example.com")
    account = _create_account(api_client, headers, balance="0.00")
    first = _create(
        api_client, headers, "commitments", recurrence="ONE_TIME", amount="0.01"
    )
    path = f"/api/v1/commitments/{first['id']}"
    confirmed = api_client.post(
        f"{path}/confirm",
        headers=headers,
        json={"account_id": account["id"], "already_in_balance": False},
    ).json()
    assert (
        api_client.patch(
            f"/api/v1/accounts/{account['id']}/balance",
            headers=headers,
            json={"balance": "999999999999999999.99"},
        ).status_code
        == 200
    )
    payload = {"original_confirmed_at": confirmed["confirmed_at"]}
    assert (
        api_client.post(f"{path}/correct", headers=headers, json=payload).status_code
        == 422
    )
    assert _month(api_client, headers, "commitments", 10)[0] == confirmed
    assert database_session.scalars(select(ConfirmationCorrection)).all() == []
    assert (
        api_client.delete(
            f"/api/v1/accounts/{account['id']}", headers=headers
        ).status_code
        == 204
    )
    assert (
        api_client.post(f"{path}/correct", headers=headers, json=payload).status_code
        == 422
    )


def test_monthly_terms_keep_versions_currency_independent_and_exact() -> None:
    versions = [
        (date(2026, 11, 1), Decimal("0.01"), 31),
        (date(2027, 3, 1), Decimal("999999999999999999.99"), 15),
    ]
    assert monthly_terms(date(2027, 2, 1), 10, Decimal("1.00"), versions) == (
        date(2027, 2, 28),
        Decimal("0.01"),
    )
    assert monthly_terms(date(2027, 3, 1), 10, Decimal("1.00"), versions) == (
        date(2027, 3, 15),
        Decimal("999999999999999999.99"),
    )
