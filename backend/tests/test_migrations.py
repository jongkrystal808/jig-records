from __future__ import annotations

import importlib
import json
import logging
import os
import sys
import tempfile
import unittest
from pathlib import Path

from alembic import command
from sqlalchemy import create_engine, inspect, text

from backend.app.core.audit_logging import REQUEST_ID_HEADER, register_audit_middleware
from backend.app.core.migrations import (
    _alembic_config,
    _normalize_alembic_revisions,
    _prepare_alembic_version_table,
    apply_runtime_compatibility_fixes,
    inspect_migration_compatibility,
)
from backend.app.core.auth import create_session_token
from backend.app.core.config import settings
from backend.app.core.logging import AUDIT_LOGGER_NAME, get_audit_log_path, setup_logging, write_audit_log


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

    def test_runtime_gate_allows_empty_database_without_version_table(self) -> None:
        with self.engine.begin() as connection:
            report = inspect_migration_compatibility(connection)
            self.assertTrue(report.runtime_upgrade_allowed)
            self.assertFalse(report.alembic_version_table_present)

    def test_runtime_gate_blocks_legacy_alias_revision_until_manual_fix(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(191) NOT NULL PRIMARY KEY)"))
            connection.execute(
                text("INSERT INTO alembic_version(version_num) VALUES ('0004_model_station_fixture_requirements')")
            )

            report = inspect_migration_compatibility(connection)
            self.assertFalse(report.runtime_upgrade_allowed)
            self.assertTrue(report.has_legacy_revision_alias)
            self.assertTrue(report.has_revision_below_gate)

            fixed_report = apply_runtime_compatibility_fixes(connection)
            self.assertFalse(fixed_report.has_legacy_revision_alias)
            self.assertFalse(fixed_report.runtime_upgrade_allowed)

    def test_runtime_gate_blocks_legacy_app_schema_without_version_table(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(text("CREATE TABLE customers (id INTEGER PRIMARY KEY, code VARCHAR(32), name VARCHAR(120))"))
            report = inspect_migration_compatibility(connection)
            self.assertFalse(report.runtime_upgrade_allowed)
            self.assertTrue(report.has_legacy_schema_without_version_table)


    def test_alembic_config_accepts_percent_encoded_database_url(self) -> None:
        original_database_url = settings.database_url
        encoded_url = "mysql+pymysql://fixture:password%23@example.test/database"
        try:
            object.__setattr__(settings, "database_url", encoded_url)
            config = _alembic_config()
            self.assertEqual(config.get_main_option("sqlalchemy.url"), encoded_url)
        finally:
            object.__setattr__(settings, "database_url", original_database_url)


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


class LoggingSetupTests(unittest.TestCase):
    def test_setup_logging_configures_backend_logger_for_standalone_cli(self) -> None:
        root_logger = logging.getLogger()
        backend_logger = logging.getLogger("backend.app")
        original_handlers = list(root_logger.handlers)
        original_root_level = root_logger.level
        original_backend_level = backend_logger.level
        try:
            root_logger.handlers.clear()
            root_logger.setLevel(logging.WARNING)
            backend_logger.setLevel(logging.NOTSET)

            setup_logging()

            self.assertEqual(backend_logger.level, logging.INFO)
            self.assertTrue(root_logger.handlers)
        finally:
            root_logger.handlers.clear()
            root_logger.handlers.extend(original_handlers)
            root_logger.setLevel(original_root_level)
            backend_logger.setLevel(original_backend_level)

    def test_write_audit_log_creates_logs_audit_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            audit_logger = logging.getLogger(AUDIT_LOGGER_NAME)
            original_handlers = list(audit_logger.handlers)
            original_propagate = audit_logger.propagate
            original_log_dir = settings.log_dir
            original_filename = settings.audit_log_filename
            try:
                for handler in audit_logger.handlers:
                    handler.close()
                audit_logger.handlers.clear()
                object.__setattr__(settings, "log_dir", temp_dir)
                object.__setattr__(settings, "audit_log_filename", "audit.log")

                write_audit_log({"event_type": "test", "message": "hello"})

                audit_log_path = get_audit_log_path()
                self.assertTrue(audit_log_path.exists())
                payload = json.loads(audit_log_path.read_text(encoding="utf-8").strip())
                self.assertEqual(payload["event_type"], "test")
                self.assertEqual(payload["message"], "hello")
            finally:
                for handler in audit_logger.handlers:
                    handler.close()
                audit_logger.handlers.clear()
                audit_logger.handlers.extend(original_handlers)
                audit_logger.propagate = original_propagate
                object.__setattr__(settings, "log_dir", original_log_dir)
                object.__setattr__(settings, "audit_log_filename", original_filename)


class AuditMiddlewareTests(unittest.TestCase):
    def test_request_audit_log_records_authenticated_user(self) -> None:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        with tempfile.TemporaryDirectory() as temp_dir:
            audit_logger = logging.getLogger(AUDIT_LOGGER_NAME)
            original_handlers = list(audit_logger.handlers)
            original_propagate = audit_logger.propagate
            original_log_dir = settings.log_dir
            original_filename = settings.audit_log_filename
            try:
                for handler in audit_logger.handlers:
                    handler.close()
                audit_logger.handlers.clear()
                object.__setattr__(settings, "log_dir", temp_dir)
                object.__setattr__(settings, "audit_log_filename", "audit.log")

                app = FastAPI()
                register_audit_middleware(app)

                @app.get("/ping")
                def ping():
                    return {"ok": True}

                token = create_session_token(mode="guest", display_name="訪客測試")
                client = TestClient(app)
                response = client.get(
                    "/ping?x=1&password=private-password&access_token=private-token",
                    headers={"Authorization": f"Bearer {token}"},
                )

                self.assertEqual(response.status_code, 200)
                lines = get_audit_log_path().read_text(encoding="utf-8").strip().splitlines()
                payload = json.loads(lines[-1])
                self.assertEqual(payload["event_type"], "request_audit")
                self.assertEqual(payload["actor"]["mode"], "guest")
                self.assertEqual(payload["actor"]["display_name"], "訪客測試")
                self.assertEqual(payload["request"]["path"], "/ping")
                self.assertEqual(
                    payload["request"]["query"],
                    "x=1&password=%5BREDACTED%5D&access_token=%5BREDACTED%5D",
                )
                self.assertEqual(payload["response"]["status_code"], 200)
                self.assertEqual(response.headers[REQUEST_ID_HEADER], payload["request_id"])
                self.assertRegex(payload["request_id"], r"^[0-9a-f]{32}$")
                self.assertNotIn("private-password", lines[-1])
                self.assertNotIn("private-token", lines[-1])
            finally:
                for handler in audit_logger.handlers:
                    handler.close()
                audit_logger.handlers.clear()
                audit_logger.handlers.extend(original_handlers)
                audit_logger.propagate = original_propagate
                object.__setattr__(settings, "log_dir", original_log_dir)
                object.__setattr__(settings, "audit_log_filename", original_filename)


class BootstrapFlowTests(unittest.TestCase):
    def _load_migrations_module(self) -> object:
        target_modules = [
            "backend.app.core.migrations",
            "backend.app.core.config",
        ]
        for module_name in target_modules:
            sys.modules.pop(module_name, None)
        return importlib.import_module("backend.app.core.migrations")

    def _load_bootstrap_module(self) -> object:
        target_modules = [
            "backend.app.bootstrap",
            "backend.app.core.config",
            "backend.app.core.database",
            "backend.app.core.migrations",
            "backend.app.services.auth_service",
        ]
        for module_name in target_modules:
            sys.modules.pop(module_name, None)
        return importlib.import_module("backend.app.bootstrap")

    def test_bootstrap_application_runs_migrations_and_creates_default_admin_once(self) -> None:
        temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_file.close()
        db_path = Path(temp_file.name)
        original = os.environ.copy()
        try:
            os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
            os.environ["AUTH_SECRET_KEY"] = "test-secret-key"
            os.environ["APP_ENV"] = "development"
            bootstrap_module = self._load_bootstrap_module()

            with self.assertLogs("backend.app.core.migrations", level="INFO") as captured:
                bootstrap_module.bootstrap_application()
            bootstrap_module.bootstrap_application()

            engine = create_engine(f"sqlite:///{db_path}")
            with engine.begin() as connection:
                revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                admin_count = connection.execute(text("SELECT COUNT(*) FROM users WHERE username = 'admin'")).scalar_one()
                admin_role = connection.execute(text("SELECT role FROM users WHERE username = 'admin'")).scalar_one()
                shortcut_columns = {
                    column["name"] for column in inspect(connection).get_columns("user_model_shortcuts")
                }
                fixture_requirement_columns = {
                    column["name"] for column in inspect(connection).get_columns("fixture_requirements")
                }
                material_transaction_columns = {
                    column["name"] for column in inspect(connection).get_columns("material_transactions")
                }
                user_columns = {
                    column["name"] for column in inspect(connection).get_columns("users")
                }
                table_names = set(inspect(connection).get_table_names())
            engine.dispose()

            self.assertEqual(revision, "0021_user_auth_version")
            self.assertEqual(admin_count, 1)
            self.assertEqual(admin_role, "super_admin")
            self.assertIn("designated_mode", fixture_requirement_columns)
            self.assertIn("fixture_requirement_identifiers", table_names)
            self.assertIn("actor_user_id", material_transaction_columns)
            self.assertIn("auth_version", user_columns)
            self.assertIn("storage_containers", table_names)
            self.assertIn("storage_codes", table_names)
            self.assertIn("fixture_placements", table_names)
            self.assertEqual(
                shortcut_columns,
                {
                    "id",
                    "user_id",
                    "customer_id",
                    "model_id",
                    "query_count",
                    "last_queried_at",
                    "is_pinned",
                    "created_at",
                    "updated_at",
                },
            )
            self.assertTrue(
                any('"event": "migration_runtime_gate"' in message and '"outcome": "passed"' in message for message in captured.output)
            )
        finally:
            database_module = sys.modules.get("backend.app.core.database")
            if database_module is not None:
                database_module.engine.dispose()
            os.environ.clear()
            os.environ.update(original)
            db_path.unlink(missing_ok=True)

    def test_storage_migration_backfills_legacy_comma_locations_and_station_context(self) -> None:
        temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_file.close()
        db_path = Path(temp_file.name)
        original_database_url = settings.database_url
        engine = None
        try:
            object.__setattr__(settings, "database_url", f"sqlite:///{db_path.as_posix()}")
            command.upgrade(_alembic_config(), "0018_designated_ids")
            engine = create_engine(f"sqlite:///{db_path.as_posix()}")
            with engine.begin() as connection:
                connection.execute(text("DROP TABLE fixture_placements"))
                connection.execute(text("DROP TABLE storage_codes"))
                connection.execute(text("DROP TABLE storage_containers"))
                connection.execute(text("INSERT INTO customers (id, code, name) VALUES (99, 'C99', 'Customer 99')"))
                connection.execute(text("INSERT INTO machine_models (id, customer_id, code, name, is_active) VALUES (99, 99, 'E1210', 'ioLogik E1210', 1)"))
                connection.execute(text("INSERT INTO stations (id, customer_id, code, name, is_active) VALUES (99, 99, 'T2', 'Test 2', 1)"))
                connection.execute(
                    text("INSERT INTO fixtures (id, customer_id, code, name, line_storage_location, department_storage_location, is_active) VALUES (99, 99, 'L-00091', 'Fixture', :location, NULL, 1)"),
                    {"location": "T2, AXG001\uFF0CMOXA001"},
                )
                connection.execute(text("INSERT INTO fixture_requirements (id, model_id, station_id, fixture_id, required_qty, designated_mode) VALUES (99, 99, 99, 99, 1, 0)"))
            engine.dispose()

            command.upgrade(_alembic_config(), "head")

            engine = create_engine(f"sqlite:///{db_path.as_posix()}")
            with engine.begin() as connection:
                revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                codes = connection.execute(text("SELECT code FROM storage_codes ORDER BY code")).scalars().all()
                placements = connection.execute(
                    text("SELECT target_type, model_id, station_id FROM fixture_placements ORDER BY target_type")
                ).mappings().all()
            engine.dispose()
            self.assertEqual(revision, "0021_user_auth_version")
            self.assertEqual(codes, ["AXG001", "MOXA001"])
            self.assertEqual(len(placements), 3)
            self.assertEqual(
                [row for row in placements if row["target_type"] == "model_station"],
                [{"target_type": "model_station", "model_id": 99, "station_id": 99}],
            )
        finally:
            if engine is not None:
                engine.dispose()
            object.__setattr__(settings, "database_url", original_database_url)
            db_path.unlink(missing_ok=True)

    def test_transaction_actor_migration_backfills_only_unique_user_matches(self) -> None:
        temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_file.close()
        db_path = Path(temp_file.name)
        original_database_url = settings.database_url
        engine = None
        try:
            object.__setattr__(settings, "database_url", f"sqlite:///{db_path.as_posix()}")
            command.upgrade(_alembic_config(), "0019_fixture_storage")
            engine = create_engine(f"sqlite:///{db_path.as_posix()}")
            with engine.begin() as connection:
                connection.execute(text("INSERT INTO customers (id, code, name) VALUES (90, 'C90', 'Customer 90')"))
                connection.execute(
                    text(
                        """
                        INSERT INTO users (id, username, password_hash, display_name, role, is_active)
                        VALUES
                            (90, 'alice', 'hash', 'Alice', 'user', 1),
                            (91, 'bob', 'hash', 'Shared Name', 'user', 1),
                            (92, 'carol', 'hash', 'Shared Name', 'user', 1)
                        """
                    )
                )
                connection.execute(
                    text(
                        """
                        INSERT INTO material_transactions (
                            id, customer_id, transaction_type, transaction_no, occurred_at,
                            actor_user_id, created_by, note
                        )
                        VALUES
                            (90, 90, 'receipt', 'LEGACY-ACTOR-UNIQUE', CURRENT_TIMESTAMP, NULL, 'alice', NULL),
                            (91, 90, 'receipt', 'LEGACY-ACTOR-AMBIGUOUS', CURRENT_TIMESTAMP, NULL, 'Shared Name', NULL)
                        """
                    )
                )
            engine.dispose()

            command.upgrade(_alembic_config(), "head")

            engine = create_engine(f"sqlite:///{db_path.as_posix()}")
            with engine.begin() as connection:
                actor_rows = connection.execute(
                    text("SELECT transaction_no, actor_user_id FROM material_transactions ORDER BY id")
                ).mappings().all()
            engine.dispose()

            self.assertEqual(
                actor_rows,
                [
                    {"transaction_no": "LEGACY-ACTOR-UNIQUE", "actor_user_id": 90},
                    {"transaction_no": "LEGACY-ACTOR-AMBIGUOUS", "actor_user_id": None},
                ],
            )
        finally:
            if engine is not None:
                engine.dispose()
            object.__setattr__(settings, "database_url", original_database_url)
            db_path.unlink(missing_ok=True)

    def test_auth_version_migration_backfills_existing_users(self) -> None:
        temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_file.close()
        db_path = Path(temp_file.name)
        original_database_url = settings.database_url
        migrations_logger = logging.getLogger("backend.app.core.migrations")
        original_logger_disabled = migrations_logger.disabled
        engine = None
        try:
            object.__setattr__(settings, "database_url", f"sqlite:///{db_path.as_posix()}")
            command.upgrade(_alembic_config(), "0020_transaction_actor")
            engine = create_engine(f"sqlite:///{db_path.as_posix()}")
            with engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        INSERT INTO users (id, username, password_hash, display_name, role, is_active)
                        VALUES (90, 'legacy-user', 'hash', 'Legacy User', 'user', 1)
                        """
                    )
                )
            engine.dispose()

            command.upgrade(_alembic_config(), "head")

            engine = create_engine(f"sqlite:///{db_path.as_posix()}")
            with engine.begin() as connection:
                revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                auth_version = connection.execute(
                    text("SELECT auth_version FROM users WHERE id = 90")
                ).scalar_one()
            engine.dispose()

            self.assertEqual(revision, "0021_user_auth_version")
            self.assertEqual(auth_version, 1)
        finally:
            if engine is not None:
                engine.dispose()
            migrations_logger.disabled = original_logger_disabled
            object.__setattr__(settings, "database_url", original_database_url)
            db_path.unlink(missing_ok=True)

    def test_blocked_runtime_gate_report_is_logged(self) -> None:
        temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_file.close()
        db_path = Path(temp_file.name)
        try:
            engine = create_engine(f"sqlite:///{db_path}")
            with engine.begin() as connection:
                connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(191) NOT NULL PRIMARY KEY)"))
                connection.execute(
                    text("INSERT INTO alembic_version(version_num) VALUES ('0004_model_station_fixture_requirements')")
                )
                migrations_module = self._load_migrations_module()
                report = migrations_module.inspect_migration_compatibility(connection)
                self.assertFalse(report.runtime_upgrade_allowed)

                with self.assertLogs("backend.app.core.migrations", level="ERROR") as captured:
                    migrations_module.log_migration_gate_report(
                        report,
                        source="runtime_startup",
                        outcome="blocked",
                    )

            self.assertTrue(
                any('"event": "migration_runtime_gate"' in message and '"outcome": "blocked"' in message for message in captured.output)
            )
        finally:
            engine.dispose()
            db_path.unlink(missing_ok=True)

    def test_app_startup_gate_report_can_be_logged_as_passed(self) -> None:
        temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_file.close()
        db_path = Path(temp_file.name)
        try:
            engine = create_engine(f"sqlite:///{db_path}")
            with engine.begin() as connection:
                connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(191) NOT NULL PRIMARY KEY)"))
                connection.execute(text("INSERT INTO alembic_version(version_num) VALUES ('0011_search_indexes')"))
                migrations_module = self._load_migrations_module()
                report = migrations_module.inspect_migration_compatibility(connection)
                self.assertTrue(report.runtime_upgrade_allowed)

                with self.assertLogs("backend.app.core.migrations", level="INFO") as captured:
                    migrations_module.log_migration_gate_report(
                        report,
                        source="app_startup",
                        outcome="passed",
                    )

            self.assertTrue(
                any('"event": "migration_runtime_gate"' in message and '"source": "app_startup"' in message and '"outcome": "passed"' in message for message in captured.output)
            )
        finally:
            engine.dispose()
            db_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
