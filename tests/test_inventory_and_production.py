from __future__ import annotations

import csv
from datetime import datetime, timezone
from io import StringIO
from unittest.mock import Mock

from sqlalchemy.dialects import mysql

from backend.app.models.inventory import MaterialTransaction
from backend.app.repositories.inventory_repository import InventoryRepository
from backend.app.utils.identifier_rules import normalize_identifier_for_write


def _login(client):
    response = client.post(
        "/api/v2/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    return response.json()["token"]


def _create_assigned_customer(client, headers):
    users = client.get("/api/v2/auth/users", headers=headers)
    assert users.status_code == 200
    admin_user_id = next(row["id"] for row in users.json() if row["username"] == "admin")

    counter = getattr(_create_assigned_customer, "_counter", 0) + 1
    _create_assigned_customer._counter = counter

    response = client.post(
        "/api/v2/master/customers",
        json={
            "code": f"TEST-CUST-{counter:03d}",
            "name": f"Test Customer {counter}",
            "assigned_user_ids": [admin_user_id],
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_form_read_models_are_server_paginated_and_searchable(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = _create_assigned_customer(app_client, headers)

    customer_page = app_client.get(
        "/api/v2/master/customers/page",
        params={"page_size": 50, "keyword": "Test Customer"},
        headers=headers,
    )
    assert customer_page.status_code == 200
    assert customer_page.json()["total"] == 1

    user_page = app_client.get(
        "/api/v2/auth/users/page",
        params={"page_size": 50, "keyword": "admin"},
        headers=headers,
    )
    assert user_page.status_code == 200
    assert user_page.json()["total"] == 1

    fixtures = []
    for index in range(3):
        response = app_client.post(
            "/api/v2/master/fixtures",
            json={"customer_id": customer_id, "code": f"FORM-{index + 1:03d}", "name": f"Form Fixture {index + 1}", "min_stock_qty": 0},
            headers=headers,
        )
        assert response.status_code == 201
        fixtures.append(response.json())

    uploaded = app_client.post(
        f"/api/v2/master/fixtures/{fixtures[1]['id']}/image",
        params={"customer_id": customer_id},
        files={"image": ("fixture.png", b"image", "image/png")},
        headers=headers,
    )
    assert uploaded.status_code == 200

    first_page = app_client.get(
        "/api/v2/master/fixtures/page",
        params={"customer_id": customer_id, "page": 1, "page_size": 2, "keyword": "Form Fixture"},
        headers=headers,
    )
    assert first_page.status_code == 200
    assert first_page.json()["total"] == 3
    assert [row["code"] for row in first_page.json()["items"]] == ["FORM-001", "FORM-002"]

    image_page = app_client.get(
        "/api/v2/master/fixtures/page",
        params={"customer_id": customer_id, "image_status": "with-image"},
        headers=headers,
    )
    assert image_page.status_code == 200
    assert image_page.json()["total"] == 1
    assert image_page.json()["items"][0]["code"] == "FORM-002"

    missing_image_page = app_client.get(
        "/api/v2/master/fixtures/page",
        params={"customer_id": customer_id, "image_status": "missing-image"},
        headers=headers,
    )
    assert missing_image_page.status_code == 200
    assert missing_image_page.json()["total"] == 2
    assert [row["code"] for row in missing_image_page.json()["items"]] == ["FORM-001", "FORM-003"]

    model = app_client.post(
        "/api/v2/master/models",
        json={"customer_id": customer_id, "code": "FORM-MODEL", "name": "Form Model"},
        headers=headers,
    )
    station = app_client.post(
        "/api/v2/master/stations",
        json={"customer_id": customer_id, "code": "FORM-STATION", "name": "Form Station"},
        headers=headers,
    )
    assert model.status_code == 201
    assert station.status_code == 201
    for fixture in fixtures[:2]:
        requirement = app_client.post(
            "/api/v2/production/fixture-requirements",
            json={"customer_id": customer_id, "model_id": model.json()["id"], "station_id": station.json()["id"], "fixture_id": fixture["id"], "required_qty": 2},
            headers=headers,
        )
        assert requirement.status_code == 201

    requirement_page = app_client.get(
        "/api/v2/production/fixture-requirements/page",
        params={"customer_id": customer_id, "page_size": 1, "model_id": model.json()["id"]},
        headers=headers,
    )
    assert requirement_page.status_code == 200
    assert requirement_page.json()["total"] == 2
    assert requirement_page.json()["items"][0]["stock_qty"] == 0

    mapping_page = app_client.get(
        "/api/v2/production/model-stations/page",
        params={"customer_id": customer_id, "keyword": "Form Station"},
        headers=headers,
    )
    assert mapping_page.status_code == 200
    assert mapping_page.json()["total"] == 1
    assert mapping_page.json()["items"][0]["model_code"] == "FORM-MODEL"


def test_form_export_endpoints_apply_existing_filters_in_one_streamed_response(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = _create_assigned_customer(app_client, headers)
    unassigned_customer = app_client.post(
        "/api/v2/master/customers",
        json={
            "code": "FORM-EXPORT-UNASSIGNED",
            "name": "Form Export Unassigned",
            "assigned_user_ids": [],
        },
        headers=headers,
    )
    assert unassigned_customer.status_code == 201
    denied_export = app_client.get(
        "/api/v2/master/form-export",
        params={"entity": "fixture", "customer_id": unassigned_customer.json()["id"]},
        headers=headers,
    )
    assert denied_export.status_code == 403

    fixtures = []
    for suffix in ("A", "B"):
        fixture = app_client.post(
            "/api/v2/master/fixtures",
            json={
                "customer_id": customer_id,
                "code": f"FORM-EXPORT-IMAGE-{suffix}",
                "name": f"Form Export Fixture {suffix}",
                "line_storage_location": f"LINE-{suffix}",
                "min_stock_qty": 2,
            },
            headers=headers,
        )
        assert fixture.status_code == 201
        fixtures.append(fixture.json())

    uploaded = app_client.post(
        f"/api/v2/master/fixtures/{fixtures[0]['id']}/image",
        params={"customer_id": customer_id},
        files={"image": ("fixture.png", b"image", "image/png")},
        headers=headers,
    )
    assert uploaded.status_code == 200

    image_export = app_client.get(
        "/api/v2/master/form-export",
        params={
            "entity": "fixture-images",
            "customer_id": customer_id,
            "keyword": "FORM-EXPORT-IMAGE",
            "image_status": "missing-image",
        },
        headers=headers,
    )
    assert image_export.status_code == 200
    assert "content-length" not in image_export.headers
    image_rows = list(csv.DictReader(StringIO(image_export.text.lstrip("\ufeff"))))
    assert image_rows == [
        {
            "治具編號": "FORM-EXPORT-IMAGE-B",
            "治具名稱": "Form Export Fixture B",
            "圖片狀態": "尚無圖片",
        }
    ]

    fixture_export = app_client.get(
        "/api/v2/master/form-export",
        params={
            "entity": "fixture",
            "customer_id": customer_id,
            "keyword": "IMAGE-A",
            "status_filter": "active",
        },
        headers=headers,
    )
    assert fixture_export.status_code == 200
    fixture_rows = list(csv.DictReader(StringIO(fixture_export.text.lstrip("\ufeff"))))
    assert len(fixture_rows) == 1
    assert fixture_rows[0]["治具編號"] == "FORM-EXPORT-IMAGE-A"
    assert fixture_rows[0]["最低水位"] == "2"

    customer_export = app_client.get(
        "/api/v2/master/form-export",
        params={"entity": "customer", "keyword": "FORM-EXPORT"},
        headers=headers,
    )
    assert customer_export.status_code == 200
    customer_rows = list(csv.DictReader(StringIO(customer_export.text.lstrip("\ufeff"))))
    assert customer_rows == []
    assigned_customer_export = app_client.get(
        "/api/v2/master/form-export",
        params={"entity": "customer", "keyword": "TEST-CUST"},
        headers=headers,
    )
    assert assigned_customer_export.status_code == 200
    assigned_customer_rows = list(
        csv.DictReader(StringIO(assigned_customer_export.text.lstrip("\ufeff")))
    )
    assert len(assigned_customer_rows) == 1
    assert assigned_customer_rows[0]["編號"].startswith("TEST-CUST-")
    assert assigned_customer_rows[0]["狀態"] == "—"

    user_export = app_client.get(
        "/api/v2/auth/users/form-export",
        params={"keyword": "admin", "status_filter": "active"},
        headers=headers,
    )
    assert user_export.status_code == 200
    user_rows = list(csv.DictReader(StringIO(user_export.text.lstrip("\ufeff"))))
    assert [(row["帳號"], row["狀態"]) for row in user_rows] == [("admin", "啟用")]

    model = app_client.post(
        "/api/v2/master/models",
        json={"customer_id": customer_id, "code": "FORM-EXPORT-MODEL", "name": "Export Model"},
        headers=headers,
    ).json()
    station = app_client.post(
        "/api/v2/master/stations",
        json={"customer_id": customer_id, "code": "FORM-EXPORT-STATION", "name": "Export Station"},
        headers=headers,
    ).json()
    mapping = app_client.post(
        "/api/v2/production/model-stations",
        json={"customer_id": customer_id, "model_id": model["id"], "station_id": station["id"]},
        headers=headers,
    )
    assert mapping.status_code == 201
    requirement = app_client.post(
        "/api/v2/production/fixture-requirements",
        json={
            "customer_id": customer_id,
            "model_id": model["id"],
            "station_id": station["id"],
            "fixture_id": fixtures[0]["id"],
            "required_qty": 2,
        },
        headers=headers,
    )
    assert requirement.status_code == 201

    mapping_export = app_client.get(
        "/api/v2/production/form-export",
        params={
            "entity": "mappings",
            "customer_id": customer_id,
            "station_id": station["id"],
            "keyword": "EXPORT-MODEL",
        },
        headers=headers,
    )
    assert mapping_export.status_code == 200
    mapping_rows = list(csv.DictReader(StringIO(mapping_export.text.lstrip("\ufeff"))))
    assert [(row["機種編號"], row["站點編號"]) for row in mapping_rows] == [
        ("FORM-EXPORT-MODEL", "FORM-EXPORT-STATION")
    ]

    requirement_export = app_client.get(
        "/api/v2/production/form-export",
        params={
            "entity": "requirements",
            "customer_id": customer_id,
            "model_id": model["id"],
            "keyword": "IMAGE-A",
        },
        headers=headers,
    )
    assert requirement_export.status_code == 200
    requirement_rows = list(csv.DictReader(StringIO(requirement_export.text.lstrip("\ufeff"))))
    assert [(row["治具"], row["每站需求"], row["可開站"]) for row in requirement_rows] == [
        ("FORM-EXPORT-IMAGE-A", "2", "0")
    ]


def test_customer_master_page_uses_stable_server_pagination(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_ids = [_create_assigned_customer(app_client, headers) for _ in range(3)]

    first_page = app_client.get(
        "/api/v2/master/customers/page",
        params={"page": 1, "page_size": 2, "keyword": "Test Customer"},
        headers=headers,
    )
    second_page = app_client.get(
        "/api/v2/master/customers/page",
        params={"page": 2, "page_size": 2, "keyword": "Test Customer"},
        headers=headers,
    )

    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert first_page.json()["total"] == 3
    assert second_page.json()["total"] == 3
    returned_ids = [row["id"] for row in first_page.json()["items"] + second_page.json()["items"]]
    assert returned_ids == customer_ids


def test_production_import_previews_conflicts_before_explicit_replacement(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = _create_assigned_customer(app_client, headers)

    model = app_client.post(
        "/api/v2/master/models",
        json={"customer_id": customer_id, "code": "PREVIEW-MODEL", "name": "Preview Model"},
        headers=headers,
    ).json()
    station = app_client.post(
        "/api/v2/master/stations",
        json={"customer_id": customer_id, "code": "PREVIEW-ST-01", "name": "Preview Station 1"},
        headers=headers,
    ).json()
    second_station = app_client.post(
        "/api/v2/master/stations",
        json={"customer_id": customer_id, "code": "PREVIEW-ST-02", "name": "Preview Station 2"},
        headers=headers,
    ).json()
    fixture = app_client.post(
        "/api/v2/master/fixtures",
        json={"customer_id": customer_id, "code": "PREVIEW-FIX", "name": "Preview Fixture", "min_stock_qty": 0},
        headers=headers,
    ).json()

    mapping = app_client.post(
        "/api/v2/production/model-stations",
        json={"customer_id": customer_id, "model_id": model["id"], "station_id": station["id"]},
        headers=headers,
    )
    assert mapping.status_code == 201
    requirement = app_client.post(
        "/api/v2/production/fixture-requirements",
        json={
            "customer_id": customer_id,
            "model_id": model["id"],
            "station_id": station["id"],
            "fixture_id": fixture["id"],
            "required_qty": 2,
        },
        headers=headers,
    )
    assert requirement.status_code == 201

    mapping_csv = (
        "model_code,station_code\n"
        "PREVIEW-MODEL,PREVIEW-ST-01\n"
        "PREVIEW-MODEL,PREVIEW-ST-02"
    )
    mapping_preview = app_client.post(
        "/api/v2/production/model-stations/import/preview",
        params={"customer_id": customer_id},
        json={"filename": "mapping.csv", "content": mapping_csv},
        headers=headers,
    )
    assert mapping_preview.status_code == 200
    assert mapping_preview.json()["unchanged_count"] == 1
    assert mapping_preview.json()["new_count"] == 1

    mapping_import = app_client.post(
        "/api/v2/production/model-stations/import",
        params={"customer_id": customer_id},
        json={"filename": "mapping.csv", "content": mapping_csv, "overwrite_existing": False},
        headers=headers,
    )
    assert mapping_import.status_code == 200
    assert mapping_import.json() == {
        "imported_count": 1,
        "created_count": 1,
        "updated_count": 0,
        "skipped_count": 1,
    }

    requirement_csv = (
        "model_code,station_code,fixture_code,required_qty\n"
        "PREVIEW-MODEL,PREVIEW-ST-01,PREVIEW-FIX,5"
    )
    requirement_preview = app_client.post(
        "/api/v2/production/fixture-requirements/import/preview",
        params={"customer_id": customer_id},
        json={"filename": "requirements.csv", "content": requirement_csv},
        headers=headers,
    )
    assert requirement_preview.status_code == 200
    preview_row = requirement_preview.json()["rows"][0]
    assert requirement_preview.json()["conflict_count"] == 1
    assert preview_row["existing_required_qty"] == 2
    assert preview_row["incoming_required_qty"] == 5

    safe_import = app_client.post(
        "/api/v2/production/fixture-requirements/import",
        params={"customer_id": customer_id},
        json={"filename": "requirements.csv", "content": requirement_csv, "overwrite_existing": False},
        headers=headers,
    )
    assert safe_import.status_code == 200
    assert safe_import.json()["updated_count"] == 0
    assert safe_import.json()["skipped_count"] == 1

    unchanged_page = app_client.get(
        "/api/v2/production/fixture-requirements/page",
        params={"customer_id": customer_id, "model_id": model["id"], "station_id": station["id"]},
        headers=headers,
    )
    assert unchanged_page.json()["items"][0]["required_qty"] == 2

    replaced = app_client.post(
        "/api/v2/production/fixture-requirements/import",
        params={"customer_id": customer_id},
        json={"filename": "requirements.csv", "content": requirement_csv, "overwrite_existing": True},
        headers=headers,
    )
    assert replaced.status_code == 200
    assert replaced.json()["updated_count"] == 1
    assert replaced.json()["created_count"] == 0

    replaced_page = app_client.get(
        "/api/v2/production/fixture-requirements/page",
        params={"customer_id": customer_id, "model_id": model["id"], "station_id": station["id"]},
        headers=headers,
    )
    assert replaced_page.json()["items"][0]["required_qty"] == 5
    assert second_station["id"] != station["id"]


def test_fixture_images_are_customer_scoped_and_deleted_with_fixture(app_client, tmp_path):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_a = _create_assigned_customer(app_client, headers)
    customer_b = _create_assigned_customer(app_client, headers)

    fixture_ids = []
    for customer_id, name in ((customer_a, "Fixture A"), (customer_b, "Fixture B")):
        response = app_client.post(
            "/api/v2/master/fixtures",
            json={
                "customer_id": customer_id,
                "code": "SHARED-CODE",
                "name": name,
                "min_stock_qty": 1,
            },
            headers=headers,
        )
        assert response.status_code == 201
        fixture_ids.append(response.json()["id"])

    for fixture_id, customer_id, content in (
        (fixture_ids[0], customer_a, b"customer-a-image"),
        (fixture_ids[1], customer_b, b"customer-b-image"),
    ):
        response = app_client.post(
            f"/api/v2/master/fixtures/{fixture_id}/image",
            params={"customer_id": customer_id},
            files={"image": ("fixture.png", content, "image/png")},
            headers=headers,
        )
        assert response.status_code == 200

    missing_scope = app_client.get("/api/v2/master/fixtures/SHARED-CODE/image", headers=headers)
    assert missing_scope.status_code == 422

    image_a = app_client.get(
        "/api/v2/master/fixtures/SHARED-CODE/image",
        params={"customer_id": customer_a},
        headers=headers,
    )
    image_b = app_client.get(
        "/api/v2/master/fixtures/SHARED-CODE/image",
        params={"customer_id": customer_b},
        headers=headers,
    )
    assert image_a.status_code == 200
    assert image_a.content == b"customer-a-image"
    assert image_b.status_code == 200
    assert image_b.content == b"customer-b-image"

    image_root = tmp_path / "fixture-images"
    assert (image_root / str(customer_a) / "SHARED-CODE.png").read_bytes() == b"customer-a-image"
    assert (image_root / str(customer_b) / "SHARED-CODE.png").read_bytes() == b"customer-b-image"

    deleted = app_client.delete(
        f"/api/v2/master/fixtures/{fixture_ids[0]}",
        params={"customer_id": customer_a, "delete_transactions": False},
        headers=headers,
    )
    assert deleted.status_code == 200
    assert not (image_root / str(customer_a) / "SHARED-CODE.png").exists()
    assert (image_root / str(customer_b) / "SHARED-CODE.png").is_file()


def test_inventory_capacity_and_search_flow(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}

    customer_id = _create_assigned_customer(app_client, headers)

    fixture = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_id,
            "code": "T-001",
            "name": "Test Fixture",
            "storage_location": "A-01",
            "min_stock_qty": 2,
            "description": "pytest",
        },
        headers=headers,
    )
    assert fixture.status_code == 201
    fixture_id = fixture.json()["id"]

    station = app_client.post(
        "/api/v2/master/stations",
        json={"customer_id": customer_id, "code": "ST-01", "name": "Station 01"},
        headers=headers,
    )
    assert station.status_code == 201
    station_id = station.json()["id"]

    model = app_client.post(
        "/api/v2/master/models",
        json={"customer_id": customer_id, "code": "M-001", "name": "Model 001"},
        headers=headers,
    )
    assert model.status_code == 201
    model_id = model.json()["id"]

    mapping = app_client.post(
        "/api/v2/production/model-stations",
        json={"customer_id": customer_id, "model_id": model_id, "station_id": station_id},
        headers=headers,
    )
    assert mapping.status_code == 201

    requirement = app_client.post(
        "/api/v2/production/fixture-requirements",
        json={"customer_id": customer_id, "model_id": model_id, "station_id": station_id, "fixture_id": fixture_id, "required_qty": 2},
        headers=headers,
    )
    assert requirement.status_code == 201

    receipt = app_client.post(
        "/api/v2/inventory/receipts",
        json={
            "customer_id": customer_id,
            "created_by": "System Admin",
            "transaction_no": "INV-FLOW-001",
            "items": [
                {
                    "fixture_id": fixture_id,
                    "ownership_type": "self_purchased",
                    "identifier": "2606",
                    "quantity": 6,
                }
            ],
        },
        headers=headers,
    )
    assert receipt.status_code == 204

    stock = app_client.get("/api/v2/inventory/stock", params={"customer_id": customer_id}, headers=headers)
    assert stock.status_code == 200
    assert stock.json()[0]["stock_qty"] == 6

    capacity = app_client.get(
        f"/api/v2/production/capacity/stations/{station_id}",
        params={"model_id": model_id, "customer_id": customer_id},
        headers=headers,
    )
    assert capacity.status_code == 200
    payload = capacity.json()
    assert payload["max_open_station_count"] == 3

    search = app_client.get("/api/v2/search/global", params={"q": "T-001", "customer_id": customer_id}, headers=headers)
    assert search.status_code == 200
    payload = search.json()
    assert payload["items"][0]["entity_type"] == "fixture"
    assert payload["total"] >= 1


def test_inventory_actor_is_bound_to_authenticated_session_for_api_and_csv(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = _create_assigned_customer(app_client, headers)
    users = app_client.get("/api/v2/auth/users", headers=headers)
    assert users.status_code == 200
    admin_user_id = next(row["id"] for row in users.json() if row["username"] == "admin")

    fixture = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_id,
            "code": "ACTOR-001",
            "name": "Actor Fixture",
            "min_stock_qty": 0,
        },
        headers=headers,
    )
    assert fixture.status_code == 201
    fixture_id = fixture.json()["id"]

    receipt = app_client.post(
        "/api/v2/inventory/receipts",
        json={
            "customer_id": customer_id,
            "created_by": "spoofed-user",
            "transaction_no": "ACTOR-API-001",
            "items": [
                {
                    "fixture_id": fixture_id,
                    "ownership_type": "self_purchased",
                    "identifier": "ACTOR-API",
                    "quantity": 2,
                }
            ],
        },
        headers=headers,
    )
    assert receipt.status_code == 204

    csv_content = (
        "transaction_type,transaction_no,fixture_code,ownership_type,identifier,quantity,created_by,occurred_at,note\n"
        "receipt,ACTOR-CSV-001,ACTOR-001,self_purchased,ACTOR-CSV,1,csv-spoofed-user,,\n"
    )
    imported = app_client.post(
        "/api/v2/inventory/transactions/import",
        params={"customer_id": customer_id, "operator_name": "query-spoofed-user"},
        json={"content": csv_content},
        headers=headers,
    )
    assert imported.status_code == 200
    assert imported.json() == {"imported_count": 1}

    transactions = app_client.get(
        "/api/v2/inventory/transactions",
        params={"customer_id": customer_id, "limit": 10},
        headers=headers,
    )
    assert transactions.status_code == 200
    actor_rows = {
        row["transaction_no"]: (row["actor_user_id"], row["created_by"])
        for row in transactions.json()
        if row["transaction_no"] in {"ACTOR-API-001", "ACTOR-CSV-001"}
    }
    assert actor_rows == {
        "ACTOR-API-001": (admin_user_id, "System Admin"),
        "ACTOR-CSV-001": (admin_user_id, "System Admin"),
    }


def test_fixture_reenable_recomputes_low_stock_alert(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = _create_assigned_customer(app_client, headers)

    fixture = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_id,
            "code": "ALERT-001",
            "name": "Alert Fixture",
            "storage_location": "RACK-ALERT",
            "min_stock_qty": 0,
        },
        headers=headers,
    )
    assert fixture.status_code == 201
    fixture_id = fixture.json()["id"]

    receipt = app_client.post(
        "/api/v2/inventory/receipts",
        json={
            "customer_id": customer_id,
            "created_by": "System Admin",
            "transaction_no": "ALERT-TX-001",
            "items": [
                {
                    "fixture_id": fixture_id,
                    "ownership_type": "self_purchased",
                    "identifier": "9001",
                    "quantity": 1,
                }
            ],
        },
        headers=headers,
    )
    assert receipt.status_code == 204

    disable_fixture = app_client.put(
        f"/api/v2/master/fixtures/{fixture_id}",
        json={
            "customer_id": customer_id,
            "code": "ALERT-001",
            "name": "Alert Fixture",
            "storage_location": "RACK-ALERT",
            "min_stock_qty": 2,
            "description": None,
            "is_active": False,
        },
        headers=headers,
    )
    assert disable_fixture.status_code == 200

    inactive_alerts = app_client.get(
        "/api/v2/inventory/alerts",
        params={"customer_id": customer_id},
        headers=headers,
    )
    assert inactive_alerts.status_code == 200
    assert inactive_alerts.json() == []

    enable_fixture = app_client.put(
        f"/api/v2/master/fixtures/{fixture_id}",
        json={
            "customer_id": customer_id,
            "code": "ALERT-001",
            "name": "Alert Fixture",
            "storage_location": "RACK-ALERT",
            "min_stock_qty": 2,
            "description": None,
            "is_active": True,
        },
        headers=headers,
    )
    assert enable_fixture.status_code == 200

    alerts = app_client.get(
        "/api/v2/inventory/alerts",
        params={"customer_id": customer_id},
        headers=headers,
    )
    assert alerts.status_code == 200
    assert alerts.json() == [
        {
            "fixture_id": fixture_id,
            "fixture_code": "ALERT-001",
            "fixture_name": "Alert Fixture",
            "stock_qty": 1,
            "customer_supplied_qty": 0,
            "self_purchased_qty": 1,
            "min_stock_qty": 2,
            "stock_status": "low_stock",
        }
    ]

    search = app_client.get(
        "/api/v2/search/global",
        params={"q": "ALERT-001", "customer_id": customer_id, "entity_type": "fixture"},
        headers=headers,
    )
    assert search.status_code == 200
    assert search.json()["items"][0]["stock_status"] == "low_stock"


def test_search_global_paginates_and_prioritizes_active_exact_matches(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = _create_assigned_customer(app_client, headers)

    active_fixture = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_id,
            "code": "S-001",
            "name": "Search Fixture Active",
            "storage_location": "RACK-A",
            "min_stock_qty": 1,
        },
        headers=headers,
    )
    assert active_fixture.status_code == 201

    inactive_fixture = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_id,
            "code": "S-002",
            "name": "Search Fixture Inactive",
            "storage_location": "RACK-B",
            "min_stock_qty": 1,
        },
        headers=headers,
    )
    assert inactive_fixture.status_code == 201
    inactive_fixture_id = inactive_fixture.json()["id"]

    update_inactive = app_client.put(
        f"/api/v2/master/fixtures/{inactive_fixture_id}",
        json={
            "customer_id": customer_id,
            "code": "S-002",
            "name": "Search Fixture Inactive",
            "storage_location": "RACK-B",
            "min_stock_qty": 1,
            "description": None,
            "is_active": False,
        },
        headers=headers,
    )
    assert update_inactive.status_code == 200

    page_one = app_client.get(
        "/api/v2/search/global",
        params={"q": "S-00", "customer_id": customer_id, "entity_type": "fixture", "page": 1, "page_size": 1},
        headers=headers,
    )
    assert page_one.status_code == 200
    payload_one = page_one.json()
    assert payload_one["total"] == 2
    assert payload_one["has_more"] is True
    assert len(payload_one["items"]) == 1
    assert payload_one["items"][0]["title"] == "S-001"
    assert payload_one["items"][0]["is_active"] is True

    page_two = app_client.get(
        "/api/v2/search/global",
        params={"q": "S-00", "customer_id": customer_id, "entity_type": "fixture", "page": 2, "page_size": 1},
        headers=headers,
    )
    assert page_two.status_code == 200
    payload_two = page_two.json()
    assert payload_two["has_more"] is False
    assert payload_two["items"][0]["title"] == "S-002"
    assert payload_two["items"][0]["is_active"] is False


