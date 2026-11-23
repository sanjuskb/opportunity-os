from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    APP_NAME: str = "Opportunity OS API"

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v: Any) -> bool:
        if isinstance(v, str):
            return v.lower() in ("true", "1", "t", "yes", "y", "debug")
        return bool(v)

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Database & Storage
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:54322/postgres"
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI & Providers
    GEMINI_API_KEY: str = ""
    OLOSTEP_API_KEY: str = ""
    CRUSTDATA_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
