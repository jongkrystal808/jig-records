from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Connection

from backend.app.core.config import settings

REVISION_ALIASES = {
    "0004_model_station_fixture_requirements": "0004_model_station_scope",
}


def _alembic_config() -> Config:
    root = Path(__file__).resolve().parents[3]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "backend" / "alembic"))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    return config


def _ensure_alembic_version_capacity(connection: Connection) -> None:
    if connection.dialect.name not in {"mysql", "mariadb"}:
        return

    inspector = inspect(connection)
    if "alembic_version" not in inspector.get_table_names():
        return

    version_column = next(
        (column for column in inspector.get_columns("alembic_version") if column["name"] == "version_num"),
        None,
    )
    if version_column is None:
        return

    current_length = getattr(version_column["type"], "length", None)
    if current_length is not None and current_length >= 191:
        return

    connection.execute(text("ALTER TABLE alembic_version MODIFY COLUMN version_num VARCHAR(191) NOT NULL"))


def _normalize_alembic_revisions(connection: Connection) -> None:
    inspector = inspect(connection)
    if "alembic_version" not in inspector.get_table_names():
        return

    for legacy_revision, canonical_revision in REVISION_ALIASES.items():
        connection.execute(
            text(
                """
                UPDATE alembic_version
                SET version_num = :canonical_revision
                WHERE version_num = :legacy_revision
                """
            ),
            {
                "canonical_revision": canonical_revision,
                "legacy_revision": legacy_revision,
            },
        )


def _prepare_alembic_version_table(connection: Connection) -> None:
    _ensure_alembic_version_capacity(connection)
    _normalize_alembic_revisions(connection)


def upgrade_database() -> None:
    engine = create_engine(settings.database_url)
    try:
        with engine.begin() as connection:
            _prepare_alembic_version_table(connection)
    finally:
        engine.dispose()

    command.upgrade(_alembic_config(), "head")