def test_search_fixture_overview_returns_customer_scoped_stock_list(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = _create_assigned_customer(app_client, headers)

    first_fixture = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_id,
            "code": "OV-001",
            "name": "Overview Fixture A",
            "line_storage_location": "LINE-A",
            "department_storage_location": "DEPT-1",
            "min_stock_qty": 1,
        },
        headers=headers,
    )
    assert first_fixture.status_code == 201
    second_fixture = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_id,
            "code": "OV-002",
            "name": "Overview Fixture B",
            "min_stock_qty": 1,
        },
        headers=headers,
    )
    assert second_fixture.status_code == 201

    receipt = app_client.post(
        "/api/v2/inventory/receipts",
        json={
            "customer_id": customer_id,
            "created_by": "System Admin",
            "transaction_no": "OVERVIEW-001",
            "items": [
                {
                    "fixture_id": first_fixture.json()["id"],
                    "ownership_type": "self_purchased",
                    "identifier": "2601",
                    "quantity": 3,
                }
            ],
        },
        headers=headers,
    )
    assert receipt.status_code == 204

    page_one = app_client.get(
        "/api/v2/search/fixtures/overview",
        params={"customer_id": customer_id, "page": 1, "page_size": 1},
        headers=headers,
    )
    assert page_one.status_code == 200
    payload = page_one.json()
    assert payload["total"] == 2
    assert payload["has_more"] is True
    assert payload["items"] == [
        {
            "entity_type": "fixture",
            "title": "OV-001",
            "subtitle": "Overview Fixture A",
            "reference_id": first_fixture.json()["id"],
            "is_active": True,
            "stock_qty": 3,
            "stock_status": "normal",
            "location_code": "LINE-A / DEPT-1",
            "matched_identifier": None,
        }
    ]

    page_two = app_client.get(
        "/api/v2/search/fixtures/overview",
        params={"customer_id": customer_id, "page": 2, "page_size": 1},
        headers=headers,
    )
    assert page_two.status_code == 200
    assert page_two.json()["items"][0]["title"] == "OV-002"
    assert page_two.json()["has_more"] is False


