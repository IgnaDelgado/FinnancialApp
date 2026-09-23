from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.currency import Currency
from app.models.user import User


def test_user_defaults_to_ars_reference_currency(
    database_session: Session,
) -> None:
    user = User(
        email="learner@example.com",
        password_hash="$argon2id$synthetic-test-hash",
    )

    database_session.add(user)
    database_session.flush()
    database_session.refresh(user)

    assert isinstance(user.id, UUID)
    assert user.email == "learner@example.com"
    assert user.reference_currency is Currency.ARS
    assert user.created_at.tzinfo is not None
    assert user.updated_at.tzinfo is not None


def test_rejects_unnormalized_user_email(database_session: Session) -> None:
    user = User(
        email="Learner@Example.com",
        password_hash="$argon2id$synthetic-test-hash",
    )
    database_session.add(user)

    with pytest.raises(IntegrityError):
        database_session.flush()


def test_rejects_duplicate_user_email(database_session: Session) -> None:
    database_session.add_all(
        [
            User(
                email="duplicate@example.com",
                password_hash="$argon2id$first-synthetic-hash",
            ),
            User(
                email="duplicate@example.com",
                password_hash="$argon2id$second-synthetic-hash",
            ),
        ]
    )

    with pytest.raises(IntegrityError):
        database_session.flush()


def test_database_defaults_reference_currency_to_ars(
    database_session: Session,
) -> None:
    reference_currency = database_session.execute(
        text(
            """
            INSERT INTO users (id, email, password_hash)
            VALUES (:id, :email, :password_hash)
            RETURNING reference_currency
            """
        ),
        {
            "id": uuid4(),
            "email": "database-default@example.com",
            "password_hash": "$argon2id$synthetic-test-hash",
        },
    ).scalar_one()

    assert reference_currency == Currency.ARS.value


def test_database_rejects_unsupported_reference_currency(
    database_session: Session,
) -> None:
    with pytest.raises(IntegrityError):
        database_session.execute(
            text(
                """
                INSERT INTO users (id, email, password_hash, reference_currency)
                VALUES (:id, :email, :password_hash, :reference_currency)
                """
            ),
            {
                "id": uuid4(),
                "email": "unsupported-currency@example.com",
                "password_hash": "$argon2id$synthetic-test-hash",
                "reference_currency": "EUR",
            },
        )
