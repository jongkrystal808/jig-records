from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from backend.app.core.auth import SessionContext, _get_db as auth_get_db, create_session_token, require_permission
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.errors import register_error_handlers
from backend.app.models import Base
from backend.app.models.audit import AuditLog
from backend.app.models.inventory import FixtureStockLevel, FixtureStockSummary, MaterialTransaction
from backend.app.routers import api_router
from backend.app.repositories.master_repository import MasterRepository
from backend.app.schemas.common import CsvImportPayload
from backend.app.schemas.auth import UserCreate
from backend.app.schemas.inventory import StockTransactionCreate
from backend.app.schemas.master import FixtureCreate
from backend.app.schemas.production import FixtureRequirementCreate, ModelStationCreate
from backend.app.services.auth_service import AuthService
from backend.app.services.inventory_service import InventoryService
from backend.app.services.master_service import MasterService
from backend.app.services.production_service import ProductionService


class ServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_file.close()
        self.db_path = Path(temp_file.name)
        self.engine = create_engine(f"sqlite:///{self.db_path}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.SessionLocal()
        self.repo = MasterRepository(self.db)
        self.auth_service = AuthService(self.db)
        self.master_service = MasterService(self.db)
        self.production_service = ProductionService(self.db)
        self.inventory_service = InventoryService(self.db)

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()
        self.db_path.unlink(missing_ok=True)

    def seed_customer_bundle(self):
        customer = self.repo.create_customer(code="C-001", name="Customer 1")
        model = self.repo.create_model(customer_id=customer.id, code="M-001", name="Model 1")
        station = self.repo.create_station(customer_id=customer.id, code="ST-001", name="Station 1")
        fixture_a = self.repo.create_fixture(
            customer_id=customer.id,
            responsible_user_id=None,
            code="FX-A",
            name="Fixture A",
            storage_location=None,
            description=None,
        )
        fixture_b = self.repo.create_fixture(
            customer_id=customer.id,
            responsible_user_id=None,
            code="FX-B",
            name="Fixture B",
            storage_location=None,
            description=None,
        )

        self.db.add_all(
            [
                FixtureStockLevel(fixture_id=fixture_a.id, min_stock_qty=1, warning_threshold=0, alert_enabled=True),
                FixtureStockSummary(fixture_id=fixture_a.id, stock_qty=12, returned_qty=0, stock_status="normal"),
                FixtureStockLevel(fixture_id=fixture_b.id, min_stock_qty=1, warning_threshold=0, alert_enabled=True),
                FixtureStockSummary(fixture_id=fixture_b.id, stock_qty=9, returned_qty=0, stock_status="normal"),
            ]
        )
        self.db.commit()
        return {
            "customer": customer,
            "model": model,
            "station": station,
            "fixture_a": fixture_a,
            "fixture_b": fixture_b,
        }


class AuthServiceTests(ServiceTestCase):
    def test_create_and_login_user(self) -> None:
        customer = self.repo.create_customer(code="C-001", name="Customer 1")
        self.db.commit()
        created = self.auth_service.create_user(
            UserCreate(
                username="alice",
                password="secret123",
                display_name="Alice",
                role="manager",
                is_active=True,
                allowed_customer_ids=[customer.id],
            )
        )

        logged_in = self.auth_service.login("alice", "secret123")
        self.assertEqual(logged_in.id, created["id"])
        self.assertEqual(logged_in.display_name, "Alice")
        self.assertEqual(created["allowed_customer_ids"], [customer.id])

        audit_log = self.db.scalar(select(AuditLog).where(AuditLog.entity_type == "user"))
        self.assertIsNotNone(audit_log)
        self.assertIn("建立使用者", audit_log.summary)

        with self.assertRaises(ValueError):
            self.auth_service.login("alice", "wrong-password")

    def test_non_admin_user_can_be_created_before_customer_assignment(self) -> None:
        created = self.auth_service.create_user(
            UserCreate(
                username="bob",
                password="secret123",
                display_name="Bob",
                role="user",
                is_active=True,
                allowed_customer_ids=[],
            )
        )
        self.assertEqual(created["allowed_customer_ids"], [])

    def test_guest_cannot_write_and_admin_can_manage(self) -> None:
        write_guard = require_permission("write")
        manage_guard = require_permission("manage")

        with self.assertRaises(HTTPException) as write_exc:
            write_guard(
                session=SessionContext(
                    mode="guest",
                    user_id=None,
                    username=None,
                    display_name="訪客",
                    role="guest",
                    issued_at=0,
                    expires_at=9999999999,
                )
            )
        self.assertEqual(write_exc.exception.status_code, 403)

        with self.assertRaises(HTTPException) as manage_exc:
            manage_guard(
                session=SessionContext(
                    mode="user",
                    user_id=1,
                    username="bob",
                    display_name="Bob",
                    role="user",
                    issued_at=0,
                    expires_at=9999999999,
                )
            )
        self.assertEqual(manage_exc.exception.status_code, 403)

        allowed = manage_guard(
            session=SessionContext(
                mode="user",
                user_id=1,
                username="admin",
                display_name="Admin",
                role="admin",
                issued_at=0,
                expires_at=9999999999,
            )
        )
        self.assertEqual(allowed.role, "admin")


class ApiErrorFormatTests(unittest.TestCase):
    def setUp(self) -> None:
        app = FastAPI()
        register_error_handlers(app)

        @app.get("/http-error")
        def http_error():
            raise HTTPException(status_code=404, detail="resource missing")

        @app.get("/validation")
        def validation(value: int):
            return {"value": value}

        @app.get("/boom")
        def boom():
            raise RuntimeError("boom")

        self.client = TestClient(app, raise_server_exceptions=False)

    def test_http_exception_uses_standard_payload(self) -> None:
        response = self.client.get("/http-error")
        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertEqual(payload["error"]["code"], "not_found")
        self.assertEqual(payload["error"]["message"], "resource missing")

    def test_validation_error_uses_standard_payload(self) -> None:
        response = self.client.get("/validation", params={"value": "abc"})
        self.assertEqual(response.status_code, 422)
        payload = response.json()
        self.assertEqual(payload["error"]["code"], "validation_error")
        self.assertEqual(payload["error"]["message"], "欄位驗證失敗")
        self.assertIn("details", payload["error"])

    def test_generic_exception_uses_standard_payload(self) -> None:
        response = self.client.get("/boom")
        self.assertEqual(response.status_code, 500)
        payload = response.json()
        self.assertEqual(payload["error"]["code"], "internal_error")
        self.assertEqual(payload["error"]["message"], "系統發生未預期錯誤")


class ProductionServiceTests(ServiceTestCase):
    def test_fixture_code_is_unique_per_customer(self) -> None:
        customer_a = self.repo.create_customer(code="C-001", name="Customer 1")
        customer_b = self.repo.create_customer(code="C-002", name="Customer 2")
        self.db.commit()

        created_a = self.master_service.create_fixture(
            FixtureCreate(customer_id=customer_a.id, code="FX-001", name="Fixture A", min_stock_qty=1)
        )
        created_b = self.master_service.create_fixture(
            FixtureCreate(customer_id=customer_b.id, code="FX-001", name="Fixture B", min_stock_qty=2)
        )

        self.assertEqual(created_a["code"], "FX-001")
        self.assertEqual(created_b["code"], "FX-001")
        self.assertNotEqual(created_a["customer_id"], created_b["customer_id"])

    def test_update_model_station_moves_mapping(self) -> None:
        bundle = self.seed_customer_bundle()
        mapping = self.production_service.create_model_station(
            ModelStationCreate(
                customer_id=bundle["customer"].id,
                model_id=bundle["model"].id,
                station_id=bundle["station"].id,
            )
        )

        new_model = self.repo.create_model(customer_id=bundle["customer"].id, code="M-002", name="Model 2")
        new_station = self.repo.create_station(customer_id=bundle["customer"].id, code="ST-002", name="Station 2")
        self.db.commit()

        updated = self.production_service.update_model_station(
            mapping.id,
            ModelStationCreate(
                customer_id=bundle["customer"].id,
                model_id=new_model.id,
                station_id=new_station.id,
            ),
        )

        self.assertEqual(updated.model_id, new_model.id)
        self.assertEqual(updated.station_id, new_station.id)
        with self.assertRaises(ValueError):
            self.production_service.get_station_capacity(bundle["station"].id, bundle["model"].id, bundle["customer"].id)

        audit_log = self.db.scalar(select(AuditLog).where(AuditLog.entity_type == "model_station").order_by(AuditLog.id.desc()))
        self.assertIsNotNone(audit_log)
        self.assertIn("更新機種站點對應", audit_log.summary)

    def test_update_fixture_requirement_recalculates_capacity(self) -> None:
        bundle = self.seed_customer_bundle()
        self.production_service.create_model_station(
            ModelStationCreate(
                customer_id=bundle["customer"].id,
                model_id=bundle["model"].id,
                station_id=bundle["station"].id,
            )
        )

        requirement_a = self.production_service.create_fixture_requirement(
            FixtureRequirementCreate(
                customer_id=bundle["customer"].id,
                model_id=bundle["model"].id,
                station_id=bundle["station"].id,
                fixture_id=bundle["fixture_a"].id,
                required_qty=2,
            )
        )
        self.production_service.create_fixture_requirement(
            FixtureRequirementCreate(
                customer_id=bundle["customer"].id,
                model_id=bundle["model"].id,
                station_id=bundle["station"].id,
                fixture_id=bundle["fixture_b"].id,
                required_qty=1,
            )
        )

        capacity_before = self.production_service.get_station_capacity(
            bundle["station"].id,
            bundle["model"].id,
            bundle["customer"].id,
        )
        self.assertEqual(capacity_before["max_open_station_count"], 6)
        self.assertEqual(capacity_before["bottleneck_fixture_code"], "FX-A")

        updated = self.production_service.update_fixture_requirement(
            requirement_a.id,
            FixtureRequirementCreate(
                customer_id=bundle["customer"].id,
                model_id=bundle["model"].id,
                station_id=bundle["station"].id,
                fixture_id=bundle["fixture_a"].id,
                required_qty=3,
            ),
        )
        self.assertEqual(updated.required_qty, 3)

        capacity_after = self.production_service.get_station_capacity(
            bundle["station"].id,
            bundle["model"].id,
            bundle["customer"].id,
        )
        self.assertEqual(capacity_after["max_open_station_count"], 4)
        self.assertEqual(capacity_after["bottleneck_fixture_code"], "FX-A")

    def test_shared_station_keeps_requirements_scoped_by_model(self) -> None:
        bundle = self.seed_customer_bundle()
        second_model = self.repo.create_model(customer_id=bundle["customer"].id, code="M-002", name="Model 2")
        fixture_c = self.repo.create_fixture(
            customer_id=bundle["customer"].id,
            responsible_user_id=None,
            code="FX-C",
            name="Fixture C",
            storage_location=None,
            description=None,
        )
        self.db.add_all(
            [
                FixtureStockLevel(fixture_id=fixture_c.id, min_stock_qty=1, warning_threshold=0, alert_enabled=True),
                FixtureStockSummary(fixture_id=fixture_c.id, stock_qty=20, returned_qty=0, stock_status="normal"),
            ]
        )
        self.db.commit()

        self.production_service.create_model_station(
            ModelStationCreate(
                customer_id=bundle["customer"].id,
                model_id=bundle["model"].id,
                station_id=bundle["station"].id,
            )
        )
        self.production_service.create_model_station(
            ModelStationCreate(
                customer_id=bundle["customer"].id,
                model_id=second_model.id,
                station_id=bundle["station"].id,
            )
        )

        self.production_service.create_fixture_requirement(
            FixtureRequirementCreate(
                customer_id=bundle["customer"].id,
                model_id=bundle["model"].id,
                station_id=bundle["station"].id,
                fixture_id=bundle["fixture_a"].id,
                required_qty=2,
            )
        )
        self.production_service.create_fixture_requirement(
            FixtureRequirementCreate(
                customer_id=bundle["customer"].id,
                model_id=bundle["model"].id,
                station_id=bundle["station"].id,
                fixture_id=bundle["fixture_b"].id,
                required_qty=3,
            )
        )
        self.production_service.create_fixture_requirement(
            FixtureRequirementCreate(
                customer_id=bundle["customer"].id,
                model_id=second_model.id,
                station_id=bundle["station"].id,
                fixture_id=fixture_c.id,
                required_qty=4,
            )
        )

        model_a_capacity = self.production_service.get_station_capacity(
            bundle["station"].id,
            bundle["model"].id,
            bundle["customer"].id,
        )
        model_b_capacity = self.production_service.get_station_capacity(
            bundle["station"].id,
            second_model.id,
            bundle["customer"].id,
        )
        self.assertEqual(model_a_capacity["max_open_station_count"], 3)
        self.assertEqual(model_a_capacity["bottleneck_fixture_code"], "FX-B")
        self.assertEqual(model_b_capacity["max_open_station_count"], 5)
        self.assertEqual(model_b_capacity["bottleneck_fixture_code"], "FX-C")

        model_a_query = self.production_service.get_model_query(
            bundle["model"].id,
            station_id=bundle["station"].id,
            customer_id=bundle["customer"].id,
        )
        model_b_query = self.production_service.get_model_query(
            second_model.id,
            station_id=bundle["station"].id,
            customer_id=bundle["customer"].id,
        )
        self.assertEqual({row["fixture_code"] for row in model_a_query["fixtures"]}, {"FX-A", "FX-B"})
        self.assertEqual({row["fixture_code"] for row in model_b_query["fixtures"]}, {"FX-C"})
        self.assertTrue(all(row["model_code"] == bundle["model"].code for row in model_a_query["station_requirements"]))
        self.assertTrue(all(row["model_code"] == second_model.code for row in model_b_query["station_requirements"]))


class InventoryServiceTests(ServiceTestCase):
    def test_receipt_updates_stock_summary(self) -> None:
        bundle = self.seed_customer_bundle()
        payload = StockTransactionCreate(
            customer_id=bundle["customer"].id,
            created_by="Tester",
            occurred_at=datetime(2026, 6, 9, 8, 30, tzinfo=timezone.utc),
            transaction_no="12005436",
            items=[
                {
                    "fixture_id": bundle["fixture_a"].id,
                    "ownership_type": "self_purchased",
                    "identifier": "202606",
                    "quantity": 5,
                }
            ],
        )

        self.inventory_service.receipt(payload)
        summary = self.db.get(FixtureStockSummary, bundle["fixture_a"].id)
        self.assertIsNotNone(summary)
        self.assertEqual(summary.stock_qty, 17)

        transaction_count = self.db.scalar(select(func.count()).select_from(MaterialTransaction))
        self.assertEqual(transaction_count, 1)
        transaction = self.db.scalar(select(MaterialTransaction).where(MaterialTransaction.customer_id == bundle["customer"].id))
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.transaction_no, "12005436")

    def test_import_transactions_csv_rolls_back_on_invalid_row(self) -> None:
        bundle = self.seed_customer_bundle()
        csv_content = (
            "transaction_type,fixture_code,ownership_type,identifier,quantity,created_by,occurred_at,note\n"
            "receipt,FX-A,self_purchased,202606,5,Tester,2026-06-09T08:30:00+00:00,\n"
            "receipt,NOT-EXIST,self_purchased,202606,5,Tester,2026-06-09T08:30:00+00:00,\n"
        )

        with self.assertRaises(ValueError):
            self.inventory_service.import_transactions_csv(
                bundle["customer"].id,
                "Tester",
                payload=CsvImportPayload(content=csv_content),
        )

        self.db.rollback()
        transaction_count = self.db.scalar(
            select(func.count()).select_from(MaterialTransaction).where(MaterialTransaction.customer_id == bundle["customer"].id)
        )
        summary = self.db.get(FixtureStockSummary, bundle["fixture_a"].id)
        self.assertEqual(transaction_count, 0)
        self.assertIsNotNone(summary)
        self.assertEqual(summary.stock_qty, 12)

    def test_inactive_fixture_is_hidden_from_stock_alert_status(self) -> None:
        bundle = self.seed_customer_bundle()
        fixture_b = bundle["fixture_b"]
        fixture_b.is_active = False
        summary_b = self.db.get(FixtureStockSummary, fixture_b.id)
        self.assertIsNotNone(summary_b)
        summary_b.stock_qty = 0
        summary_b.stock_status = "out_of_stock"
        self.db.commit()

        stock_rows = self.inventory_service.list_stock_summary(customer_id=bundle["customer"].id)
        alerts = self.inventory_service.list_alerts(customer_id=bundle["customer"].id)

        stock_by_code = {row["fixture_code"]: row for row in stock_rows}
        self.assertEqual(stock_by_code["FX-B"]["stock_status"], "normal")
        self.assertNotIn("FX-B", {row["fixture_code"] for row in alerts})