def test_search_global_matches_fixture_and_model_codes_without_separators(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = _create_assigned_customer(app_client, headers)

    fixture = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_id,
            "code": "FX-100-A",
            "name": "Separator Fixture",
            "storage_location": "RACK-C",
            "min_stock_qty": 1,
        },
        headers=headers,
    )
    assert fixture.status_code == 201

    model = app_client.post(
        "/api/v2/master/models",
        json={"customer_id": customer_id, "code": "MD-200-X", "name": "Separator Model"},
        headers=headers,
    )
    assert model.status_code == 201

    fixture_search = app_client.get(
        "/api/v2/search/global",
        params={"q": "FX100A", "customer_id": customer_id, "entity_type": "fixture"},
        headers=headers,
    )
    assert fixture_search.status_code == 200
    fixture_payload = fixture_search.json()
    assert fixture_payload["total"] >= 1
    assert fixture_payload["items"][0]["title"] == "FX-100-A"

    model_search = app_client.get(
        "/api/v2/search/global",
        params={"q": "MD200X", "customer_id": customer_id, "entity_type": "model"},
        headers=headers,
    )
    assert model_search.status_code == 200
    model_payload = model_search.json()
    assert model_payload["total"] >= 1
    assert model_payload["items"][0]["title"] == "MD-200-X"


