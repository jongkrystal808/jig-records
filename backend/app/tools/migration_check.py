from __future__ import annotations

import argparse

from sqlalchemy import create_engine

from backend.app.core.config import settings
from backend.app.core.logging import setup_logging
from backend.app.core.migrations import (
    OFFLINE_MIGRATION_CHECK_COMMAND,
    apply_runtime_compatibility_fixes,
    format_migration_compatibility_report,
    inspect_migration_compatibility,
    log_migration_gate_report,
)


def main() -> None:
    setup_logging()
    parser = argparse.ArgumentParser(
        description="Inspect migration compatibility state without relying on runtime startup patching"
    )
    parser.add_argument(
        "--apply-compat-fixes",
        action="store_true",
        help="Explicitly apply legacy alembic_version compatibility fixes before re-checking",
    )
    args = parser.parse_args()

    engine = create_engine(settings.database_url)
    exit_code = 0
    try:
        with engine.begin() as connection:
            if args.apply_compat_fixes:
                report = apply_runtime_compatibility_fixes(connection)
                print("Applied explicit compatibility fixes.")
            else:
                report = inspect_migration_compatibility(connection)

            log_migration_gate_report(
                report,
                source="offline_check",
                outcome="passed" if report.runtime_upgrade_allowed else "blocked",
            )
            print(format_migration_compatibility_report(report))
            if report.runtime_upgrade_allowed:
                print("status: runtime migration gate passed")
            else:
                exit_code = 1
                print("status: runtime migration gate blocked")
                print(f"next: run `{OFFLINE_MIGRATION_CHECK_COMMAND}` or perform manual Alembic upgrade as needed")
    finally:
        engine.dispose()

    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
