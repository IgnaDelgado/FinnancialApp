import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_rejects_example_jwt_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(
            app_environment="production",
            database_url="postgresql+psycopg://synthetic",
            jwt_secret_key="replace_with_at_least_32_random_characters",
        )


def test_cors_origins_are_parsed_and_normalized() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://synthetic",
        jwt_secret_key="synthetic-test-secret-key-with-32-characters",
        cors_allowed_origins="https://app.example.com/, http://localhost:8081",
    )

    assert settings.cors_allowed_origin_list == [
        "https://app.example.com",
        "http://localhost:8081",
    ]


def test_cors_rejects_wildcard_origin() -> None:
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql+psycopg://synthetic",
            jwt_secret_key="synthetic-test-secret-key-with-32-characters",
            cors_allowed_origins="*",
        )


def test_cors_rejects_origin_with_path() -> None:
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql+psycopg://synthetic",
            jwt_secret_key="synthetic-test-secret-key-with-32-characters",
            cors_allowed_origins="https://app.example.com/login",
        )
