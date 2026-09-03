import os

import uvicorn

from backend.app.bootstrap import bootstrap_application
from backend.app.core.config import settings


FALSE_ENV_VALUES = {"0", "false", "no", "off"}
TRUE_ENV_VALUES = {"1", "true", "yes", "on"}


def should_bootstrap_before_run() -> bool:
    return os.getenv("BOOTSTRAP_BEFORE_RUN", "1").strip().lower() not in FALSE_ENV_VALUES


def should_reload_server() -> bool:
    configured = os.getenv("UVICORN_RELOAD")
    if configured is None:
        return settings.environment == "development"
    normalized = configured.strip().lower()
    if normalized in TRUE_ENV_VALUES:
        return True
    if normalized in FALSE_ENV_VALUES:
        return False
    raise RuntimeError("UVICORN_RELOAD must be a boolean value")


def uvicorn_worker_count(*, reload_enabled: bool) -> int:
    if reload_enabled:
        return 1
    configured = os.getenv("UVICORN_WORKERS", "1").strip()
    try:
        workers = int(configured)
    except ValueError as exc:
        raise RuntimeError("UVICORN_WORKERS must be a positive integer") from exc
    if workers < 1:
        raise RuntimeError("UVICORN_WORKERS must be a positive integer")
    return workers


if __name__ == "__main__":
    if should_bootstrap_before_run():
        bootstrap_application()
    reload_enabled = should_reload_server()
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=reload_enabled,
        workers=uvicorn_worker_count(reload_enabled=reload_enabled),
    )
