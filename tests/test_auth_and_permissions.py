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
    assert session["role"] == "super_admin"
    assert session["user"]["allowed_customer_ids"] == []

    customers = app_client.get("/api/v2/master/customers", headers={"Authorization": f"Bearer {session['token']}"})
    assert customers.status_code == 200
    assert customers.json() == []

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
    current_admin = app_client.get("/api/v2/auth/users", headers=admin_headers)
    assert current_admin.status_code == 200
    admin_user_id = next(row["id"] for row in current_admin.json() if row["username"] == "admin")

    created_customer_a = app_client.post(
        "/api/v2/master/customers",
        json={"code": "CUST1", "name": "Customer 1", "assigned_user_ids": [admin_user_id]},
        headers=admin_headers,
    )
    assert created_customer_a.status_code == 201
    customer_a = created_customer_a.json()["id"]

    created_customer = app_client.post(
        "/api/v2/master/customers",
        json={"code": "CUST2", "name": "Customer 2", "assigned_user_ids": [admin_user_id]},
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
            "code": "CUST1",
            "name": "Customer 1",
            "assigned_user_ids": [admin_user_id, created_user.json()["id"]],
        },
        headers=admin_headers,
    )
    assert assign_customer.status_code == 200
    assert assign_customer.json()["assigned_user_ids"] == [admin_user_id, created_user.json()["id"]]

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

    admin_fixture_b = app_client.post(
        "/api/v2/master/fixtures",
        json={
            "customer_id": customer_b,
            "code": "FX-PRIVATE-IMAGE",
            "name": "Private Fixture Image",
            "min_stock_qty": 1,
        },
        headers=admin_headers,
    )
    assert admin_fixture_b.status_code == 201
    uploaded = app_client.post(
        f"/api/v2/master/fixtures/{admin_fixture_b.json()['id']}/image",
        params={"customer_id": customer_b},
        files={"image": ("fixture.png", b"private-image", "image/png")},
        headers=admin_headers,
    )
    assert uploaded.status_code == 200

    forbidden_image = app_client.get(
        "/api/v2/master/fixtures/FX-PRIVATE-IMAGE/image",
        params={"customer_id": customer_b},
        headers=scoped_headers,
    )
    assert forbidden_image.status_code == 403

    forbidden_reassignment = app_client.put(
        f"/api/v2/master/fixtures/{admin_fixture_b.json()['id']}",
        json={
            "customer_id": customer_a,
            "code": "FX-PRIVATE-IMAGE",
            "name": "Private Fixture Image",
            "min_stock_qty": 1,
            "is_active": True,
        },
        headers=scoped_headers,
    )
    assert forbidden_reassignment.status_code == 403


def test_admin_only_sees_assigned_customers(app_client):
    admin = _login(app_client)
    admin_headers = {"Authorization": f"Bearer {admin['token']}"}

    current_admin = app_client.get("/api/v2/auth/users", headers=admin_headers)
    assert current_admin.status_code == 200
    admin_user_id = next(row["id"] for row in current_admin.json() if row["username"] == "admin")

    created_customer_a = app_client.post(
        "/api/v2/master/customers",
        json={"code": "CUST1", "name": "Customer 1", "assigned_user_ids": [admin_user_id]},
        headers=admin_headers,
    )
    assert created_customer_a.status_code == 201
    customer_a = created_customer_a.json()["id"]

    created_customer = app_client.post(
        "/api/v2/master/customers",
        json={"code": "CUST2", "name": "Customer 2"},
        headers=admin_headers,
    )
    assert created_customer.status_code == 201
    customer_b = created_customer.json()["id"]

    scoped_admin = _login(app_client)
    scoped_admin_headers = {"Authorization": f"Bearer {scoped_admin['token']}"}

    scoped_customers = app_client.get("/api/v2/master/customers", headers=scoped_admin_headers)
    assert scoped_customers.status_code == 200
    assert [row["id"] for row in scoped_customers.json()] == [customer_a]

    forbidden = app_client.get("/api/v2/inventory/stock", params={"customer_id": customer_b}, headers=scoped_admin_headers)
    assert forbidden.status_code == 403


