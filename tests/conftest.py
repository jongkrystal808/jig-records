from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def app_client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("AUTH_TOKEN_TTL_SECONDS", "3600")
    monkeypatch.setenv("FIXTURE_IMAGE_DIR", str(tmp_path / "fixture-images"))

    for module_name in list(sys.modules):
        if module_name == "backend" or module_name.startswith("backend."):
            del sys.modules[module_name]

    bootstrap_module = importlib.import_module("backend.app.bootstrap")
    bootstrap_module.bootstrap_application()
    app_module = importlib.import_module("backend.app.main")
    with TestClient(app_module.app) as client:
        yield client
