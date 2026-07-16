from __future__ import annotations

from datetime import datetime, timezone


def _login(client):
    response = client.post(
        "/api/v2/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    return response.json()["token"]


def test_inventory_capacity_and_search_flow(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}

    customer_id = app_client.get("/api/v2/master/customers", headers=headers).json()[0]["id"]

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

    stock = app_client.get("/api/v2/inventory/stock", headers=headers)
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

    search = app_client.get("/api/v2/search/global", params={"q": "T-001"}, headers=headers)
    assert search.status_code == 200
    payload = search.json()
    assert payload["items"][0]["entity_type"] == "fixture"
    assert payload["total"] >= 1


def test_fixture_reenable_recomputes_low_stock_alert(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = app_client.get("/api/v2/master/customers", headers=headers).json()[0]["id"]

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
    customer_id = app_client.get("/api/v2/master/customers", headers=headers).json()[0]["id"]

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


def test_search_global_matches_fixture_and_model_codes_without_separators(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = app_client.get("/api/v2/master/customers", headers=headers).json()[0]["id"]

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


def test_search_fixture_context_loads_detail_on_demand(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = app_client.get("/api/v2/master/customers", headers=headers).json()[0]["id"]

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
    customer_id = app_client.get("/api/v2/master/customers", headers=headers).json()[0]["id"]

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
    customer_id = app_client.get("/api/v2/master/customers", headers=headers).json()[0]["id"]

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
    customer_id = app_client.get("/api/v2/master/customers", headers=headers).json()[0]["id"]

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


def test_csv_import_flow(app_client):
    token = _login(app_client)
    headers = {"Authorization": f"Bearer {token}"}
    customer_id = app_client.get("/api/v2/master/customers", headers=headers).json()[0]["id"]

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
    customer_id = app_client.get("/api/v2/master/customers", headers=headers).json()[0]["id"]

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
    customer_id = app_client.get("/api/v2/master/customers", headers=headers).json()[0]["id"]

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