def test_search_fixture_identifier_mode_excludes_unrelated_fuzzy_matches(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = _create_assigned_customer(app_client, headers)

    matched_fixture = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_id,
            "code": "IDENT-001",
            "name": "Identifier Matched Fixture",
            "storage_location": "RACK-IDENT",
            "min_stock_qty": 1,
        },
        headers=headers,
    )
    assert matched_fixture.status_code == 201
    matched_fixture_id = matched_fixture.json()["id"]

    fuzzy_fixture = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_id,
            "code": "IDENT-002",
            "name": "Spare C-0003-0002 Fixture",
            "storage_location": "RACK-SPARE",
            "min_stock_qty": 1,
        },
        headers=headers,
    )
    assert fuzzy_fixture.status_code == 201
    fuzzy_fixture_id = fuzzy_fixture.json()["id"]

    receipt = app_client.post(
        "/api/v2/inventory/receipts",
        json={
            "customer_id": customer_id,
            "created_by": "System Admin",
            "transaction_no": "IDENT-SEARCH-001",
            "items": [
                {
                    "fixture_id": matched_fixture_id,
                    "ownership_type": "self_purchased",
                    "identifier": "C-0003-0002",
                    "quantity": 1,
                },
                {
                    "fixture_id": matched_fixture_id,
                    "ownership_type": "self_purchased",
                    "identifier": "OTHER-IDENTIFIER",
                    "quantity": 2,
                },
            ],
        },
        headers=headers,
    )
    assert receipt.status_code == 204

    fixture_response = app_client.get(
        "/api/v2/search/global",
        params={
            "q": "c-0003-0002",
            "customer_id": customer_id,
            "entity_type": "fixture",
        },
        headers=headers,
    )
    assert fixture_response.status_code == 200
    fixture_payload = fixture_response.json()
    assert [item["reference_id"] for item in fixture_payload["items"]] == [fuzzy_fixture_id]
    assert fixture_payload["items"][0]["matched_identifier"] is None

    response = app_client.get(
        "/api/v2/search/global",
        params={
            "q": "c-0003-0002",
            "customer_id": customer_id,
            "entity_type": "fixture",
            "fixture_search_mode": "identifier",
        },
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert [item["reference_id"] for item in payload["items"]] == [matched_fixture_id]
    assert payload["items"][0]["title"] == "IDENT-001"
    assert payload["items"][0]["matched_identifier"] == "C-0003-0002"

    context_response = app_client.get(
        f"/api/v2/search/fixtures/{matched_fixture_id}/context",
        params={
            "customer_id": customer_id,
            "identifier": payload["items"][0]["matched_identifier"],
        },
        headers=headers,
    )
    assert context_response.status_code == 200
    context = context_response.json()
    assert context["identifier_rows"] == []
    assert context["related_models"] == []
    assert context["station_rows"] == []
    assert len(context["transactions"]) == 1
    assert [item["identifier"] for item in context["transactions"][0]["items"]] == ["C-0003-0002"]


def test_search_fixture_context_loads_detail_on_demand(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = _create_assigned_customer(app_client, headers)

    fixture = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_id,
            "code": "CTX-001",
            "name": "Context Fixture",
            "storage_location": "CTX-A",
            "min_stock_qty": 2,
        },
        headers=headers,
    )
    assert fixture.status_code == 201
    fixture_id = fixture.json()["id"]

    model = app_client.post(
        "/api/v2/master/models",
        json={"customer_id": customer_id, "code": "CTX-M", "name": "Context Model"},
        headers=headers,
    )
    assert model.status_code == 201
    model_id = model.json()["id"]

    station = app_client.post(
        "/api/v2/master/stations",
        json={"customer_id": customer_id, "code": "CTX-ST", "name": "Context Station"},
        headers=headers,
    )
    assert station.status_code == 201
    station_id = station.json()["id"]

    mapping = app_client.post(
        "/api/v2/production/model-stations",
        json={"customer_id": customer_id, "model_id": model_id, "station_id": station_id},
        headers=headers,
    )
    assert mapping.status_code == 201

    requirement = app_client.post(
        "/api/v2/production/fixture-requirements",
        json={"customer_id": customer_id, "model_id": model_id, "station_id": station_id, "fixture_id": fixture_id, "required_qty": 3},
        headers=headers,
    )
    assert requirement.status_code == 201

    receipt = app_client.post(
        "/api/v2/inventory/receipts",
        json={
            "customer_id": customer_id,
            "created_by": "System Admin",
            "transaction_no": "CTX-TX-001",
            "items": [
                {
                    "fixture_id": fixture_id,
                    "ownership_type": "self_purchased",
                    "identifier": "7",
                    "quantity": 5,
                }
            ],
        },
        headers=headers,
    )
    assert receipt.status_code == 204

    context = app_client.get(
        f"/api/v2/search/fixtures/{fixture_id}/context",
        params={"customer_id": customer_id, "recent_transaction_limit": 8},
        headers=headers,
    )
    assert context.status_code == 200
    payload = context.json()
    assert payload["fixture"]["code"] == "CTX-001"
    assert payload["stock"]["stock_qty"] == 5
    assert payload["identifier_rows"][0]["identifier"] == "0007"
    assert payload["related_models"][0]["code"] == "CTX-M"
    assert payload["station_rows"][0]["station_code"] == "CTX-ST"
    assert payload["transactions"][0]["items"][0]["identifier"] == "0007"


