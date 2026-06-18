from __future__ import annotations


def _login(client):
    response = client.post(
        "/api/v2/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    return response.json()


def _guest(client):
    response = client.post("/api/v2/auth/guest")
    assert response.status_code == 200
    return response.json()


def test_auth_login_guest_and_permissions(app_client):
    health = app_client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok", "database": "ok"}

    session = _login(app_client)
    assert session["mode"] == "user"
    assert session["token"]
    assert session["role"] == "admin"
    assert session["user"]["allowed_customer_ids"] == []

    customers = app_client.get("/api/v2/master/customers", headers={"Authorization": f"Bearer {session['token']}"})
    assert customers.status_code == 200
    assert customers.json()

    guest = _guest(app_client)
    guest_customers = app_client.get("/api/v2/master/customers", headers={"Authorization": f"Bearer {guest['token']}"})
    assert guest_customers.status_code == 200

    forbidden = app_client.post(
        "/api/v2/master/customers",
        json={"code": "CUSTX", "name": "Customer X"},
        headers={"Authorization": f"Bearer {guest['token']}"},
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "forbidden"


def test_scoped_user_only_sees_assigned_customers(app_client):
    admin = _login(app_client)
    admin_headers = {"Authorization": f"Bearer {admin['token']}"}
    customers = app_client.get("/api/v2/master/customers", headers=admin_headers).json()
    customer_a = customers[0]["id"]

    created_customer = app_client.post(
        "/api/v2/master/customers",
        json={"code": "CUST2", "name": "Customer 2"},
        headers=admin_headers,
    )
    assert created_customer.status_code == 201
    customer_b = created_customer.json()["id"]

    created_user = app_client.post(
        "/api/v2/auth/users",
        json={
            "username": "limited",
            "password": "secret123",
            "display_name": "Limited User",
            "role": "user",
            "is_active": True,
            "allowed_customer_ids": [],
        },
        headers=admin_headers,
    )
    assert created_user.status_code == 201
    assert created_user.json()["allowed_customer_ids"] == []

    assign_customer = app_client.put(
        f"/api/v2/master/customers/{customer_a}",
        json={
            "code": customers[0]["code"],
            "name": customers[0]["name"],
            "assigned_user_ids": [created_user.json()["id"]],
        },
        headers=admin_headers,
    )
    assert assign_customer.status_code == 200
    assert assign_customer.json()["assigned_user_ids"] == [created_user.json()["id"]]

    scoped = app_client.post("/api/v2/auth/login", json={"username": "limited", "password": "secret123"})
    assert scoped.status_code == 200
    scoped_headers = {"Authorization": f"Bearer {scoped.json()['token']}"}

    scoped_customers = app_client.get("/api/v2/master/customers", headers=scoped_headers)
    assert scoped_customers.status_code == 200
    assert [row["id"] for row in scoped_customers.json()] == [customer_a]

    forbidden = app_client.get("/api/v2/inventory/stock", params={"customer_id": customer_b}, headers=scoped_headers)
    assert forbidden.status_code == 403

    created_fixture = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_a,
            "code": "FX-001",
            "name": "Fixture 001",
            "storage_location": "A-01",
            "min_stock_qty": 1,
        },
        headers=scoped_headers,
    )
    assert created_fixture.status_code == 201

    forbidden_fixture = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_b,
            "code": "FX-002",
            "name": "Fixture 002",
            "storage_location": "A-02",
            "min_stock_qty": 1,
        },
        headers=scoped_headers,
    )
    assert forbidden_fixture.status_code == 403


def test_validation_error_uses_unified_error_format(app_client):
    response = app_client.post("/api/v2/auth/login", json={"username": "", "password": ""})
    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "validation_error"
    assert payload["error"]["message"] == "欄位驗證失敗"
