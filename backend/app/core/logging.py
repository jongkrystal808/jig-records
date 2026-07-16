from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from backend.app.core.config import settings

APP_LOGGER_NAME = "backend.app"
AUDIT_LOGGER_NAME = "backend.app.audit"


def get_audit_log_path() -> Path:
    return Path(settings.log_dir) / settings.audit_log_filename


def _has_handler_for_path(logger: logging.Logger, target_path: Path) -> bool:
    resolved_target = target_path.resolve()
    for handler in logger.handlers:
        if isinstance(handler, RotatingFileHandler) and Path(handler.baseFilename).resolve() == resolved_target:
            return True
    return False


def get_audit_logger() -> logging.Logger:
    logger = logging.getLogger(AUDIT_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    audit_log_path = get_audit_log_path()
    audit_log_path.parent.mkdir(parents=True, exist_ok=True)
    if not _has_handler_for_path(logger, audit_log_path):
        handler = RotatingFileHandler(
            audit_log_path,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    return logger


def write_audit_log(payload: dict) -> None:
    get_audit_logger().info(json.dumps(payload, ensure_ascii=False, default=str))


def setup_logging() -> None:
    app_logger = logging.getLogger(APP_LOGGER_NAME)
    app_logger.setLevel(logging.INFO)

    root_logger = logging.getLogger()
    if root_logger.handlers:
        get_audit_logger()
        return

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    get_audit_logger()
