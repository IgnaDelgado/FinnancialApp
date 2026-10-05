from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from typing import cast
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.database import get_engine
from app.domain.currency import Currency
from app.domain.planning import monthly_dates
from app.models.planning import MonthlyPlan, PlannedCommitment, PlannedIncome
from app.models.planning_maintenance import MonthlyPlanChange
from app.models.user import User
from app.repositories.planning import PlanningRepository
from app.services.planning import PlanningService
from tests.test_financial_accounts_api import _create_account, _headers

RESOURCES = [("income", "expected_date"), ("commitments", "due_date")]


@pytest.mark.parametrize(("resource", "date_field"), RESOURCES)
@pytest.mark.parametrize("plan_count", [1, 4])
def test_generation_reads_versions_once_and_preserves_each_plans_terms(
    api_client: TestClient,
    database_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    resource: str,
    date_field: str,
    plan_count: int,
) -> None:
    monkeypatch.setattr(
        "app.services.planning.financial_today", lambda: date(2026, 3, 15)
    )
    headers = _headers(database_session, "batched-versions@example.com")
    user = database_session.scalar(
        select(User).where(User.email == "batched-versions@example.com")
    )
    assert user is not None
    for index in range(plan_count):
        response = api_client.post(
            f"/api/v1/{resource}",
            headers=headers,
            json={
                "description": f"Synthetic {index}",
                "amount": "1.01",
                "currency": "ARS",
                date_field: "2026-01-31",
                "recurrence": "MONTHLY",
            },
        )
        assert response.status_code == 201
        if index == 0:
            continue  # A plan without versions still uses its original terms.
        for amount in ("2.02", "3.03"):
            database_session.add(
                MonthlyPlanChange(
                    template_id=UUID(response.json()["template_id"]),
                    effective_period=date(2026, 2, 1),
                    amount=Decimal(amount),
                    day=28,
                )
            )
    database_session.flush()
    service = PlanningService(database_session)
    with patch.object(
        database_session, "execute", wraps=database_session.execute
    ) as executed:
        # Exercise catch-up AND future preview: neither may reread the versions.
        service.ensure_monthly_records(
            user.id, resource, date(2026, 4, 1), date(2026, 4, 30)
        )
    version_reads = [
        call
        for call in executed.call_args_list
        if "FROM monthly_plan_changes" in str(call.args[0])
    ]
    assert len(version_reads) == 1
    model = PlannedIncome if resource == "income" else PlannedCommitment
    entries = database_session.scalars(
        select(model).where(model.user_id == user.id)
    ).all()
    assert len(entries) == plan_count * 4
    for entry in entries:
        entry = cast(PlannedIncome | PlannedCommitment, entry)
        day = getattr(entry, date_field)
        changed = entry.description != "Synthetic 0" and day.month >= 2
        assert entry.amount == Decimal("3.03" if changed else "1.01")
        assert day.day == (
            28 if changed or day.month == 2 else 31 if day.month != 4 else 30
        )
    with patch.object(
        database_session, "execute", wraps=database_session.execute
    ) as executed:
        service.ensure_monthly_records(
            user.id, resource, date(2026, 3, 1), date(2026, 3, 31)
        )
    assert not any(
        "FROM monthly_plan_changes" in str(call.args[0])
        for call in executed.call_args_list
    )


@pytest.mark.parametrize(
    ("first", "end", "expected"),
    [
        (
            date(2026, 1, 31),
            date(2026, 4, 30),
            [
                date(2026, 1, 31),
                date(2026, 2, 28),
                date(2026, 3, 31),
                date(2026, 4, 30),
            ],
        ),
        (
            date(2024, 1, 30),
            date(2024, 3, 31),
            [date(2024, 1, 30), date(2024, 2, 29), date(2024, 3, 30)],
        ),
        (date(2026, 12, 5), date(2027, 1, 31), [date(2026, 12, 5), date(2027, 1, 5)]),
        (date(9999, 12, 31), date(9999, 12, 31), [date(9999, 12, 31)]),
    ],
)
def test_monthly_dates_keep_original_day_and_clamp_short_months(
    first: date, end: date, expected: list[date]
) -> None:
    assert list(monthly_dates(first, first.replace(day=1), end)) == expected
    assert list(monthly_dates(first, date(1, 1, 1), first)) == [first]
    assert list(monthly_dates(first, date(1, 1, 1), first.replace(day=1))) == (
        [] if first.day != 1 else [first]
    )


