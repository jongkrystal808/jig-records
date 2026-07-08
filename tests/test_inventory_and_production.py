from __future__ import annotations


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
    assert search.json()[0]["entity_type"] == "fixture"


def test_inventory_rejects_identifier_longer_than_four_digits_with_json_safe_error(app_client):
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

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "validation_error"
    assert payload["error"]["message"] == "欄位驗證失敗"
    assert payload["error"]["details"][0]["msg"] == "Value error, identifier must be 4 digits or fewer"
    assert payload["error"]["details"][0]["ctx"]["error"] == "identifier must be 4 digits or fewer"


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
