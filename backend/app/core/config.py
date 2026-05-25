from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Fixture-M Lite API")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    api_v2_prefix: str = "/api/v2"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./fixture_m_lite.db")


settings = Settings()