class ProductionApiTests(ServiceTestCase):
    def setUp(self) -> None:
        super().setUp()
        app = FastAPI()
        register_error_handlers(app)
        app.dependency_overrides[get_db] = self._override_get_db
        app.dependency_overrides[auth_get_db] = self._override_get_db
        app.include_router(api_router, prefix=settings.api_v2_prefix)
        self.client = TestClient(app, raise_server_exceptions=False)

        self.admin = self.auth_service.create_user(
            UserCreate(
                username="admin",
                password="admin123",
                display_name="Admin",
                role="admin",
                is_active=True,
            )
        )
        self.token = create_session_token(mode="user", user=self.repo.get_user(self.admin["id"]))

    def tearDown(self) -> None:
        self.client.close()
        super().tearDown()

    def _override_get_db(self):
        try:
            yield self.db
        finally:
            pass

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def test_shared_station_capacity_and_query_are_scoped_by_model(self) -> None:
        bundle = self.seed_customer_bundle()
        second_model = self.repo.create_model(customer_id=bundle["customer"].id, code="M-002", name="Model 2")
        fixture_c = self.repo.create_fixture(
            customer_id=bundle["customer"].id,
            responsible_user_id=None,
            code="FX-C",
            name="Fixture C",
            storage_location=None,
            description=None,
        )
        self.db.add_all(
            [
                FixtureStockLevel(fixture_id=fixture_c.id, min_stock_qty=1, warning_threshold=0, alert_enabled=True),
                FixtureStockSummary(fixture_id=fixture_c.id, stock_qty=20, returned_qty=0, stock_status="normal"),
            ]
        )
        self.db.commit()

        self.production_service.create_model_station(
            ModelStationCreate(
                customer_id=bundle["customer"].id,
                model_id=bundle["model"].id,
                station_id=bundle["station"].id,
            )
        )
        self.production_service.create_model_station(
            ModelStationCreate(
                customer_id=bundle["customer"].id,
                model_id=second_model.id,
                station_id=bundle["station"].id,
            )
        )
        self.production_service.create_fixture_requirement(
            FixtureRequirementCreate(
                customer_id=bundle["customer"].id,
                model_id=bundle["model"].id,
                station_id=bundle["station"].id,
                fixture_id=bundle["fixture_a"].id,
                required_qty=2,
            )
        )
        self.production_service.create_fixture_requirement(
            FixtureRequirementCreate(
                customer_id=bundle["customer"].id,
                model_id=bundle["model"].id,
                station_id=bundle["station"].id,
                fixture_id=bundle["fixture_b"].id,
                required_qty=3,
            )
        )
        self.production_service.create_fixture_requirement(
            FixtureRequirementCreate(
                customer_id=bundle["customer"].id,
                model_id=second_model.id,
                station_id=bundle["station"].id,
                fixture_id=fixture_c.id,
                required_qty=4,
            )
        )

        capacity_a = self.client.get(
            f"/api/v2/production/capacity/stations/{bundle['station'].id}",
            params={"model_id": bundle["model"].id, "customer_id": bundle["customer"].id},
            headers=self._auth_headers(),
        )
        self.assertEqual(capacity_a.status_code, 200)
        self.assertEqual(capacity_a.json()["max_open_station_count"], 3)
        self.assertEqual(capacity_a.json()["bottleneck_fixture_code"], "FX-B")
        self.assertNotIn("current_open_station_count", capacity_a.json())

        capacity_b = self.client.get(
            f"/api/v2/production/capacity/stations/{bundle['station'].id}",
            params={"model_id": second_model.id, "customer_id": bundle["customer"].id},
            headers=self._auth_headers(),
        )
        self.assertEqual(capacity_b.status_code, 200)
        self.assertEqual(capacity_b.json()["max_open_station_count"], 5)
        self.assertEqual(capacity_b.json()["bottleneck_fixture_code"], "FX-C")

        query_a = self.client.get(
            f"/api/v2/production/models/{bundle['model'].id}/query",
            params={"station_id": bundle["station"].id, "customer_id": bundle["customer"].id},
            headers=self._auth_headers(),
        )
        self.assertEqual(query_a.status_code, 200)
        self.assertEqual({row["fixture_code"] for row in query_a.json()["fixtures"]}, {"FX-A", "FX-B"})

        query_b = self.client.get(
            f"/api/v2/production/models/{second_model.id}/query",
            params={"station_id": bundle["station"].id, "customer_id": bundle["customer"].id},
            headers=self._auth_headers(),
        )
        self.assertEqual(query_b.status_code, 200)
        self.assertEqual({row["fixture_code"] for row in query_b.json()["fixtures"]}, {"FX-C"})

    def test_non_admin_customer_scope_blocks_unassigned_customer(self) -> None:
        customer_a = self.repo.create_customer(code="C-001", name="Customer 1")
        customer_b = self.repo.create_customer(code="C-002", name="Customer 2")
        self.db.commit()
        scoped_user = self.auth_service.create_user(
            UserCreate(
                username="scoped",
                password="secret123",
                display_name="Scoped User",
                role="user",
                is_active=True,
                allowed_customer_ids=[],
            )
        )
        self.repo.replace_allowed_users_for_customer(customer_a.id, [scoped_user["id"]])
        self.db.commit()
        token = create_session_token(mode="user", user=self.repo.get_user(scoped_user["id"]))
        headers = {"Authorization": f"Bearer {token}"}

        customers_response = self.client.get("/api/v2/master/customers", headers=headers)
        self.assertEqual(customers_response.status_code, 200)
        self.assertEqual([row["id"] for row in customers_response.json()], [customer_a.id])

        allowed_stock = self.client.get("/api/v2/inventory/stock", params={"customer_id": customer_a.id}, headers=headers)
        self.assertEqual(allowed_stock.status_code, 200)

        forbidden_stock = self.client.get("/api/v2/inventory/stock", params={"customer_id": customer_b.id}, headers=headers)
        self.assertEqual(forbidden_stock.status_code, 403)

        missing_scope = self.client.get("/api/v2/inventory/stock", headers=headers)
        self.assertEqual(missing_scope.status_code, 403)


if __name__ == "__main__":
    unittest.main()
