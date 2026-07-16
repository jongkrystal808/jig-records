from dataclasses import dataclass
import os
from pathlib import Path


def _normalize_environment(raw: str | None) -> str:
    value = (raw or "development").strip().lower()
    if value in {"prod", "production"}:
        return "production"
    if value in {"stage", "staging"}:
        return "staging"
    if value in {"test", "testing"}:
        return "testing"
    return "development"


def _default_database_url() -> str:
    explicit = os.getenv("DATABASE_URL")
    if explicit:
        return explicit

    db_host = os.getenv("DB_HOST")
    if not db_host:
        return "sqlite:///./fixture_m_lite.db"

    db_port = os.getenv("DB_PORT", "3306")
    db_user = os.getenv("DB_USER", "fixture_user")
    db_password = os.getenv("DB_PASSWORD", "fixture_pass")
    db_name = os.getenv("DB_NAME", "fixture_m_lite")
    return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Fixture-M Lite API")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    environment: str = _normalize_environment(os.getenv("APP_ENV") or os.getenv("ENVIRONMENT"))
    api_v2_prefix: str = "/api/v2"
    database_url: str = _default_database_url()
    fixture_image_dir: str = os.getenv("FIXTURE_IMAGE_DIR", "./uploads/fixtures")
    auth_secret_key: str = os.getenv("AUTH_SECRET_KEY", "change-me-in-production")
    auth_token_ttl_seconds: int = int(os.getenv("AUTH_TOKEN_TTL_SECONDS", "86400"))
    default_admin_password: str | None = os.getenv("DEFAULT_ADMIN_PASSWORD")
    log_dir: str = os.getenv("LOG_DIR", str(Path("logs")))
    audit_log_filename: str = os.getenv("AUDIT_LOG_FILENAME", "audit.log")

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def uses_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def uses_default_auth_secret(self) -> bool:
        return self.auth_secret_key == "change-me-in-production"

    @property
    def uses_default_admin_password(self) -> bool:
        return (self.default_admin_password or "").strip() in {"", "admin123"}

    def validate_runtime_safety(self) -> None:
        if not self.is_production:
            return
        if self.uses_default_auth_secret:
            raise RuntimeError("AUTH_SECRET_KEY must be set to a strong non-default value in production")
        if self.uses_sqlite:
            raise RuntimeError("Production requires an explicit MySQL DATABASE_URL or DB_* configuration; SQLite fallback is not allowed")


settings = Settings()