@pytest.mark.parametrize(("resource", "date_field"), RESOURCES)
@pytest.mark.parametrize("currency", ["ARS", "USD"])
def test_monthly_creation_and_repeated_queries_preserve_accounts_and_pending_history(
    api_client: TestClient,
    database_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    resource: str,
    date_field: str,
    currency: str,
) -> None:
    monkeypatch.setattr(
        "app.services.planning.financial_today", lambda: date(2026, 3, 15)
    )
    headers = _headers(database_session, "monthly-owner@example.com")
    other = _headers(database_session, "monthly-other@example.com")
    account = _create_account(api_client, headers)
    account_url = f"/api/v1/accounts/{account['id']}"
    before = api_client.get(account_url, headers=headers).json()
    history = api_client.get(account_url + "/balance-history", headers=headers).json()
    url = f"/api/v1/{resource}"
    created = api_client.post(
        url,
        headers=headers,
        json={
            "description": "Synthetic recurring",
            "amount": "999999999999999999.99",
            "currency": currency,
            date_field: "2026-01-31",
            "recurrence": "MONTHLY",
        },
    )
    assert created.status_code == 201
    assert created.json()["recurrence"] == "MONTHLY"
    assert created.json()["template_id"] is not None
    query = url + "?year=2026&month=3"
    entries = api_client.get(query, headers=headers).json()
    assert [item[date_field] for item in entries] == [
        "2026-01-31",
        "2026-02-28",
        "2026-03-31",
    ]
    for _ in range(3):
        assert api_client.get(query, headers=headers).json() == entries
    assert all(
        item["status"] == "PLANNED"
        and item["amount"] == "999999999999999999.99"
        and item["currency"] == currency
        for item in entries
    )
    assert api_client.get(query, headers=other).json() == []
    assert api_client.get(query + "&include_overdue=false", headers=headers).json() == [
        entries[-1]
    ]
    assert (
        api_client.get(query + "&limit=2", headers=headers).json()
        + api_client.get(query + "&offset=2&limit=2", headers=headers).json()
        == entries
    )
    assert api_client.get(account_url, headers=headers).json() == before
    assert (
        api_client.get(account_url + "/balance-history", headers=headers).json()
        == history
    )
    plan = database_session.get(MonthlyPlan, UUID(created.json()["template_id"]))
    assert plan is not None
    assert plan.amount == Decimal("999999999999999999.99")
    assert plan.first_date == date(2026, 1, 31)
    assert plan.generated_through == date(2026, 3, 1)


@pytest.mark.parametrize(("resource", "date_field"), RESOURCES)
def test_future_month_generation_does_not_skip_unvisited_months_or_start_early(
    api_client: TestClient,
    database_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    resource: str,
    date_field: str,
) -> None:
    monkeypatch.setattr(
        "app.services.planning.financial_today", lambda: date(2026, 10, 1)
    )
    headers = _headers(database_session, "future-monthly@example.com")
    url = f"/api/v1/{resource}"
    response = api_client.post(
        url,
        headers=headers,
        json={
            "description": "Synthetic future",
            "amount": "0.01",
            "currency": "USD",
            date_field: "2026-12-31",
            "recurrence": "MONTHLY",
        },
    )
    assert response.status_code == 201
    assert api_client.get(url + "?year=2026&month=10", headers=headers).json() == []
    assert (
        api_client.get(
            url + "?year=2027&month=2&include_overdue=false", headers=headers
        ).json()[0][date_field]
        == "2027-02-28"
    )
    monkeypatch.setattr(
        "app.services.planning.financial_today", lambda: date(2027, 3, 1)
    )
    entries = api_client.get(url + "?year=2027&month=3", headers=headers).json()
    assert [entry[date_field] for entry in entries] == [
        "2026-12-31",
        "2027-01-31",
        "2027-02-28",
        "2027-03-31",
    ]
    assert api_client.get(url + "?year=2027&month=3", headers=headers).json() == entries


@pytest.mark.parametrize(("resource", "date_field"), RESOURCES)
@pytest.mark.parametrize("invalid", ["0", "-1", "1.001", "1000000000000000000"])
def test_invalid_monthly_creation_does_not_persist_template(
    api_client: TestClient,
    database_session: Session,
    resource: str,
    date_field: str,
    invalid: str,
) -> None:
    headers = _headers(database_session, "invalid-monthly@example.com")
    assert (
        api_client.post(
            f"/api/v1/{resource}",
            headers=headers,
            json={
                "description": "Synthetic",
                "amount": invalid,
                "currency": "ARS",
                date_field: "2026-10-01",
                "recurrence": "MONTHLY",
            },
        ).status_code
        == 422
    )
    assert database_session.scalar(select(MonthlyPlan)) is None


