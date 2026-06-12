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
    session = _login(app_client)
    assert session["mode"] == "user"
    assert session["token"]
    assert session["role"] == "admin"

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


def test_validation_error_uses_unified_error_format(app_client):
    response = app_client.post("/api/v2/auth/login", json={"username": "", "password": ""})
    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "validation_error"
    assert payload["error"]["message"] == "欄位驗證失敗"
