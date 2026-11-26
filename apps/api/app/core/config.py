from typing import Any

from pydantic import AliasChoices, Field, field_validator, model_validator
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
    SUPABASE_STORAGE_BUCKET: str = "resumes"
    LOCAL_RESUME_STORAGE_DIR: str = "./test-results/resumes"

    # Supabase Auth (exclusive identity provider)
    SUPABASE_URL: str = Field(
        default="",
        validation_alias=AliasChoices("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"),
    )
    SUPABASE_ANON_KEY: str = Field(
        default="",
        validation_alias=AliasChoices(
            "SUPABASE_ANON_KEY",
            "NEXT_PUBLIC_SUPABASE_ANON_KEY",
            "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
            "SUPABASE_PUBLISHABLE_KEY",
        ),
    )
    SUPABASE_SERVICE_ROLE_KEY: str = Field(
        default="",
        validation_alias=AliasChoices("SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SECRET_KEY"),
    )
    SUPABASE_JWT_SECRET: str = Field(
        default="",
        validation_alias=AliasChoices("SUPABASE_JWT_SECRET", "JWT_SECRET"),
    )
    SUPABASE_JWT_AUDIENCE: str = "authenticated"
    SUPABASE_JWT_ISSUER: str = ""
    SUPABASE_JWKS_URL: str = ""

    # Voice WebSocket Ticket & Frame Limits
    VOICE_TICKET_TTL_SECONDS: int = 30
    VOICE_MAX_MESSAGE_BYTES: int = 65536

    # Background Worker (ARQ & ML Runtime)
    ARQ_MAX_CONCURRENT_TASKS: int = 1
    ARQ_TASK_TIMEOUT_SECONDS: int = 300
    ARQ_MAX_TRIES: int = 3
    EMBEDDING_BACKFILL_BATCH_SIZE: int = 50
    EMBEDDING_STALE_PENDING_SECONDS: int = 600
    TORCH_NUM_THREADS: int = 4
    ML_MATCHING_MODEL_PATH: str = "ml/artifacts/minilm-nexteras-v1"
    ML_MAX_LOADED_MODELS: int = 1
    ENABLE_PRETRAINED_NLI: bool = False

    # AI & Providers
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    GEMINI_LIVE_MODEL: str = "gemini-2.5-flash"
    GEMINI_LIVE_WEBSOCKET_URL: str = (
        "wss://generativelanguage.googleapis.com/ws/"
        "google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent"
    )
    OLOSTEP_API_KEY: str = ""
    OLOSTEP_API_BASE_URL: str = "https://api.olostep.com/v1"
    CRUSTDATA_API_KEY: str = ""
    CRUSTDATA_API_BASE_URL: str = "https://api.crustdata.com"
    CRUSTDATA_API_VERSION: str = "2025-11-01"

    # Security, Rate Limiting & Playwright
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    PLAYWRIGHT_HEADLESS: bool = True
    PLAYWRIGHT_TIMEOUT_MS: int = 30000
    PLAYWRIGHT_SCREENSHOT_DIR: str = "./test-results/screenshots"
    PLAYWRIGHT_STORAGE_STATE_DIR: str = "./test-results/storage"

    # Observability & Analytics
    SENTRY_DSN: str = ""
    POSTHOG_API_KEY: str = ""
    POSTHOG_HOST: str = "https://us.i.posthog.com"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.strip().lower() == "production"

    @property
    def effective_jwt_issuer(self) -> str:
        """Return configured issuer or derive Supabase Auth issuer from SUPABASE_URL."""
        if self.SUPABASE_JWT_ISSUER:
            return self.SUPABASE_JWT_ISSUER.rstrip("/")
        if self.SUPABASE_URL:
            return f"{self.SUPABASE_URL.rstrip('/')}/auth/v1"
        return ""

    @property
    def effective_jwks_url(self) -> str:
        """Return configured JWKS URL or derive it from SUPABASE_URL."""
        if self.SUPABASE_JWKS_URL:
            return self.SUPABASE_JWKS_URL
        if self.SUPABASE_URL:
            return f"{self.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
        return ""

    @model_validator(mode="after")
    def enforce_production_safety(self) -> "Settings":
        """Ensure safe defaults and fail closed on unsafe production configuration."""
        if self.is_production:
            if "DEBUG" not in self.model_fields_set:
                self.DEBUG = False
            elif self.DEBUG:
                raise ValueError("DEBUG must be false when ENVIRONMENT=production.")

            if not self.effective_jwt_issuer:
                raise ValueError(
                    "SUPABASE_URL or SUPABASE_JWT_ISSUER must be configured when ENVIRONMENT=production."
                )

            if not self.REDIS_URL.strip():
                raise ValueError("REDIS_URL must be configured when ENVIRONMENT=production.")

        return self

    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
