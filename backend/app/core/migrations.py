from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Connection

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

REVISION_ALIASES = {
    "0004_model_station_fixture_requirements": "0004_model_station_scope",
}
RUNTIME_MIGRATION_GATE_REVISION = "0011_search_indexes"
ALEMBIC_VERSION_MIN_LENGTH = 191
OFFLINE_MIGRATION_CHECK_COMMAND = "python -m backend.app.tools.migration_check"

CORE_APP_TABLES = {
    "audit_logs",
    "customers",
    "fixture_requirements",
    "fixtures",
    "machine_models",
    "material_transaction_items",
    "material_transactions",
    "stations",
    "users",
}


class RuntimeMigrationGateError(RuntimeError):
    pass


@dataclass(frozen=True)
class MigrationCompatibilityReport:
    current_revisions: tuple[str, ...]
    database_tables: tuple[str, ...]
    alembic_version_table_present: bool
    alembic_version_length: int | None
    requires_version_table_resize: bool
    has_legacy_revision_alias: bool
    has_revision_below_gate: bool
    has_unknown_revision: bool
    has_legacy_schema_without_version_table: bool
    has_multiple_heads: bool
    runtime_upgrade_allowed: bool

    @property
    def current_revision_display(self) -> str:
        if not self.current_revisions:
            return "<none>"
        return ", ".join(self.current_revisions)

    @property
    def issue_codes(self) -> tuple[str, ...]:
        issues: list[str] = []
        if self.has_legacy_schema_without_version_table:
            issues.append("legacy_schema_without_version_table")
        if self.requires_version_table_resize:
            issues.append("alembic_version_too_short")
        if self.has_legacy_revision_alias:
            issues.append("legacy_revision_alias")
        if self.has_revision_below_gate:
            issues.append("revision_below_gate")
        if self.has_unknown_revision:
            issues.append("unknown_revision")
        if self.has_multiple_heads:
            issues.append("multiple_heads")
        return tuple(issues)


def _alembic_config() -> Config:
    root = Path(__file__).resolve().parents[3]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "backend" / "alembic"))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    return config


def _alembic_script_directory() -> ScriptDirectory:
    return ScriptDirectory.from_config(_alembic_config())


def _current_revisions(connection: Connection) -> tuple[str, ...]:
    inspector = inspect(connection)
    if "alembic_version" not in inspector.get_table_names():
        return ()
    rows = connection.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num ASC")).scalars().all()
    return tuple(str(row) for row in rows)


def _alembic_version_length(connection: Connection) -> int | None:
    inspector = inspect(connection)
    if "alembic_version" not in inspector.get_table_names():
        return None

    version_column = next(
        (column for column in inspector.get_columns("alembic_version") if column["name"] == "version_num"),
        None,
    )
    if version_column is None:
        return None
    return getattr(version_column["type"], "length", None)


def _revision_chain(script: ScriptDirectory, revision: str) -> set[str]:
    try:
        return {item.revision for item in script.walk_revisions(base="base", head=revision)}
    except Exception:
        return set()


def _is_revision_at_or_above_gate(script: ScriptDirectory, revision: str, gate_revision: str) -> bool:
    if revision == gate_revision:
        return True
    current_chain = _revision_chain(script, revision)
    return gate_revision in current_chain


def inspect_migration_compatibility(
    connection: Connection,
    *,
    gate_revision: str = RUNTIME_MIGRATION_GATE_REVISION,
) -> MigrationCompatibilityReport:
    inspector = inspect(connection)
    table_names = tuple(sorted(inspector.get_table_names()))
    current_revisions = _current_revisions(connection)
    version_length = _alembic_version_length(connection)
    requires_resize = (
        connection.dialect.name in {"mysql", "mariadb"}
        and version_length is not None
        and version_length < ALEMBIC_VERSION_MIN_LENGTH
    )
    has_legacy_alias = any(revision in REVISION_ALIASES for revision in current_revisions)

    script = _alembic_script_directory()
    has_unknown_revision = False
    has_revision_below_gate = False
    for revision in current_revisions:
        if revision in REVISION_ALIASES:
            has_revision_below_gate = True
            continue
        if not _is_revision_at_or_above_gate(script, revision, gate_revision):
            gate_chain = _revision_chain(script, gate_revision)
            if revision in gate_chain:
                has_revision_below_gate = True
            else:
                has_unknown_revision = True

    alembic_version_table_present = "alembic_version" in table_names
    app_tables = set(table_names) & CORE_APP_TABLES
    has_legacy_schema_without_version_table = bool(app_tables) and not alembic_version_table_present
    has_multiple_heads = len(current_revisions) > 1
    runtime_upgrade_allowed = (
        not requires_resize
        and not has_legacy_alias
        and not has_revision_below_gate
        and not has_unknown_revision
        and not has_legacy_schema_without_version_table
        and not has_multiple_heads
    )
    return MigrationCompatibilityReport(
        current_revisions=current_revisions,
        database_tables=table_names,
        alembic_version_table_present=alembic_version_table_present,
        alembic_version_length=version_length,
        requires_version_table_resize=requires_resize,
        has_legacy_revision_alias=has_legacy_alias,
        has_revision_below_gate=has_revision_below_gate,
        has_unknown_revision=has_unknown_revision,
        has_legacy_schema_without_version_table=has_legacy_schema_without_version_table,
        has_multiple_heads=has_multiple_heads,
        runtime_upgrade_allowed=runtime_upgrade_allowed,
    )