def test_search_fixture_context_filters_shared_transaction_items_to_selected_fixture(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = _create_assigned_customer(app_client, headers)

    fixture_a = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_id,
            "code": "CTX-SHARE-A",
            "name": "Context Shared A",
            "storage_location": "CTX-SA",
            "min_stock_qty": 1,
        },
        headers=headers,
    )
    assert fixture_a.status_code == 201
    fixture_a_id = fixture_a.json()["id"]

    fixture_b = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_id,
            "code": "CTX-SHARE-B",
            "name": "Context Shared B",
            "storage_location": "CTX-SB",
            "min_stock_qty": 1,
        },
        headers=headers,
    )
    assert fixture_b.status_code == 201
    fixture_b_id = fixture_b.json()["id"]

    receipt = app_client.post(
        "/api/v2/inventory/receipts",
        json={
            "customer_id": customer_id,
            "created_by": "System Admin",
            "transaction_no": "CTX-SHARED-20260713",
            "items": [
                {
                    "fixture_id": fixture_a_id,
                    "ownership_type": "self_purchased",
                    "identifier": "2604",
                    "quantity": 24,
                },
                {
                    "fixture_id": fixture_b_id,
                    "ownership_type": "self_purchased",
                    "identifier": "2605",
                    "quantity": 1,
                },
            ],
        },
        headers=headers,
    )
    assert receipt.status_code == 204

    context_a = app_client.get(
        f"/api/v2/search/fixtures/{fixture_a_id}/context",
        params={"customer_id": customer_id, "recent_transaction_limit": 8},
        headers=headers,
    )
    assert context_a.status_code == 200
    payload_a = context_a.json()
    assert payload_a["transactions"][0]["transaction_no"] == "CTX-SHARED-20260713"
    assert payload_a["transactions"][0]["items"] == [
        {
            "fixture_id": fixture_a_id,
            "fixture_code": "CTX-SHARE-A",
            "fixture_name": "Context Shared A",
            "ownership_type": "self_purchased",
            "identifier": "2604",
            "quantity": 24,
            "note": None,
        }
    ]

    context_b = app_client.get(
        f"/api/v2/search/fixtures/{fixture_b_id}/context",
        params={"customer_id": customer_id, "recent_transaction_limit": 8},
        headers=headers,
    )
    assert context_b.status_code == 200
    payload_b = context_b.json()
    assert payload_b["transactions"][0]["transaction_no"] == "CTX-SHARED-20260713"
    assert payload_b["transactions"][0]["items"] == [
        {
            "fixture_id": fixture_b_id,
            "fixture_code": "CTX-SHARE-B",
            "fixture_name": "Context Shared B",
            "ownership_type": "self_purchased",
            "identifier": "2605",
            "quantity": 1,
            "note": None,
        }
    ]


