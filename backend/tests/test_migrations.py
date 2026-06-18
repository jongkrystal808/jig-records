from __future__ import annotations

import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine, text

from backend.app.core.migrations import _normalize_alembic_revisions, _prepare_alembic_version_table


class MigrationPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_file.close()
        self.db_path = Path(temp_file.name)
        self.engine = create_engine(f"sqlite:///{self.db_path}")

    def tearDown(self) -> None:
        self.engine.dispose()
        self.db_path.unlink(missing_ok=True)

    def test_normalize_legacy_revision_alias(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(191) NOT NULL PRIMARY KEY)"))
            connection.execute(
                text("INSERT INTO alembic_version(version_num) VALUES ('0004_model_station_fixture_requirements')")
            )

            _prepare_alembic_version_table(connection)

            revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            self.assertEqual(revision, "0004_model_station_scope")

    def test_prepare_skips_when_version_table_missing(self) -> None:
        with self.engine.begin() as connection:
            _prepare_alembic_version_table(connection)

    def test_normalize_is_noop_for_current_revision(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(191) NOT NULL PRIMARY KEY)"))
            connection.execute(text("INSERT INTO alembic_version(version_num) VALUES ('0004_model_station_scope')"))

            _normalize_alembic_revisions(connection)

            revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            self.assertEqual(revision, "0004_model_station_scope")


class RuntimeSafetySettingsTests(unittest.TestCase):
    def _load_settings_module(self) -> object:
        module_name = "backend.app.core.config"
        sys.modules.pop(module_name, None)
        return importlib.import_module(module_name)

    def test_production_requires_non_default_auth_secret(self) -> None:
        original = os.environ.copy()
        try:
            os.environ["APP_ENV"] = "production"
            os.environ["DATABASE_URL"] = "mysql+pymysql://user:pass@db:3306/app?charset=utf8mb4"
            os.environ["AUTH_SECRET_KEY"] = "change-me-in-production"
            module = self._load_settings_module()
            with self.assertRaisesRegex(RuntimeError, "AUTH_SECRET_KEY"):
                module.settings.validate_runtime_safety()
        finally:
            os.environ.clear()
            os.environ.update(original)

    def test_production_rejects_sqlite_fallback(self) -> None:
        original = os.environ.copy()
        try:
            os.environ["APP_ENV"] = "production"
            os.environ.pop("DATABASE_URL", None)
            os.environ.pop("DB_HOST", None)
            os.environ["AUTH_SECRET_KEY"] = "strong-secret"
            module = self._load_settings_module()
            with self.assertRaisesRegex(RuntimeError, "SQLite fallback"):
                module.settings.validate_runtime_safety()
        finally:
            os.environ.clear()
            os.environ.update(original)


if __name__ == "__main__":
    unittest.main()
