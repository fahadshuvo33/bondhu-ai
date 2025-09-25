from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    app_name: str = "AI Study Hub"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # Security
    secret_key: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Database
    database_url: str

    # Redis
    redis_url: str

    # AI Providers
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None

    # Payment
    bkash_app_key: Optional[str] = None
    bkash_app_secret: Optional[str] = None
    bkash_username: Optional[str] = None
    bkash_password: Optional[str] = None
    bkash_base_url: Optional[str] = None

    # SMS
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None

    # File Storage
    upload_path: str = "./uploads"
    max_upload_size: int = 20 * 1024 * 1024  # 20MB

    # Rate Limiting
    rate_limit_per_minute: int = 60

    # Monitoring
    sentry_dsn: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Note: Do NOT instantiate `settings` at import time. Some tools (alembic)
# import project modules during migrations before environment variables are
# available which would raise validation errors. Call `get_settings()` at
# runtime where needed, for example inside request handlers or startup code.