def test_inventory_accepts_legacy_numeric_identifier_longer_than_four_digits(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = _create_assigned_customer(app_client, headers)

    fixture = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_id,
            "code": "T-ERR-001",
            "name": "Validation Fixture",
            "storage_location": "A-01",
            "min_stock_qty": 1,
        },
        headers=headers,
    )
    assert fixture.status_code == 201
    fixture_id = fixture.json()["id"]

    response = app_client.post(
        "/api/v2/inventory/receipts",
        json={
            "customer_id": customer_id,
            "created_by": "System Admin",
            "transaction_no": "LEGACY-ID-001",
            "items": [
                {
                    "fixture_id": fixture_id,
                    "ownership_type": "self_purchased",
                    "identifier": "12345",
                    "quantity": 1,
                }
            ],
        },
        headers=headers,
    )

    assert response.status_code == 204

    transactions = app_client.get(
        "/api/v2/inventory/transactions",
        params={"limit": 2000, "customer_id": customer_id, "identifier": "12345"},
        headers=headers,
    )
    assert transactions.status_code == 200
    payload = transactions.json()
    assert len(payload) == 1
    assert payload[0]["items"][0]["identifier"] == "12345"


def test_inventory_transactions_still_return_legacy_identifier_history(app_client):
    from backend.app.core.database import SessionLocal
    from backend.app.models.inventory import MaterialTransaction, MaterialTransactionItem

    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = _create_assigned_customer(app_client, headers)

    fixture = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_id,
            "code": "C-78-3",
            "name": "Legacy Identifier Fixture",
            "storage_location": "A-01",
            "min_stock_qty": 1,
        },
        headers=headers,
    )
    assert fixture.status_code == 201
    fixture_id = fixture.json()["id"]

    db = SessionLocal()
    try:
        transaction = MaterialTransaction(
            customer_id=customer_id,
            transaction_type="receipt",
            occurred_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            created_by="legacy-user",
            transaction_no="LEGACY-202606",
            note="legacy import",
        )
        db.add(transaction)
        db.flush()
        db.add(
            MaterialTransactionItem(
                transaction_id=transaction.id,
                fixture_id=fixture_id,
                ownership_type="self_purchased",
                identifier="202606",
                quantity=1,
                note=None,
            )
        )
        db.commit()
    finally:
        db.close()

    response = app_client.get(
        "/api/v2/inventory/transactions",
        params={"limit": 2000, "customer_id": customer_id, "fixture_code": "C-78-3"},
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["items"][0]["identifier"] == "202606"

    legacy_identifier_query = app_client.get(
        "/api/v2/inventory/transactions",
        params={"limit": 2000, "customer_id": customer_id, "identifier": "202606"},
        headers=headers,
    )

    assert legacy_identifier_query.status_code == 200
    legacy_payload = legacy_identifier_query.json()
    assert len(legacy_payload) == 1
    assert legacy_payload[0]["items"][0]["fixture_code"] == "C-78-3"


def test_transaction_csv_export_applies_ownership_filter(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = _create_assigned_customer(app_client, headers)

    fixture = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_id,
            "code": "EXPORT-FILTER-01",
            "name": "Export Filter Fixture",
            "storage_location": "E-01",
            "min_stock_qty": 1,
        },
        headers=headers,
    )
    assert fixture.status_code == 201
    fixture_id = fixture.json()["id"]

    receipt = app_client.post(
        "/api/v2/inventory/receipts",
        json={
            "customer_id": customer_id,
            "created_by": "Export Tester",
            "transaction_no": "EXPORT-FILTER-TX",
            "items": [
                {
                    "fixture_id": fixture_id,
                    "ownership_type": "self_purchased",
                    "identifier": "SELF-ONLY",
                    "quantity": 1,
                },
                {
                    "fixture_id": fixture_id,
                    "ownership_type": "customer_supplied",
                    "identifier": "CUSTOMER-ONLY",
                    "quantity": 2,
                },
            ],
        },
        headers=headers,
    )
    assert receipt.status_code == 204

    exported = app_client.get(
        "/api/v2/inventory/transactions/export",
        params={
            "customer_id": customer_id,
            "ownership_type": "self_purchased",
        },
        headers=headers,
    )

    assert exported.status_code == 200
    assert "SELF-ONLY" in exported.text
    assert "CUSTOMER-ONLY" not in exported.text


def test_transaction_filters_accept_repeated_multi_value_query_parameters(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = _create_assigned_customer(app_client, headers)

    fixture = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_id,
            "code": "MULTI-FILTER-01",
            "name": "Multi Filter Fixture",
            "min_stock_qty": 0,
        },
        headers=headers,
    )
    assert fixture.status_code == 201
    fixture_id = fixture.json()["id"]

    for endpoint, transaction_no, quantity in (
        ("receipts", "MULTI-RECEIPT", 3),
        ("returns", "MULTI-RETURN", 1),
    ):
        response = app_client.post(
            f"/api/v2/inventory/{endpoint}",
            json={
                "customer_id": customer_id,
                "created_by": "Multi Filter Tester",
                "transaction_no": transaction_no,
                "items": [
                    {
                        "fixture_id": fixture_id,
                        "ownership_type": "self_purchased",
                        "identifier": "MULTI-01",
                        "quantity": quantity,
                    }
                ],
            },
            headers=headers,
        )
        assert response.status_code == 204

    filtered = app_client.get(
        "/api/v2/inventory/transactions/overview",
        params=[
            ("customer_id", str(customer_id)),
            ("transaction_type", "receipt"),
            ("transaction_type", "return"),
            ("ownership_type", "self_purchased"),
            ("page", "1"),
            ("page_size", "50"),
        ],
        headers=headers,
    )

    assert filtered.status_code == 200
    payload = filtered.json()
    assert payload["total"] == 2
    assert {row["transaction_type"] for row in payload["items"]} == {"receipt", "return"}


def test_transaction_csv_export_streams_every_matching_transaction_beyond_legacy_limit(app_client):
    from backend.app.core.database import SessionLocal
    from backend.app.models.inventory import MaterialTransactionItem

    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = _create_assigned_customer(app_client, headers)

    fixture = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_id,
            "code": "EXPORT-UNLIMITED-01",
            "name": "Unlimited Export Fixture",
            "min_stock_qty": 0,
        },
        headers=headers,
    )
    assert fixture.status_code == 201
    fixture_id = fixture.json()["id"]

    db = SessionLocal()
    try:
        transactions = [
            MaterialTransaction(
                customer_id=customer_id,
                transaction_type="receipt",
                occurred_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
                created_by="Unlimited Export Tester",
                transaction_no=f"EXPORT-UNLIMITED-{index:04d}",
                note=None,
            )
            for index in range(2001)
        ]
        db.add_all(transactions)
        db.flush()
        db.add_all(
            [
                MaterialTransactionItem(
                    transaction_id=transaction.id,
                    fixture_id=fixture_id,
                    ownership_type="self_purchased",
                    identifier=f"UNLIMITED-{index:04d}",
                    quantity=1,
                    note=None,
                )
                for index, transaction in enumerate(transactions)
            ]
        )
        db.commit()
    finally:
        db.close()

    exported = app_client.get(
        "/api/v2/inventory/transactions/export",
        params={
            "customer_id": customer_id,
            "created_by": "Unlimited Export Tester",
        },
        headers=headers,
    )

    assert exported.status_code == 200
    assert "content-length" not in exported.headers
    rows = list(csv.DictReader(StringIO(exported.text.lstrip("\ufeff"))))
    assert len(rows) == 2001
    assert {row["identifier"] for row in rows} == {
        f"UNLIMITED-{index:04d}" for index in range(2001)
    }


