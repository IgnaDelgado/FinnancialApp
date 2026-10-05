import os
import subprocess
import sys
from uuid import uuid4

from sqlalchemy import create_engine, text

from app.core.database import get_engine


def test_upgrade_from_last_merge_preserves_existing_accounts_and_confirmations() -> (
    None
):
    database_name = f"migration_review_{uuid4().hex}"
    url = get_engine().url.set(database=database_name)
    admin = create_engine(get_engine().url, isolation_level="AUTOCOMMIT")
    isolated = create_engine(url)
    env = dict(os.environ, DATABASE_URL=url.render_as_string(hide_password=False))

    def migrate(*arguments: str) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *arguments],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr

    with admin.connect() as connection:
        connection.execute(text(f"CREATE DATABASE {database_name}"))
    try:
        migrate("upgrade", "0006_remove_account_updated_at")
        user_id, account_id, snapshot_id = uuid4(), uuid4(), uuid4()
        with isolated.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO users (id,email,password_hash) VALUES "
                    "(:id,'migration@example.com','synthetic')"
                ),
                {"id": user_id},
            )
            connection.execute(
                text(
                    "INSERT INTO financial_accounts "
                    "(id,user_id,name,account_type,currency,current_balance,"
                    "is_liquid,balance_updated_at) "
                    "VALUES "
                    "(:id,:user,'Synthetic','BANK','ARS',100.01,true,'2026-10-01T12:00:00Z')"
                ),
                {"id": account_id, "user": user_id},
            )
            connection.execute(
                text(
                    "INSERT INTO account_balance_snapshots "
                    "(id,account_id,balance,recorded_at) VALUES "
                    "(:id,:account,100.01,'2026-10-01T12:00:00Z')"
                ),
                {"id": snapshot_id, "account": account_id},
            )
            original_account = connection.execute(
                text("SELECT * FROM financial_accounts")
            ).all()
            original_history = connection.execute(
                text("SELECT * FROM account_balance_snapshots")
            ).all()
        migrate("upgrade", "0008_preferred_accounts")
        with isolated.begin() as connection:
            income_id = uuid4()
            connection.execute(
                text(
                    "INSERT INTO planned_income "
                    "(id,user_id,description,amount,currency,expected_date,status,"
                    "recurrence,account_id,confirmed_at,already_in_balance) "
                    "VALUES "
                    "(:id,:user,'Synthetic',0.01,'ARS','2026-10-01','RECEIVED','ONE_TIME',:account,'2026-10-02T12:00:00Z',true)"
                ),
                {"id": income_id, "user": user_id, "account": account_id},
            )
            confirmed_before = connection.execute(
                text("SELECT * FROM planned_income")
            ).all()
        migrate("upgrade", "head")
        with isolated.connect() as connection:
            assert (
                connection.execute(text("SELECT * FROM financial_accounts")).all()
                == original_account
            )
            assert (
                connection.execute(
                    text("SELECT * FROM account_balance_snapshots")
                ).all()
                == original_history
            )
            assert (
                connection.execute(text("SELECT * FROM planned_income")).all()
                == confirmed_before
            )
            assert (
                connection.scalar(text("SELECT count(*) FROM confirmation_corrections"))
                == 0
            )
        # An empty maintenance migration can roll back without changing history.
        migrate("downgrade", "0008_preferred_accounts")
        migrate("upgrade", "head")
        with isolated.connect() as connection:
            assert (
                connection.execute(text("SELECT * FROM planned_income")).all()
                == confirmed_before
            )
    finally:
        isolated.dispose()
        with admin.connect() as connection:
            connection.execute(text(f"DROP DATABASE {database_name} WITH (FORCE)"))
        admin.dispose()
