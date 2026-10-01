from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.cash_flow import cash_flow_snapshot
from app.domain.currency import Currency
from app.models.financial_account import AccountBalanceSnapshot
from tests.test_financial_accounts_api import _create_account, _headers


@pytest.mark.parametrize("currency", [Currency.ARS, Currency.USD])
def test_margin_excludes_unavailable_cash_and_income_not_received(
    currency: Currency,
) -> None:
    result = cash_flow_snapshot(
        currency,
        date(2026, 10, 10),
        date(2026, 10, 31),
        [
            (currency, Decimal("100.10"), True),
            (currency, Decimal("-5.00"), True),
            (currency, Decimal("900.00"), False),
        ],
        [
            (currency, Decimal("20.05"), date(2026, 9, 1)),
            (currency, Decimal("10.01"), date(2026, 10, 31)),
            (currency, Decimal("100.00"), date(2026, 11, 1)),
        ],
        [
            (currency, Decimal("50.25"), date(2026, 10, 10)),
            (currency, Decimal("20.00"), date(2026, 10, 9)),
            (currency, Decimal("40.00"), date(2026, 11, 1)),
        ],
    )
    assert result.cash_after_bills == Decimal("70.04")
    assert result.forecast_after_bills == Decimal("120.29")
    assert result.negative_balances == Decimal("-5.00")
    assert result.overdue_income_count == 1


def test_margin_keeps_currencies_separate_and_preserves_shortfall_and_zero() -> None:
    result = cash_flow_snapshot(
        Currency.ARS,
        date(2026, 10, 1),
        date(2026, 10, 31),
        [
            (Currency.USD, Decimal("1000000.00"), True),
            (Currency.ARS, Decimal("0.00"), True),
        ],
        [
            (Currency.ARS, Decimal("0.01"), date(2026, 10, 1)),
            (Currency.USD, Decimal("200.00"), date(2026, 10, 1)),
        ],
        [(Currency.USD, Decimal("100.00"), date(2026, 10, 1))],
    )
    assert result.liquid_cash == Decimal("0.00")
    assert result.cash_after_bills == Decimal("-0.01")
    assert result.forecast_after_bills == Decimal("-0.01")
    empty = cash_flow_snapshot(
        Currency.USD, date(2026, 10, 1), date(2026, 10, 31), [], [], []
    )
    assert empty.cash_after_bills == Decimal("0.00")


def test_margin_preserves_maximum_decimal_precision_without_rounding() -> None:
    maximum = Decimal("999999999999999999.99")
    result = cash_flow_snapshot(
        Currency.ARS,
        date(2026, 10, 1),
        date(2026, 10, 31),
        [(Currency.ARS, maximum, True)] * 2,
        [(Currency.ARS, Decimal("0.01"), date(2026, 10, 31))],
        [],
    )
    assert result.cash_after_bills == Decimal("1999999999999999999.97")


def test_home_requires_authentication(api_client: TestClient) -> None:
    assert api_client.get("/api/v1/home").status_code == 401


def test_home_uses_all_owned_records_and_does_not_change_balances(
    api_client: TestClient,
    database_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.services.home.financial_today", lambda: date(2026, 10, 10))
    monkeypatch.setattr(
        "app.services.planning.financial_today", lambda: date(2026, 10, 10)
    )
    headers = _headers(database_session, "home-owner@example.com")
    other = _headers(database_session, "home-other@example.com")
    account = _create_account(api_client, headers, balance="100.10")
    archived = _create_account(api_client, headers, balance="500.00")
    assert (
        api_client.delete(
            f"/api/v1/accounts/{archived['id']}", headers=headers
        ).status_code
        == 204
    )
    _create_account(api_client, headers, balance="-10.00")
    _create_account(api_client, headers, balance="900.00", account_type="INVESTMENT")
    _create_account(api_client, headers, balance="200.00", currency="USD")
    _create_account(api_client, other, balance="100000.00")
    for index in range(55):
        response = api_client.post(
            "/api/v1/commitments",
            headers=headers,
            json={
                "description": f"Synthetic bill {index}",
                "amount": "0.01",
                "currency": "ARS",
                "due_date": "2026-10-31",
            },
        )
        assert response.status_code == 201
    for resource, day_field, day in [
        ("income", "expected_date", "2026-10-10"),
        ("commitments", "due_date", "2026-10-05"),
    ]:
        assert (
            api_client.post(
                f"/api/v1/{resource}",
                headers=headers,
                json={
                    "description": "Synthetic monthly",
                    "amount": "20.25",
                    "currency": "ARS",
                    day_field: day,
                    "recurrence": "MONTHLY",
                },
            ).status_code
            == 201
        )
    before = list(database_session.scalars(select(AccountBalanceSnapshot)).all())
    first = api_client.get("/api/v1/home", headers=headers)
    assert first.status_code == 200
    data = first.json()
    ars, usd = data["currencies"]
    assert data["account_count"] == 4
    assert data["commitment_count"] == 56
    assert ars["liquid_cash"] == "100.10"
    assert ars["pending_bills"] == "20.80"
    assert ars["cash_after_bills"] == "79.30"
    assert ars["forecast_after_bills"] == "99.55"
    assert ars["negative_balances"] == "-10.00"
    assert usd["cash_after_bills"] == "200.00"
    assert api_client.get("/api/v1/home", headers=headers).json() == data
    assert (
        api_client.get(f"/api/v1/accounts/{account['id']}", headers=headers).json()[
            "current_balance"
        ]
        == "100.10"
    )
    assert len(
        list(database_session.scalars(select(AccountBalanceSnapshot)).all())
    ) == len(before)
    assert api_client.get("/api/v1/home", headers=other).json()["commitment_count"] == 0


def test_home_materializes_monthly_bills_after_rollover(
    api_client: TestClient,
    database_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.services.home.financial_today", lambda: date(2027, 2, 1))
    monkeypatch.setattr(
        "app.services.planning.financial_today", lambda: date(2027, 2, 1)
    )
    headers = _headers(database_session, "home-rollover@example.com")
    assert (
        api_client.post(
            "/api/v1/commitments",
            headers=headers,
            json={
                "description": "Synthetic rent",
                "amount": "10.25",
                "currency": "ARS",
                "due_date": "2027-01-31",
                "recurrence": "MONTHLY",
            },
        ).status_code
        == 201
    )
    data = api_client.get("/api/v1/home", headers=headers).json()
    assert data["month_end"] == "2027-02-28"
    assert data["commitment_count"] == 2
    assert data["currencies"][0]["pending_bills"] == "20.50"