def test_admin_transaction_page_filters_and_paginates_by_transaction(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = _create_assigned_customer(app_client, headers)

    fixture_a = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_id,
            "code": "LEDGER-A",
            "name": "Ledger Fixture A",
            "storage_location": "L-A",
            "min_stock_qty": 1,
        },
        headers=headers,
    )
    fixture_b = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_id,
            "code": "LEDGER-B",
            "name": "Ledger Fixture B",
            "storage_location": "L-B",
            "min_stock_qty": 1,
        },
        headers=headers,
    )
    assert fixture_a.status_code == 201
    assert fixture_b.status_code == 201

    fixture_a_id = fixture_a.json()["id"]
    fixture_b_id = fixture_b.json()["id"]

    first_tx = app_client.post(
        "/api/v2/inventory/receipts",
        json={
            "customer_id": customer_id,
            "created_by": "Alpha User",
            "transaction_no": "LEDGER-TX-001",
            "items": [
                {
                    "fixture_id": fixture_a_id,
                    "ownership_type": "self_purchased",
                    "identifier": "2607",
                    "quantity": 3,
                }
            ],
        },
        headers=headers,
    )
    second_tx = app_client.post(
        "/api/v2/inventory/receipts",
        json={
            "customer_id": customer_id,
            "created_by": "Beta User",
            "transaction_no": "LEDGER-TX-002",
            "items": [
                {
                    "fixture_id": fixture_b_id,
                    "ownership_type": "self_purchased",
                    "identifier": "2608",
                    "quantity": 1,
                }
            ],
        },
        headers=headers,
    )
    assert first_tx.status_code == 204
    assert second_tx.status_code == 204

    filtered = app_client.get(
        "/api/v2/inventory/admin/transactions",
        params={
            "customer_id": customer_id,
            "page": 1,
            "page_size": 10,
            "fixture_code": "LEDGER-A",
            "created_by": "System Admin",
            "transaction_type": "receipt",
        },
        headers=headers,
    )
    assert filtered.status_code == 200
    payload = filtered.json()
    assert payload["total"] == 1
    assert payload["page"] == 1
    assert payload["page_size"] == 10
    assert len(payload["items"]) == 1
    assert payload["items"][0]["transaction_no"] == "LEDGER-TX-001"
    assert payload["items"][0]["created_by"] == "System Admin"
    assert payload["items"][0]["items"][0]["fixture_code"] == "LEDGER-A"

    paged = app_client.get(
        "/api/v2/inventory/admin/transactions",
        params={"customer_id": customer_id, "page": 1, "page_size": 1},
        headers=headers,
    )
    assert paged.status_code == 200
    paged_payload = paged.json()
    assert paged_payload["total"] == 2
    assert len(paged_payload["items"]) == 1
    assert paged_payload["items"][0]["transaction_no"] == "LEDGER-TX-002"


def test_admin_transaction_page_mysql_sql_orders_by_transaction_id_only():
    repo = InventoryRepository(None)  # type: ignore[arg-type]
    stmt = (
        repo._build_transaction_id_stmt(customer_id=20)
        .order_by(MaterialTransaction.id.desc())
        .offset(0)
        .limit(12)
    )

    sql = str(stmt.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))

    assert "ORDER BY material_transactions.id DESC" in sql
    assert "occurred_at" not in sql


def test_inventory_write_lock_queries_compile_for_mysql():
    db = Mock()
    db.scalars.return_value = []
    repo = InventoryRepository(db)

    repo.lock_fixtures_for_update([2, 1, 2])
    fixture_lock_stmt = db.scalars.call_args.args[0]
    fixture_lock_sql = str(
        fixture_lock_stmt.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True})
    )
    assert "ORDER BY fixtures.id ASC" in fixture_lock_sql
    assert "FOR UPDATE" in fixture_lock_sql

    db.scalar.return_value = object()
    repo.get_or_create_stock_summary_for_update(1)
    summary_lock_stmt = db.scalar.call_args.args[0]
    summary_lock_sql = str(
        summary_lock_stmt.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True})
    )
    assert "fixture_stock_summary.fixture_id = 1" in summary_lock_sql
    assert "FOR UPDATE" in summary_lock_sql

    db.execute.return_value = []
    repo.get_available_identifier_qty(
        fixture_id=1,
        identifier="2606",
        ownership_type="customer_supplied",
    )
    identifier_lock_stmt = db.execute.call_args.args[0]
    identifier_lock_sql = str(
        identifier_lock_stmt.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True})
    )
    assert "material_transaction_items.identifier = '2606'" in identifier_lock_sql
    assert "material_transaction_items.ownership_type = 'customer_supplied'" in identifier_lock_sql
    assert "FOR UPDATE" in identifier_lock_sql


def test_inventory_receipt_requires_transaction_no(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = _create_assigned_customer(app_client, headers)

    fixture = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_id,
            "code": "REQ-TX-001",
            "name": "Required Tx Fixture",
            "storage_location": "REQ-TX",
            "min_stock_qty": 1,
        },
        headers=headers,
    )
    assert fixture.status_code == 201
    fixture_id = fixture.json()["id"]

    receipt = app_client.post(
        "/api/v2/inventory/receipts",
        json={
            "customer_id": customer_id,
            "created_by": "System Admin",
            "items": [
                {
                    "fixture_id": fixture_id,
                    "ownership_type": "self_purchased",
                    "identifier": "2609",
                    "quantity": 1,
                }
            ],
        },
        headers=headers,
    )

    assert receipt.status_code == 422
    assert "transaction_no" in receipt.text


def test_inventory_read_endpoints_tolerate_legacy_blank_transaction_no(app_client):
    from backend.app.core.database import SessionLocal
    from backend.app.models.inventory import MaterialTransaction, MaterialTransactionItem

    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = _create_assigned_customer(app_client, headers)

    fixture = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_id,
            "code": "LEGACY-BLANK-TX",
            "name": "Legacy Blank Transaction No",
            "storage_location": "L-LEGACY",
            "min_stock_qty": 1,
        },
        headers=headers,
    )
    assert fixture.status_code == 201
    fixture_id = fixture.json()["id"]

    db = SessionLocal()
    try:
        transaction = MaterialTransaction(
            customer_id=customer_id,
            transaction_type="receipt",
            occurred_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
            created_by="legacy-user",
            transaction_no="",
            note="legacy blank tx no",
        )
        db.add(transaction)
        db.flush()
        db.add(
            MaterialTransactionItem(
                transaction_id=transaction.id,
                fixture_id=fixture_id,
                ownership_type="self_purchased",
                identifier="2607",
                quantity=2,
                note=None,
            )
        )
        db.commit()
    finally:
        db.close()

    transactions = app_client.get(
        "/api/v2/inventory/transactions",
        params={"customer_id": customer_id, "created_by": "legacy-user"},
        headers=headers,
    )
    assert transactions.status_code == 200
    transactions_payload = transactions.json()
    assert len(transactions_payload) == 1
    assert transactions_payload[0]["transaction_no"] is None

    ledger_page = app_client.get(
        "/api/v2/inventory/admin/transactions",
        params={"customer_id": customer_id, "page": 1, "page_size": 10, "created_by": "legacy-user"},
        headers=headers,
    )
    assert ledger_page.status_code == 200
    ledger_payload = ledger_page.json()
    assert ledger_payload["total"] == 1
    assert ledger_payload["items"][0]["transaction_no"] is None

    overview_page = app_client.get(
        "/api/v2/inventory/transactions/overview",
        params={"customer_id": customer_id, "page": 1, "page_size": 10, "created_by": "legacy-user"},
        headers=headers,
    )
    assert overview_page.status_code == 200
    overview_payload = overview_page.json()
    assert overview_payload["total"] == 1
    assert overview_payload["items"][0]["transaction_no"] is None


