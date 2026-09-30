from decimal import Decimal
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.financial_account import AccountBalanceSnapshot, FinancialAccount
from app.models.user import User


def _headers(database_session: Session, email: str) -> dict[str, str]:
    user = User(email=email, password_hash="$argon2id$synthetic-test-hash")
    database_session.add(user)
    database_session.commit()
    access_token, _ = create_access_token(user.id)
    return {"Authorization": f"Bearer {access_token}"}


def _create_account(
    api_client: TestClient,
    headers: dict[str, str],
    *,
    account_type: str = "BANK",
    currency: str = "ARS",
    balance: str = "1250.25",
    is_liquid: bool | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": "Synthetic account",
        "account_type": account_type,
        "currency": currency,
        "initial_balance": balance,
    }
    if is_liquid is not None:
        payload["is_liquid"] = is_liquid
    response = api_client.post("/api/v1/accounts", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()  # type: ignore[no-any-return]


def test_create_account_records_initial_balance_and_snapshot(
    api_client: TestClient, database_session: Session
) -> None:
    headers = _headers(database_session, "owner@example.com")
    created = _create_account(api_client, headers)
    account_id = UUID(str(created["id"]))
    account = database_session.get(FinancialAccount, account_id)
    snapshots = database_session.scalars(
        select(AccountBalanceSnapshot).where(
            AccountBalanceSnapshot.account_id == account_id
        )
    ).all()

    assert created["currency"] == "ARS"
    assert created["current_balance"] == "1250.25"
    assert created["is_liquid"] is True
    assert account is not None
    assert account.current_balance == Decimal("1250.25")
    assert len(snapshots) == 1
    assert snapshots[0].balance == Decimal("1250.25")
    assert account.balance_updated_at == snapshots[0].recorded_at


def test_investment_account_cash_defaults_to_non_liquid(
    api_client: TestClient, database_session: Session
) -> None:
    headers = _headers(database_session, "investor@example.com")
    account = _create_account(
        api_client, headers, account_type="INVESTMENT", currency="USD", balance="0"
    )

    assert account["currency"] == "USD"
    assert account["current_balance"] == "0.00"
    assert account["is_liquid"] is False


def test_update_balance_records_history_without_replacing_prior_snapshot(
    api_client: TestClient, database_session: Session
) -> None:
    headers = _headers(database_session, "history@example.com")
    created = _create_account(api_client, headers)
    account_id = str(created["id"])
    updated = api_client.patch(
        f"/api/v1/accounts/{account_id}/balance",
        json={"balance": "999.99"},
        headers=headers,
    )
    history = api_client.get(
        f"/api/v1/accounts/{account_id}/balance-history", headers=headers
    )

    assert updated.status_code == 200
    assert updated.json()["current_balance"] == "999.99"
    assert history.status_code == 200
    assert [item["balance"] for item in history.json()] == ["1250.25", "999.99"]


def test_balance_history_can_be_read_in_bounded_pages(
    api_client: TestClient, database_session: Session
) -> None:
    headers = _headers(database_session, "pages@example.com")
    created = _create_account(api_client, headers)
    account_url = f"/api/v1/accounts/{created['id']}"
    for balance in ("2.00", "3.00"):
        response = api_client.patch(
            f"{account_url}/balance", json={"balance": balance}, headers=headers
        )
        assert response.status_code == 200

    first = api_client.get(f"{account_url}/balance-history?limit=2", headers=headers)
    second = api_client.get(
        f"{account_url}/balance-history?limit=2&offset=2", headers=headers
    )

    assert [item["balance"] for item in first.json()] == ["1250.25", "2.00"]
    assert [item["balance"] for item in second.json()] == ["3.00"]
    assert (
        api_client.get(
            f"{account_url}/balance-history?limit=101", headers=headers
        ).status_code
        == 422
    )


def test_negative_balance_is_preserved_in_account_and_history(
    api_client: TestClient, database_session: Session
) -> None:
    headers = _headers(database_session, "overdraft@example.com")
    created = _create_account(api_client, headers, balance="-25000.75")
    account_id = str(created["id"])
    updated = api_client.patch(
        f"/api/v1/accounts/{account_id}/balance",
        json={"balance": "-50000.01"},
        headers=headers,
    )
    history = api_client.get(
        f"/api/v1/accounts/{account_id}/balance-history", headers=headers
    )

    assert created["current_balance"] == "-25000.75"
    assert updated.status_code == 200
    assert updated.json()["current_balance"] == "-50000.01"
    assert [item["balance"] for item in history.json()] == ["-25000.75", "-50000.01"]


def test_rejects_imprecise_or_unsupported_account_values(
    api_client: TestClient, database_session: Session
) -> None:
    headers = _headers(database_session, "validation@example.com")
    base = {
        "name": "Synthetic account",
        "account_type": "BANK",
        "currency": "ARS",
        "initial_balance": "10.00",
    }
    invalid_changes = (
        {"initial_balance": "1.001"},
        {"initial_balance": "-1.001"},
        {"initial_balance": "1000000000000000000.00"},
        {"currency": "EUR"},
        {"account_type": "BROKER_TOTAL"},
        {"name": "   "},
    )

    for change in invalid_changes:
        response = api_client.post(
            "/api/v1/accounts", json={**base, **change}, headers=headers
        )
        assert response.status_code == 422
    assert api_client.get("/api/v1/accounts", headers=headers).json() == []


def test_account_operations_are_scoped_to_owner(
    api_client: TestClient, database_session: Session
) -> None:
    owner_headers = _headers(database_session, "first@example.com")
    other_headers = _headers(database_session, "second@example.com")
    created = _create_account(api_client, owner_headers)
    account_url = f"/api/v1/accounts/{created['id']}"

    assert len(api_client.get("/api/v1/accounts", headers=owner_headers).json()) == 1
    assert api_client.get("/api/v1/accounts", headers=other_headers).json() == []
    assert api_client.get(account_url, headers=other_headers).status_code == 404
    assert (
        api_client.get(
            f"{account_url}/balance-history", headers=other_headers
        ).status_code
        == 404
    )
    assert (
        api_client.patch(
            f"{account_url}/balance",
            json={"balance": "1.00"},
            headers=other_headers,
        ).status_code
        == 404
    )
    assert api_client.delete(account_url, headers=other_headers).status_code == 404
    assert (
        api_client.get(account_url, headers=owner_headers).json()["current_balance"]
        == "1250.25"
    )


def test_archived_account_disappears_from_active_operations_but_retains_records(
    api_client: TestClient, database_session: Session
) -> None:
    headers = _headers(database_session, "archive@example.com")
    created = _create_account(api_client, headers)
    account_id = UUID(str(created["id"]))
    account_url = f"/api/v1/accounts/{account_id}"

    assert api_client.delete(account_url, headers=headers).status_code == 204
    assert api_client.get("/api/v1/accounts", headers=headers).json() == []
    assert api_client.get(account_url, headers=headers).status_code == 404
    assert (
        api_client.patch(
            f"{account_url}/balance", json={"balance": "2.00"}, headers=headers
        ).status_code
        == 404
    )
    persisted = database_session.get(FinancialAccount, account_id)
    assert persisted is not None
    database_session.refresh(persisted)
    assert persisted.archived_at is not None
    assert (
        database_session.scalar(
            select(AccountBalanceSnapshot).where(
                AccountBalanceSnapshot.account_id == account_id
            )
        )
        is not None
    )


def test_accounts_require_authentication(api_client: TestClient) -> None:
    assert api_client.get("/api/v1/accounts").status_code == 401
    assert (
        api_client.post(
            "/api/v1/accounts",
            json={
                "name": "Synthetic account",
                "account_type": "CASH",
                "currency": "ARS",
                "initial_balance": "0.00",
            },
        ).status_code
        == 401
    )