def test_validation_error_uses_unified_error_format(app_client):
    response = app_client.post("/api/v2/auth/login", json={"username": "", "password": ""})
    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "validation_error"
    assert payload["error"]["message"] == "欄位驗證失敗"


def test_user_create_and_update_reject_illegal_roles(app_client):
    admin = _login(app_client)
    admin_headers = {"Authorization": f"Bearer {admin['token']}"}

    guest_role = app_client.post(
        "/api/v2/auth/users",
        json={
            "username": "not-a-guest-session",
            "password": "secret123",
            "display_name": "Invalid Guest Account",
            "role": "guest",
            "is_active": True,
            "allowed_customer_ids": [],
        },
        headers=admin_headers,
    )
    assert guest_role.status_code == 422
    assert guest_role.json()["error"]["code"] == "validation_error"

    users = app_client.get("/api/v2/auth/users", headers=admin_headers)
    assert users.status_code == 200
    admin_user = next(row for row in users.json() if row["username"] == "admin")
    arbitrary_role = app_client.put(
        f"/api/v2/auth/users/{admin_user['id']}",
        json={
            "email": admin_user["email"],
            "display_name": admin_user["display_name"],
            "role": "manager",
            "is_active": admin_user["is_active"],
            "allowed_customer_ids": admin_user["allowed_customer_ids"],
        },
        headers=admin_headers,
    )
    assert arbitrary_role.status_code == 422
    assert arbitrary_role.json()["error"]["code"] == "validation_error"


def test_super_admin_and_admin_management_boundaries(app_client):
    super_admin = _login(app_client)
    super_headers = {"Authorization": f"Bearer {super_admin['token']}"}
    super_users = app_client.get("/api/v2/auth/users", headers=super_headers)
    super_admin_id = next(row["id"] for row in super_users.json() if row["username"] == "admin")
    customer = app_client.post(
        "/api/v2/master/customers",
        json={"code": "ROLE-CUST", "name": "Role Customer", "assigned_user_ids": [super_admin_id]},
        headers=super_headers,
    )
    assert customer.status_code == 201
    customer_id = customer.json()["id"]

    ordinary_admin = app_client.post(
        "/api/v2/auth/users",
        json={
            "username": "ordinary-admin",
            "password": "secret123",
            "display_name": "Ordinary Admin",
            "role": "admin",
            "is_active": True,
            "allowed_customer_ids": [customer_id],
        },
        headers=super_headers,
    )
    assert ordinary_admin.status_code == 201
    ordinary_session = app_client.post(
        "/api/v2/auth/login",
        json={"username": "ordinary-admin", "password": "secret123"},
    ).json()
    admin_headers = {"Authorization": f"Bearer {ordinary_session['token']}"}

    assert app_client.get("/api/v2/auth/users", headers=admin_headers).status_code == 403
    assert app_client.post(
        "/api/v2/master/customers",
        json={"code": "DENIED", "name": "Denied"},
        headers=admin_headers,
    ).status_code == 403
    assert app_client.post(
        f"/api/v2/auth/users/{ordinary_admin.json()['id']}/reset-password",
        json={"password": "blocked-reset"},
        headers=admin_headers,
    ).status_code == 403
    assert app_client.get(
        "/api/v2/inventory/admin/transactions",
        params={"customer_id": customer_id},
        headers=admin_headers,
    ).status_code == 200
    assert app_client.get(
        "/api/v2/master/fixtures/quality",
        params={"customer_id": customer_id},
        headers=admin_headers,
    ).status_code == 200


