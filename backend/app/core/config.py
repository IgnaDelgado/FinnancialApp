from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

    app_environment: Literal["development", "test", "production"] = "development"
    database_url: str = Field(min_length=1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
