from functools import lru_cache
from typing import Literal, Self
from urllib.parse import urlsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_JWT_SECRET_PLACEHOLDER = "replace_with_at_least_32_random_characters"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

    app_environment: Literal["development", "test", "production"] = "development"
    database_url: str = Field(min_length=1)
    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=15, ge=1, le=60)
    refresh_token_expire_days: int = Field(default=20, ge=1, le=90)
    session_absolute_expire_days: int = Field(default=90, ge=1, le=365)
    cors_allowed_origins: str = ""

    @field_validator("cors_allowed_origins")
    @classmethod
    def validate_cors_origins(cls, value: str) -> str:
        for raw_origin in value.split(","):
            origin = raw_origin.strip().rstrip("/")
            if not origin:
                continue
            parsed = urlsplit(origin)
            if (
                origin == "*"
                or parsed.scheme not in {"http", "https"}
                or not parsed.netloc
                or parsed.username is not None
                or parsed.password is not None
                or parsed.path
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError(
                    "CORS_ALLOWED_ORIGINS must contain only explicit HTTP origins"
                )
        return value

    @property
    def cors_allowed_origin_list(self) -> list[str]:
        return [
            origin.strip().rstrip("/")
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]

    @property
    def cors_allow_origin_regex(self) -> str | None:
        if self.app_environment in {"development", "test"}:
            return r"^http://(?:localhost|127\.0\.0\.1)(?::\d+)?$"
        return None

    @model_validator(mode="after")
    def reject_placeholder_jwt_secret_in_production(self) -> Self:
        if (
            self.app_environment == "production"
            and self.jwt_secret_key == _JWT_SECRET_PLACEHOLDER
        ):
            raise ValueError("JWT_SECRET_KEY must be replaced in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