def test_signed_in_user_can_change_only_own_password(app_client):
    super_admin = _login(app_client)
    headers = {"Authorization": f"Bearer {super_admin['token']}"}

    wrong_current = app_client.post(
        "/api/v2/auth/password",
        json={"current_password": "wrong", "new_password": "new-secret-123"},
        headers=headers,
    )
    assert wrong_current.status_code == 400

    changed = app_client.post(
        "/api/v2/auth/password",
        json={"current_password": "admin123", "new_password": "new-secret-123"},
        headers=headers,
    )
    assert changed.status_code == 204
    assert app_client.post(
        "/api/v2/auth/login",
        json={"username": "admin", "password": "admin123"},
    ).status_code == 401
    relogin = app_client.post(
        "/api/v2/auth/login",
        json={"username": "admin", "password": "new-secret-123"},
    )
    assert relogin.status_code == 200
    assert relogin.json()["role"] == "super_admin"


def test_regular_user_can_change_own_password(app_client):
    super_admin = _login(app_client)
    super_headers = {"Authorization": f"Bearer {super_admin['token']}"}
    user = app_client.post(
        "/api/v2/auth/users",
        json={
            "username": "password-user",
            "password": "secret123",
            "display_name": "Password User",
            "role": "user",
            "is_active": True,
            "allowed_customer_ids": [],
        },
        headers=super_headers,
    )
    assert user.status_code == 201
    user_session = app_client.post(
        "/api/v2/auth/login",
        json={"username": "password-user", "password": "secret123"},
    ).json()
    changed = app_client.post(
        "/api/v2/auth/password",
        json={"current_password": "secret123", "new_password": "user-new-secret"},
        headers={"Authorization": f"Bearer {user_session['token']}"},
    )
    assert changed.status_code == 204
    assert app_client.post(
        "/api/v2/auth/login",
        json={"username": "password-user", "password": "user-new-secret"},
    ).status_code == 200


def test_model_shortcut_preferences_persist_per_user_and_customer(app_client):
    admin = _login(app_client)
    headers = {"Authorization": f"Bearer {admin['token']}"}
    users = app_client.get("/api/v2/auth/users", headers=headers)
    admin_user_id = next(row["id"] for row in users.json() if row["username"] == "admin")
    customer = app_client.post(
        "/api/v2/master/customers",
        json={"code": "PREF-CUST", "name": "Preference Customer", "assigned_user_ids": [admin_user_id]},
        headers=headers,
    )
    assert customer.status_code == 201
    customer_id = customer.json()["id"]
    model = app_client.post(
        "/api/v2/master/models",
        json={"customer_id": customer_id, "code": "PREF-MODEL", "name": "Preference Model"},
        headers=headers,
    )
    assert model.status_code == 201
    model_id = model.json()["id"]

    initial = app_client.get(
        "/api/v2/auth/preferences/model-shortcuts",
        params={"customer_id": customer_id},
        headers=headers,
    )
    assert initial.status_code == 200
    assert initial.json() == []

    for expected_count in (1, 2):
        recorded = app_client.post(
            f"/api/v2/auth/preferences/model-shortcuts/{model_id}/query",
            params={"customer_id": customer_id},
            headers=headers,
        )
        assert recorded.status_code == 200
        assert recorded.json()["query_count"] == expected_count
        assert recorded.json()["last_queried_at"] is not None

    pinned = app_client.put(
        f"/api/v2/auth/preferences/model-shortcuts/{model_id}/pin",
        params={"customer_id": customer_id},
        json={"pinned": True},
        headers=headers,
    )
    assert pinned.status_code == 200
    assert pinned.json()["pinned"] is True

    reloaded = app_client.get(
        "/api/v2/auth/preferences/model-shortcuts",
        params={"customer_id": customer_id},
        headers=headers,
    )
    assert reloaded.status_code == 200
    assert reloaded.json()[0]["model_code"] == "PREF-MODEL"
    assert reloaded.json()[0]["query_count"] == 2
    assert reloaded.json()[0]["pinned"] is True

    guest = _guest(app_client)
    guest_response = app_client.get(
        "/api/v2/auth/preferences/model-shortcuts",
        params={"customer_id": customer_id},
        headers={"Authorization": f"Bearer {guest['token']}"},
    )
    assert guest_response.status_code == 403
