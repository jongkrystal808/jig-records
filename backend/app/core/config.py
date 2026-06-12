from dataclasses import dataclass
import os


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
    api_v2_prefix: str = "/api/v2"
    database_url: str = _default_database_url()
    fixture_image_dir: str = os.getenv("FIXTURE_IMAGE_DIR", "./uploads/fixtures")
    auth_secret_key: str = os.getenv("AUTH_SECRET_KEY", "change-me-in-production")
    auth_token_ttl_seconds: int = int(os.getenv("AUTH_TOKEN_TTL_SECONDS", "86400"))


settings = Settings()