def test_inventory_dashboard_summary_counts_beyond_recent_200_transactions(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = _create_assigned_customer(app_client, headers)

    fixture = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_id,
            "code": "DB-SUM-001",
            "name": "Dashboard Summary Fixture",
            "storage_location": "DB-SUM",
            "min_stock_qty": 500,
        },
        headers=headers,
    )
    assert fixture.status_code == 201
    fixture_id = fixture.json()["id"]

    for index in range(205):
        receipt = app_client.post(
            "/api/v2/inventory/receipts",
            json={
                "customer_id": customer_id,
                "created_by": "Summary User",
                "transaction_no": f"DB-SUM-R-{index + 1:03d}",
                "items": [
                    {
                        "fixture_id": fixture_id,
                        "ownership_type": "self_purchased",
                        "identifier": f"{3000 + index}",
                        "quantity": 1,
                    }
                ],
            },
            headers=headers,
        )
        assert receipt.status_code == 204

    for index in range(12):
        returned_identifier = normalize_identifier_for_write(str(3000 + index))
        returned_identifier = returned_identifier or str(3000 + index)
        returned = app_client.post(
            "/api/v2/inventory/returns",
            json={
                "customer_id": customer_id,
                "created_by": "Summary User",
                "transaction_no": f"DB-SUM-T-{index + 1:03d}",
                "items": [
                    {
                        "fixture_id": fixture_id,
                        "ownership_type": "self_purchased",
                        "identifier": returned_identifier,
                        "quantity": 1,
                    }
                ],
            },
            headers=headers,
        )
        assert returned.status_code == 204

    summary = app_client.get(
        "/api/v2/inventory/dashboard-summary",
        params={"customer_id": customer_id},
        headers=headers,
    )
    assert summary.status_code == 200
    payload = summary.json()
    assert payload["today_receipt_qty"] == 205
    assert payload["today_return_qty"] == 12
    assert payload["low_stock_count"] == 1
    assert payload["has_more_low_stock_entries"] is False
    assert len(payload["low_stock_preview_entries"]) == 1
    assert payload["low_stock_preview_entries"][0]["fixture_code"] == "DB-SUM-001"
    assert len(payload["recent_receipt_entries"]) == 10
    assert payload["recent_receipt_entries"][0]["transaction_no"] == "DB-SUM-R-205"
    assert payload["recent_receipt_entries"][-1]["transaction_no"] == "DB-SUM-R-196"
    assert len(payload["recent_return_entries"]) == 10
    assert payload["recent_return_entries"][0]["transaction_no"] == "DB-SUM-T-012"
    assert payload["recent_return_entries"][-1]["transaction_no"] == "DB-SUM-T-003"


def test_csv_import_flow(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = _create_assigned_customer(app_client, headers)

    payload = {
        "filename": "fixtures.csv",
        "content": "code,name,storage_location,min_stock_qty,description,is_active\nT-CSV,CSV Fixture,A-02,1,imported,true\n",
    }
    response = app_client.post(
        f"/api/v2/master/fixtures/import?customer_id={customer_id}",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["imported_count"] == 1


def test_admin_can_reverse_transaction_case_and_rebuild_stock(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = _create_assigned_customer(app_client, headers)

    fixture = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_id,
            "code": "REV-001",
            "name": "Reverse Fixture",
            "storage_location": "REV-A",
            "min_stock_qty": 1,
        },
        headers=headers,
    )
    assert fixture.status_code == 201
    fixture_id = fixture.json()["id"]

    receipt = app_client.post(
        "/api/v2/inventory/receipts",
        json={
            "customer_id": customer_id,
            "created_by": "System Admin",
            "transaction_no": "REV-TX-001",
            "items": [
                {
                    "fixture_id": fixture_id,
                    "ownership_type": "self_purchased",
                    "identifier": "2607",
                    "quantity": 8,
                }
            ],
        },
        headers=headers,
    )
    assert receipt.status_code == 204

    transactions = app_client.get(
        "/api/v2/inventory/transactions",
        params={"customer_id": customer_id, "transaction_no": "REV-TX-001"},
        headers=headers,
    )
    assert transactions.status_code == 200
    transaction_id = transactions.json()[0]["id"]

    reversed_tx = app_client.delete(
        f"/api/v2/inventory/admin/transactions/{transaction_id}",
        params={"customer_id": customer_id},
        headers=headers,
    )
    assert reversed_tx.status_code == 200
    assert reversed_tx.json()["transaction_no"] == "REV-TX-001"
    assert reversed_tx.json()["item_count"] == 1
    assert reversed_tx.json()["total_quantity"] == 8

    stock = app_client.get(
        "/api/v2/inventory/stock",
        params={"customer_id": customer_id},
        headers=headers,
    )
    assert stock.status_code == 200
    stock_row = next(row for row in stock.json() if row["fixture_id"] == fixture_id)
    assert stock_row["stock_qty"] == 0
    assert stock_row["stock_status"] == "out_of_stock"

    remaining = app_client.get(
        "/api/v2/inventory/transactions",
        params={"customer_id": customer_id, "transaction_no": "REV-TX-001"},
        headers=headers,
    )
    assert remaining.status_code == 200
    assert remaining.json() == []


def test_admin_recalculate_inventory_state_repairs_summary_after_manual_change(app_client):
    from backend.app.core.database import SessionLocal
    from backend.app.models.inventory import FixtureStockSummary

    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = _create_assigned_customer(app_client, headers)

    fixture = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_id,
            "code": "RECALC-001",
            "name": "Recalc Fixture",
            "storage_location": "RC-A",
            "min_stock_qty": 3,
        },
        headers=headers,
    )
    assert fixture.status_code == 201
    fixture_id = fixture.json()["id"]

    receipt = app_client.post(
        "/api/v2/inventory/receipts",
        json={
            "customer_id": customer_id,
            "created_by": "System Admin",
            "transaction_no": "RECALC-TX-001",
            "items": [
                {
                    "fixture_id": fixture_id,
                    "ownership_type": "self_purchased",
                    "identifier": "2608",
                    "quantity": 5,
                }
            ],
        },
        headers=headers,
    )
    assert receipt.status_code == 204

    db = SessionLocal()
    try:
        summary = db.get(FixtureStockSummary, fixture_id)
        assert summary is not None
        summary.stock_qty = 99
        summary.stock_status = "normal"
        db.commit()
    finally:
        db.close()

    recalc = app_client.post(
        "/api/v2/inventory/admin/recalculate",
        params={"customer_id": customer_id},
        headers=headers,
    )
    assert recalc.status_code == 200
    assert recalc.json()["fixture_count"] >= 1
    assert recalc.json()["transaction_count"] >= 1

    stock = app_client.get(
        "/api/v2/inventory/stock",
        params={"customer_id": customer_id},
        headers=headers,
    )
    assert stock.status_code == 200
    stock_row = next(row for row in stock.json() if row["fixture_id"] == fixture_id)
    assert stock_row["stock_qty"] == 5
    assert stock_row["stock_status"] == "normal"
