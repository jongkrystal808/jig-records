from __future__ import annotations

import logging

APP_LOGGER_NAME = "backend.app"


def setup_logging() -> None:
    app_logger = logging.getLogger(APP_LOGGER_NAME)
    app_logger.setLevel(logging.INFO)

    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    logging.basicConfig(level=logging.INFO, format="%(message)s")
