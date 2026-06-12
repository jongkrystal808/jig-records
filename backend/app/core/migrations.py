from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

from backend.app.core.config import settings


def _alembic_config() -> Config:
    root = Path(__file__).resolve().parents[3]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "backend" / "alembic"))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    return config


def upgrade_database() -> None:
    command.upgrade(_alembic_config(), "head")
