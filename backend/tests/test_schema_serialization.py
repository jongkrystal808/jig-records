from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.schemas.common import TimestampedResponse
from backend.app.schemas.inventory import (
    StockTransactionItemRead,
    StockTransactionPageRead,
    StockTransactionRead,
)


def test_timestamped_response_serializes_datetimes_as_dates():
    response = TimestampedResponse(
        created_at=datetime(2026, 8, 4, 8, 30, tzinfo=timezone.utc),
        updated_at=datetime(2026, 8, 5, 17, 45, tzinfo=timezone.utc),
    )

    assert response.model_dump(mode="json") == {
        "created_at": "2026-08-04",
        "updated_at": "2026-08-05",
    }


def test_fastapi_response_model_keeps_date_only_contract():
    app = FastAPI()

    @app.get("/timestamp", response_model=TimestampedResponse)
    def get_timestamp():
        return {
            "created_at": datetime(2026, 8, 4, 8, 30, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 8, 5, 17, 45, tzinfo=timezone.utc),
        }

    response = TestClient(app).get("/timestamp")

    assert response.status_code == 200
    assert response.json() == {
        "created_at": "2026-08-04",
        "updated_at": "2026-08-05",
    }


def test_nested_inventory_response_keeps_date_only_contract():
    transaction = StockTransactionRead(
        id=7,
        customer_id=2,
        transaction_type="receipt",
        transaction_no="R-20260804-001",
        occurred_at=datetime(2026, 8, 4, 9, 15, tzinfo=timezone.utc),
        created_by="admin",
        note=None,
        created_at=datetime(2026, 8, 4, 9, 16, tzinfo=timezone.utc),
        items=[
            StockTransactionItemRead(
                fixture_id=11,
                fixture_code="FX-011",
                fixture_name="測試治具",
                ownership_type="customer_supplied",
                identifier="0001",
                quantity=1,
                note=None,
            )
        ],
    )

    payload = StockTransactionPageRead(
        items=[transaction], page=1, page_size=20, total=1
    ).model_dump(mode="json")

    assert payload["items"][0]["occurred_at"] == "2026-08-04"
    assert payload["items"][0]["created_at"] == "2026-08-04"


def test_schema_imports_do_not_emit_pydantic_deprecation_warnings():
    repository_root = Path(__file__).resolve().parents[2]
    command = """
import warnings
from pydantic.warnings import PydanticDeprecatedSince20
warnings.simplefilter('error', PydanticDeprecatedSince20)
import backend.app.schemas.audit
import backend.app.schemas.auth
import backend.app.schemas.inventory
import backend.app.schemas.master
import backend.app.schemas.production
import backend.app.schemas.search
"""

    result = subprocess.run(
        [sys.executable, "-c", command],
        cwd=repository_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
