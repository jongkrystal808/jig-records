from __future__ import annotations

import argparse

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.core.migrations import upgrade_database
from backend.app.services.auth_service import AuthService


def bootstrap_application(*, run_migrations: bool = True, ensure_default_user: bool = True) -> None:
    settings.validate_runtime_safety()

    if run_migrations:
        upgrade_database()

    if not ensure_default_user:
        return

    db = SessionLocal()
    try:
        AuthService(db).ensure_default_user()
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap the Jig Record backend runtime")
    parser.add_argument("--skip-migrations", action="store_true", help="Do not run Alembic migrations")
    parser.add_argument("--skip-default-user", action="store_true", help="Do not ensure the default admin user exists")
    args = parser.parse_args()

    bootstrap_application(
        run_migrations=not args.skip_migrations,
        ensure_default_user=not args.skip_default_user,
    )


if __name__ == "__main__":
    main()