def format_migration_compatibility_report(report: MigrationCompatibilityReport) -> str:
    lines = [
        f"current revisions: {report.current_revision_display}",
        f"alembic_version present: {'yes' if report.alembic_version_table_present else 'no'}",
        f"alembic_version length: {report.alembic_version_length if report.alembic_version_length is not None else '<missing>'}",
        f"runtime gate revision: {RUNTIME_MIGRATION_GATE_REVISION}",
    ]
    if report.has_legacy_schema_without_version_table:
        lines.append("issue: legacy app tables exist without alembic_version")
    if report.requires_version_table_resize:
        lines.append(f"issue: alembic_version.version_num is shorter than {ALEMBIC_VERSION_MIN_LENGTH}")
    if report.has_legacy_revision_alias:
        lines.append("issue: legacy revision alias still present in alembic_version")
    if report.has_revision_below_gate:
        lines.append("issue: current revision is below the runtime migration gate")
    if report.has_unknown_revision:
        lines.append("issue: current revision is unknown or outside the expected revision chain")
    if report.has_multiple_heads:
        lines.append("issue: multiple alembic heads detected")
    return "\n".join(lines)


def format_runtime_migration_gate_error(report: MigrationCompatibilityReport) -> str:
    summary = format_migration_compatibility_report(report)
    return (
        "Runtime migration compatibility checks failed.\n"
        f"{summary}\n"
        "Automatic compatibility patching during startup has been disabled.\n"
        f"Run `{OFFLINE_MIGRATION_CHECK_COMMAND}` first. "
        "If it reports legacy version-table issues, rerun it with `--apply-compat-fixes`, "
        "then perform the Alembic upgrade manually before starting the app."
    )


def build_migration_gate_payload(
    report: MigrationCompatibilityReport,
    *,
    source: str,
    outcome: str,
) -> dict[str, object]:
    return {
        "event": "migration_runtime_gate",
        "source": source,
        "outcome": outcome,
        "gate_revision": RUNTIME_MIGRATION_GATE_REVISION,
        "current_revisions": list(report.current_revisions),
        "current_revision_display": report.current_revision_display,
        "issue_codes": list(report.issue_codes),
        "alembic_version_present": report.alembic_version_table_present,
        "alembic_version_length": report.alembic_version_length,
        "runtime_upgrade_allowed": report.runtime_upgrade_allowed,
    }


def log_migration_gate_report(
    report: MigrationCompatibilityReport,
    *,
    source: str,
    outcome: str,
) -> None:
    payload = build_migration_gate_payload(report, source=source, outcome=outcome)
    message = json.dumps(payload, ensure_ascii=True, sort_keys=True)
    if outcome == "blocked":
        logger.error(message)
    elif outcome == "compat_fixes_applied":
        logger.warning(message)
    else:
        logger.info(message)


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
    if current_length is not None and current_length >= ALEMBIC_VERSION_MIN_LENGTH:
        return

    connection.execute(
        text(f"ALTER TABLE alembic_version MODIFY COLUMN version_num VARCHAR({ALEMBIC_VERSION_MIN_LENGTH}) NOT NULL")
    )


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


def apply_runtime_compatibility_fixes(connection: Connection) -> MigrationCompatibilityReport:
    _prepare_alembic_version_table(connection)
    report = inspect_migration_compatibility(connection)
    log_migration_gate_report(report, source="offline_check", outcome="compat_fixes_applied")
    return report


def verify_runtime_migration_gate(*, source: str = "runtime_startup") -> MigrationCompatibilityReport:
    engine = create_engine(settings.database_url)
    try:
        with engine.begin() as connection:
            report = inspect_migration_compatibility(connection)
            if not report.runtime_upgrade_allowed:
                log_migration_gate_report(report, source=source, outcome="blocked")
                raise RuntimeMigrationGateError(format_runtime_migration_gate_error(report))
            log_migration_gate_report(report, source=source, outcome="passed")
            return report
    finally:
        engine.dispose()


def upgrade_database() -> None:
    verify_runtime_migration_gate(source="runtime_startup")
    command.upgrade(_alembic_config(), "head")