def test_period_uniqueness_preserves_existing_instance(
    database_session: Session,
) -> None:
    user = User(email="unique-monthly@example.com", password_hash="synthetic hash")
    database_session.add(user)
    database_session.commit()
    created = PlanningService(database_session).create_income(
        user_id=user.id,
        description="Synthetic",
        amount=Decimal("10.25"),
        currency=Currency.ARS,
        expected_date=date(2026, 10, 5),
        recurrence="MONTHLY",
    )
    plan = database_session.get(MonthlyPlan, created.template_id)
    assert plan is not None
    PlanningRepository(database_session).insert_occurrences(
        plan, [date(2026, 10, 8), date(2026, 10, 5)]
    )
    database_session.flush()
    assert database_session.scalars(select(PlannedIncome)).all() == [created]
    assert created.expected_date == date(2026, 10, 5)
    assert created.amount == Decimal("10.25")


def test_monthly_backfill_preserves_records_across_insert_batches(
    database_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "app.services.planning.financial_today", lambda: date(2026, 10, 1)
    )
    user = User(email="batch-monthly@example.com", password_hash="synthetic hash")
    database_session.add(user)
    database_session.commit()
    service = PlanningService(database_session)
    service.create_income(
        user_id=user.id,
        description="Synthetic long history",
        amount=Decimal("0.01"),
        currency=Currency.USD,
        expected_date=date(1980, 1, 31),
        recurrence="MONTHLY",
    )
    first_page = service.list_income(
        user.id,
        start=date(2026, 10, 1),
        end=date(2026, 10, 31),
        include_overdue=True,
        limit=100,
        offset=0,
    )
    assert len(first_page) == 100
    records = database_session.scalars(
        select(PlannedIncome)
        .where(PlannedIncome.user_id == user.id)
        .order_by(PlannedIncome.expected_date)
    ).all()
    assert len(records) == 562
    assert records[0].expected_date == date(1980, 1, 31)
    assert records[-1].expected_date == date(2026, 10, 31)
    assert len({record.recurrence_period for record in records}) == 562
    assert all(record.amount == Decimal("0.01") for record in records)


@pytest.mark.parametrize("kind", ["income", "commitments"])
def test_concurrent_month_generation_creates_one_instance_per_period(
    monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    monkeypatch.setattr(
        "app.services.planning.financial_today", lambda: date(2026, 3, 1)
    )
    engine = get_engine()
    user_id = uuid4()
    try:
        with Session(engine) as session:
            session.add(
                User(
                    id=user_id,
                    email=f"concurrent-{user_id}@example.com",
                    password_hash="synthetic hash",
                )
            )
            session.commit()
            service = PlanningService(session)
            if kind == "income":
                service.create_income(
                    user_id=user_id,
                    description="Synthetic",
                    amount=Decimal("1.01"),
                    currency=Currency.ARS,
                    expected_date=date(2026, 1, 31),
                    recurrence="MONTHLY",
                )
            else:
                service.create_commitment(
                    user_id=user_id,
                    description="Synthetic",
                    amount=Decimal("1.01"),
                    currency=Currency.USD,
                    due_date=date(2026, 1, 31),
                    recurrence="MONTHLY",
                )

        def read_month() -> int:
            with Session(engine) as session:
                service = PlanningService(session)
                if kind == "income":
                    return len(
                        service.list_income(
                            user_id,
                            start=date(2026, 3, 1),
                            end=date(2026, 3, 31),
                            include_overdue=True,
                            limit=50,
                            offset=0,
                        )
                    )
                return len(
                    service.list_commitments(
                        user_id,
                        start=date(2026, 3, 1),
                        end=date(2026, 3, 31),
                        include_overdue=True,
                        limit=50,
                        offset=0,
                    )
                )

        with ThreadPoolExecutor(max_workers=3) as pool:
            assert list(pool.map(lambda _: read_month(), range(3))) == [3, 3, 3]
        with Session(engine) as session:
            if kind == "income":
                assert (
                    len(
                        session.scalars(
                            select(PlannedIncome).where(
                                PlannedIncome.user_id == user_id
                            )
                        ).all()
                    )
                    == 3
                )
            else:
                assert (
                    len(
                        session.scalars(
                            select(PlannedCommitment).where(
                                PlannedCommitment.user_id == user_id
                            )
                        ).all()
                    )
                    == 3
                )
    finally:
        with Session(engine) as session:
            session.execute(delete(User).where(User.id == user_id))
            session.commit()
