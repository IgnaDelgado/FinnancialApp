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
