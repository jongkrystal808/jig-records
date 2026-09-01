from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import sessionmaker

from backend.app.core.auth import SessionContext, _get_db as auth_get_db, create_session_token, require_permission
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.errors import register_error_handlers
from backend.app.models import Base
from backend.app.models.audit import AuditLog
from backend.app.models.inventory import FixtureStockLevel, FixtureStockSummary, MaterialTransaction, MaterialTransactionItem
from backend.app.models.production import FixtureRequirement, MachineCapacitySummary
from backend.app.routers import api_router
from backend.app.repositories.master_repository import MasterRepository
from backend.app.schemas.common import CsvImportPayload
from backend.app.schemas.auth import UserCreate, UserUpdate
from backend.app.schemas.inventory import StockTransactionCreate
from backend.app.schemas.master import FixtureCreate, FixtureUpdate
from backend.app.schemas.production import FixtureRequirementCopy, FixtureRequirementCreate, ModelStationCreate
from backend.app.services.auth_service import AuthService
from backend.app.services.inventory_service import DuplicateTransactionError, InventoryService
from backend.app.services.master_service import MasterService
from backend.app.services.production_service import ProductionService
from backend.app.services.search_service import SearchService
from backend.app.utils.fixture_images import resolve_fixture_image_path, save_fixture_image


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

    def ensure_transaction_actor(self) -> SessionContext:
        if hasattr(self, "transaction_actor"):
            return self.transaction_actor
        user = self.repo.create_user(
            username="test-operator",
            email=None,
            password_hash="test-hash",
            display_name="Tester",
            role="user",
            is_active=True,
        )
        self.db.commit()
        self.transaction_actor = SessionContext(
            mode="user",
            user_id=user.id,
            username=user.username,
            display_name=user.display_name,
            role=user.role,
            issued_at=0,
            expires_at=9999999999,
        )
        self.inventory_service = InventoryService(self.db, actor=self.transaction_actor)
        return self.transaction_actor

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()
        self.db_path.unlink(missing_ok=True)

    def seed_customer_bundle(self):
        self.ensure_transaction_actor()
        customer = self.repo.create_customer(code="C-001", name="Customer 1")
        model = self.repo.create_model(customer_id=customer.id, code="M-001", name="Model 1")
        station = self.repo.create_station(customer_id=customer.id, code="ST-001", name="Station 1")
        fixture_a = self.repo.create_fixture(
            customer_id=customer.id,
            responsible_user_id=None,
            code="FX-A",
            name="Fixture A",
            line_storage_location=None,
            department_storage_location=None,
            description=None,
        )
        fixture_b = self.repo.create_fixture(
            customer_id=customer.id,
            responsible_user_id=None,
            code="FX-B",
            name="Fixture B",
            line_storage_location=None,
            department_storage_location=None,
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
                email="alice@example.com",
                password="secret123",
                display_name="Alice",
                role="user",
                is_active=True,
                allowed_customer_ids=[customer.id],
            )
        )

        logged_in = self.auth_service.login("alice", "secret123")
        self.assertEqual(logged_in.id, created["id"])
        self.assertEqual(logged_in.display_name, "Alice")
        self.assertEqual(created["email"], "alice@example.com")
        self.assertEqual(created["allowed_customer_ids"], [customer.id])
        self.assertEqual(
            created["allowed_customers"],
            [{"id": customer.id, "code": "C-001", "name": "Customer 1"}],
        )

        audit_log = self.db.scalar(select(AuditLog).where(AuditLog.entity_type == "user"))
        self.assertIsNotNone(audit_log)
        self.assertIn("建立使用者", audit_log.summary)

        with self.assertRaises(ValueError):
            self.auth_service.login("alice", "wrong-password")

    def test_non_admin_user_can_be_created_before_customer_assignment(self) -> None:
        created = self.auth_service.create_user(
            UserCreate(
                username="bob",
                email=None,
                password="secret123",
                display_name="Bob",
                role="user",
                is_active=True,
                allowed_customer_ids=[],
            )
        )
        self.assertEqual(created["allowed_customer_ids"], [])

    def test_update_user_email(self) -> None:
        customer = self.repo.create_customer(code="C-002", name="Customer 2")
        self.db.commit()
        created = self.auth_service.create_user(
            UserCreate(
                username="carol",
                email=None,
                password="secret123",
                display_name="Carol",
                role="user",
                is_active=True,
                allowed_customer_ids=[customer.id],
            )
        )

        updated = self.auth_service.update_user(
            created["id"],
            UserUpdate(
                email="carol@example.com",
                display_name="Carol Chen",
                role="user",
                is_active=True,
            ),
        )

        self.assertEqual(updated["email"], "carol@example.com")
        self.assertEqual(updated["display_name"], "Carol Chen")
        self.assertEqual(updated["allowed_customer_ids"], [customer.id])

    def test_admin_customer_assignment_is_not_discarded(self) -> None:
        customer = self.repo.create_customer(code="C-003", name="Customer 3")
        self.db.commit()

        created = self.auth_service.create_user(
            UserCreate(
                username="scoped-admin",
                email=None,
                password="secret123",
                display_name="Scoped Admin",
                role="admin",
                is_active=True,
                allowed_customer_ids=[customer.id],
            )
        )

        self.assertEqual(created["allowed_customer_ids"], [customer.id])

    def test_last_active_super_admin_cannot_be_demoted(self) -> None:
        first = self.auth_service.create_user(
            UserCreate(
                username="root-one",
                password="secret123",
                display_name="Root One",
                role="super_admin",
                is_active=True,
                allowed_customer_ids=[],
            )
        )
        with self.assertRaisesRegex(ValueError, "至少必須保留一位"):
            self.auth_service.update_user(
                first["id"],
                UserUpdate(display_name="Root One", role="admin", is_active=True),
            )

        self.auth_service.create_user(
            UserCreate(
                username="root-two",
                password="secret123",
                display_name="Root Two",
                role="super_admin",
                is_active=True,
                allowed_customer_ids=[],
            )
        )
        updated = self.auth_service.update_user(
            first["id"],
            UserUpdate(display_name="Root One", role="admin", is_active=True),
        )
        self.assertEqual(updated["role"], "admin")

    def test_role_permissions_distinguish_admin_and_super_admin_management(self) -> None:
        write_guard = require_permission("write")
        manage_guard = require_permission("manage")
        super_manage_guard = require_permission("super_manage")

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

        for illegal_role in ("guest", "manager"):
            with self.subTest(illegal_role=illegal_role), self.assertRaises(HTTPException) as illegal_role_exc:
                write_guard(
                    session=SessionContext(
                        mode="user",
                        user_id=2,
                        username="invalid-role-user",
                        display_name="Invalid Role User",
                        role=illegal_role,
                        issued_at=0,
                        expires_at=9999999999,
                    )
                )
            self.assertEqual(illegal_role_exc.exception.status_code, 403)

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

        with self.assertRaises(HTTPException) as super_manage_exc:
            super_manage_guard(session=allowed)
        self.assertEqual(super_manage_exc.exception.status_code, 403)

        super_admin = SessionContext(
            mode="user",
            user_id=3,
            username="root-admin",
            display_name="Root Admin",
            role="super_admin",
            issued_at=0,
            expires_at=9999999999,
        )
        self.assertEqual(write_guard(session=super_admin).role, "super_admin")
        self.assertEqual(manage_guard(session=super_admin).role, "super_admin")
        self.assertEqual(super_manage_guard(session=super_admin).role, "super_admin")


class SearchServiceTests(ServiceTestCase):
    def test_fixture_and_identifier_search_modes_do_not_override_each_other(self) -> None:
        bundle = self.seed_customer_bundle()
        direct_fixture = self.repo.create_fixture(
            customer_id=bundle["customer"].id,
            responsible_user_id=None,
            code="2204",
            name="Fixture code 2204",
            line_storage_location=None,
            department_storage_location=None,
            description=None,
        )
        self.db.add(
            FixtureStockSummary(
                fixture_id=direct_fixture.id,
                stock_qty=3,
                returned_qty=0,
                stock_status="normal",
            )
        )
        transaction = MaterialTransaction(
            customer_id=bundle["customer"].id,
            transaction_type="receipt",
            transaction_no="SEARCH-IDENTIFIER-001",
            occurred_at=datetime.now(timezone.utc),
            created_by="Search Test",
            note=None,
        )
        transaction.items.append(
            MaterialTransactionItem(
                fixture_id=bundle["fixture_b"].id,
                ownership_type="customer_supplied",
                identifier="2204",
                quantity=1,
                note=None,
            )
        )
        self.db.add(transaction)
        self.db.commit()

        service = SearchService(self.db)
        fixture_result = service.global_search(
            "2204",
            customer_id=bundle["customer"].id,
            entity_type="fixture",
            fixture_search_mode="fixture",
        )
        identifier_result = service.global_search(
            "2204",
            customer_id=bundle["customer"].id,
            entity_type="fixture",
            fixture_search_mode="identifier",
        )

        self.assertEqual([row["reference_id"] for row in fixture_result["items"]], [direct_fixture.id])
        self.assertEqual(fixture_result["items"][0]["matched_identifier"], None)
        self.assertEqual([row["reference_id"] for row in identifier_result["items"]], [bundle["fixture_b"].id])
        self.assertEqual(identifier_result["items"][0]["matched_identifier"], "2204")


class MasterServiceTests(ServiceTestCase):
    def test_fixture_code_uniqueness_lookup_is_case_insensitive(self) -> None:
        customer_a = self.repo.create_customer(code="C-UNIQUE-A", name="Unique Customer A")
        customer_b = self.repo.create_customer(code="C-UNIQUE-B", name="Unique Customer B")
        self.repo.create_fixture(
            customer_id=customer_a.id,
            responsible_user_id=None,
            code="ONLY-ONE",
            name="Unique Fixture",
            description=None,
        )
        self.repo.create_fixture(
            customer_id=customer_a.id,
            responsible_user_id=None,
            code="SHARED",
            name="Shared Fixture A",
            description=None,
        )
        self.repo.create_fixture(
            customer_id=customer_b.id,
            responsible_user_id=None,
            code="shared",
            name="Shared Fixture B",
            description=None,
        )
        self.db.commit()

        result = self.master_service.repo.list_globally_unique_fixture_codes(
            ["ONLY-ONE", "SHARED"]
        )

        self.assertEqual(result, {"ONLY-ONE"})

    def test_legacy_flat_image_is_not_shared_when_fixture_code_is_duplicated(self) -> None:
        original_image_dir = settings.fixture_image_dir
        with tempfile.TemporaryDirectory() as image_dir:
            object.__setattr__(settings, "fixture_image_dir", image_dir)
            try:
                customer_a = self.repo.create_customer(code="C-IMG-A", name="Image Customer A")
                customer_b = self.repo.create_customer(code="C-IMG-B", name="Image Customer B")
                fixture_a = self.repo.create_fixture(
                    customer_id=customer_a.id,
                    responsible_user_id=None,
                    code="SHARED",
                    name="Fixture A",
                    description=None,
                )
                self.repo.create_fixture(
                    customer_id=customer_b.id,
                    responsible_user_id=None,
                    code="SHARED",
                    name="Fixture B",
                    description=None,
                )
                self.db.commit()
                Path(image_dir, "SHARED.png").write_bytes(b"legacy")

                self.assertIsNone(
                    self.master_service.get_fixture_image_path("SHARED", customer_id=customer_a.id)
                )
                self.assertIsNone(
                    self.master_service.get_fixture_image_path("SHARED", customer_id=customer_b.id)
                )
                self.master_service.delete_fixture(
                    fixture_a.id,
                    customer_id=customer_a.id,
                    delete_transactions=False,
                )
                self.assertFalse(Path(image_dir, "SHARED.png").exists())
                self.assertIsNone(
                    self.master_service.get_fixture_image_path("SHARED", customer_id=customer_b.id)
                )
            finally:
                object.__setattr__(settings, "fixture_image_dir", original_image_dir)

    def test_fixture_image_rename_is_rolled_back_when_database_commit_fails(self) -> None:
        original_image_dir = settings.fixture_image_dir
        with tempfile.TemporaryDirectory() as image_dir:
            object.__setattr__(settings, "fixture_image_dir", image_dir)
            try:
                customer = self.repo.create_customer(code="C-IMG", name="Image Customer")
                fixture = self.repo.create_fixture(
                    customer_id=customer.id,
                    responsible_user_id=None,
                    code="FX-OLD",
                    name="Fixture Image",
                    description=None,
                )
                self.db.commit()
                save_fixture_image(customer.id, fixture.code, b"image", content_type="image/png")

                with patch.object(self.db, "commit", side_effect=RuntimeError("commit failed")):
                    with self.assertRaisesRegex(RuntimeError, "commit failed"):
                        self.master_service.update_fixture(
                            fixture.id,
                            FixtureUpdate(
                                customer_id=customer.id,
                                code="FX-NEW",
                                name="Fixture Image",
                                is_active=True,
                            ),
                        )

                self.assertIsNotNone(resolve_fixture_image_path(customer.id, "FX-OLD"))
                self.assertIsNone(resolve_fixture_image_path(customer.id, "FX-NEW"))
                self.assertEqual(self.repo.get_fixture(fixture.id).code, "FX-OLD")
            finally:
                object.__setattr__(settings, "fixture_image_dir", original_image_dir)

    def test_fixture_department_storage_location_is_preserved_when_line_is_empty(self) -> None:
        customer = self.repo.create_customer(code="C-DEP", name="Department Storage Customer")
        self.db.commit()

        created = self.master_service.create_fixture(
            FixtureCreate(
                customer_id=customer.id,
                code="FX-DEP",
                name="Fixture Department Only",
                line_storage_location=None,
                department_storage_location="RD-SHELF-9",
                min_stock_qty=1,
            )
        )

        self.assertIsNone(created["line_storage_location"])
        self.assertEqual(created["department_storage_location"], "RD-SHELF-9")

        updated = self.master_service.update_fixture(
            created["id"],
            FixtureUpdate(
                customer_id=customer.id,
                code="FX-DEP",
                name="Fixture Department Only",
                line_storage_location=None,
                department_storage_location="RD-SHELF-10",
                min_stock_qty=1,
                is_active=True,
            ),
        )

        self.assertIsNone(updated["line_storage_location"])
        self.assertEqual(updated["department_storage_location"], "RD-SHELF-10")

    def test_delete_fixture_preserves_transaction_history_snapshot(self) -> None:
        bundle = self.seed_customer_bundle()
        fixture_id = bundle["fixture_a"].id
        customer_id = bundle["customer"].id
        self.production_service.create_model_station(
            ModelStationCreate(
                customer_id=customer_id,
                model_id=bundle["model"].id,
                station_id=bundle["station"].id,
            )
        )
        self.production_service.create_fixture_requirement(
            FixtureRequirementCreate(
                customer_id=customer_id,
                model_id=bundle["model"].id,
                station_id=bundle["station"].id,
                fixture_id=fixture_id,
                required_qty=2,
            )
        )
        self.inventory_service.receipt(
            StockTransactionCreate(
                customer_id=customer_id,
                created_by="Admin",
                transaction_no="DELETE-KEEP-001",
                items=[
                    {
                        "fixture_id": fixture_id,
                        "ownership_type": "self_purchased",
                        "identifier": "1",
                        "quantity": 3,
                    },
                    {
                        "fixture_id": bundle["fixture_b"].id,
                        "ownership_type": "customer_supplied",
                        "identifier": "2",
                        "quantity": 4,
                    },
                ],
            )
        )

        result = self.master_service.delete_fixture(
            fixture_id,
            customer_id=customer_id,
            delete_transactions=False,
        )

        self.assertIsNone(self.repo.get_fixture(fixture_id))
        self.assertFalse(result["transaction_records_deleted"])
        self.assertEqual(result["transaction_item_count"], 1)
        self.assertEqual(result["deleted_requirement_count"], 1)
        self.assertEqual(
            self.db.scalar(
                select(func.count(FixtureRequirement.id)).where(FixtureRequirement.fixture_id == fixture_id)
            ),
            0,
        )

        transaction = next(
            row
            for row in self.inventory_service.list_transactions(limit=50, customer_id=customer_id)
            if row["transaction_no"] == "DELETE-KEEP-001"
        )
        deleted_item = next(item for item in transaction["items"] if item["fixture_code"] == "FX-A")
        self.assertIsNone(deleted_item["fixture_id"])
        self.assertEqual(deleted_item["fixture_name"], "Fixture A")
        self.assertEqual(
            next(item for item in transaction["items"] if item["fixture_code"] == "FX-B")["fixture_id"],
            bundle["fixture_b"].id,
        )
        export_rows = self.inventory_service.repo.list_transaction_item_rows(
            customer_id=customer_id,
            transaction_no="DELETE-KEEP-001",
        )
        export_deleted_item = next(row for row in export_rows if row["fixture_code"] == "FX-A")
        self.assertIsNone(export_deleted_item["fixture_id"])
        self.assertEqual(export_deleted_item["fixture_name"], "Fixture A")
        self.inventory_service.recalculate_inventory_state(customer_id=customer_id)

        replacement = self.master_service.create_fixture(
            FixtureCreate(customer_id=customer_id, code="FX-A", name="Fixture A Replacement")
        )
        self.assertNotEqual(replacement["id"], fixture_id)

    def test_delete_fixture_can_remove_only_its_transaction_items(self) -> None:
        bundle = self.seed_customer_bundle()
        fixture_id = bundle["fixture_a"].id
        customer_id = bundle["customer"].id
        self.inventory_service.receipt(
            StockTransactionCreate(
                customer_id=customer_id,
                created_by="Admin",
                transaction_no="DELETE-ONLY-001",
                items=[
                    {
                        "fixture_id": fixture_id,
                        "ownership_type": "self_purchased",
                        "identifier": "1",
                        "quantity": 2,
                    }
                ],
            )
        )
        self.inventory_service.receipt(
            StockTransactionCreate(
                customer_id=customer_id,
                created_by="Admin",
                transaction_no="DELETE-MIXED-001",
                items=[
                    {
                        "fixture_id": fixture_id,
                        "ownership_type": "self_purchased",
                        "identifier": "2",
                        "quantity": 1,
                    },
                    {
                        "fixture_id": bundle["fixture_b"].id,
                        "ownership_type": "customer_supplied",
                        "identifier": "3",
                        "quantity": 1,
                    },
                ],
            )
        )

        result = self.master_service.delete_fixture(
            fixture_id,
            customer_id=customer_id,
            delete_transactions=True,
        )

        self.assertTrue(result["transaction_records_deleted"])
        self.assertEqual(result["transaction_item_count"], 2)
        self.assertEqual(result["deleted_transaction_count"], 1)
        transaction_rows = self.inventory_service.list_transactions(limit=50, customer_id=customer_id)
        self.assertNotIn("DELETE-ONLY-001", {row["transaction_no"] for row in transaction_rows})
        mixed = next(row for row in transaction_rows if row["transaction_no"] == "DELETE-MIXED-001")
        self.assertEqual([item["fixture_code"] for item in mixed["items"]], ["FX-B"])
        self.assertEqual(
            self.db.scalar(
                select(func.count(MaterialTransactionItem.id)).where(MaterialTransactionItem.fixture_id == fixture_id)
            ),
            0,
        )

    def test_delete_model_removes_related_mapping_and_requirements(self) -> None:
        bundle = self.seed_customer_bundle()
        customer_id = bundle["customer"].id
        self.production_service.create_model_station(
            ModelStationCreate(
                customer_id=customer_id,
                model_id=bundle["model"].id,
                station_id=bundle["station"].id,
            )
        )
        self.production_service.create_fixture_requirement(
            FixtureRequirementCreate(
                customer_id=customer_id,
                model_id=bundle["model"].id,
                station_id=bundle["station"].id,
                fixture_id=bundle["fixture_a"].id,
                required_qty=2,
            )
        )
        self.db.add(MachineCapacitySummary(station_id=bundle["station"].id, max_open_station_count=4, bottleneck_fixture_code="FX-A"))
        self.db.commit()

        result = self.master_service.delete_model(bundle["model"].id, customer_id=customer_id)

        self.assertEqual(result.model_code, "M-001")
        self.assertEqual(result.deleted_model_station_count, 1)
        self.assertEqual(result.deleted_requirement_count, 1)
        self.assertEqual(result.deleted_capacity_summary_count, 1)
        self.assertIsNone(self.repo.get_model(bundle["model"].id, customer_id=customer_id))

    def test_delete_station_removes_related_mapping_and_requirements(self) -> None:
        bundle = self.seed_customer_bundle()
        customer_id = bundle["customer"].id
        self.production_service.create_model_station(
            ModelStationCreate(
                customer_id=customer_id,
                model_id=bundle["model"].id,
                station_id=bundle["station"].id,
            )
        )
        self.production_service.create_fixture_requirement(
            FixtureRequirementCreate(
                customer_id=customer_id,
                model_id=bundle["model"].id,
                station_id=bundle["station"].id,
                fixture_id=bundle["fixture_a"].id,
                required_qty=1,
            )
        )
        self.db.add(MachineCapacitySummary(station_id=bundle["station"].id, max_open_station_count=3, bottleneck_fixture_code="FX-A"))
        self.db.commit()

        result = self.master_service.delete_station(bundle["station"].id, customer_id=customer_id)

        self.assertEqual(result.station_code, "ST-001")
        self.assertEqual(result.deleted_model_station_count, 1)
        self.assertEqual(result.deleted_requirement_count, 1)
        self.assertEqual(result.deleted_capacity_summary_count, 1)
        self.assertIsNone(self.repo.get_station(bundle["station"].id, customer_id=customer_id))

    def test_fixture_quality_report_flags_expected_issues(self) -> None:
        original_image_dir = settings.fixture_image_dir
        with tempfile.TemporaryDirectory() as image_dir:
            object.__setattr__(settings, "fixture_image_dir", image_dir)
            try:
                customer = self.repo.create_customer(code="C-QLT", name="Quality Customer")
                model = self.repo.create_model(customer_id=customer.id, code="M-QLT", name="Quality Model")
                station = self.repo.create_station(customer_id=customer.id, code="ST-QLT", name="Quality Station")
                fixture_good = self.repo.create_fixture(
                    customer_id=customer.id,
                    responsible_user_id=None,
                    code="FX-GOOD",
                    name="Fixture Good",
                    line_storage_location="A-01-01",
                    department_storage_location=None,
                    description=None,
                )
                fixture_bad = self.repo.create_fixture(
                    customer_id=customer.id,
                    responsible_user_id=None,
                    code="FX-BAD",
                    name="",
                    line_storage_location=None,
                    department_storage_location=None,
                    description=None,
                )
                fixture_department_only = self.repo.create_fixture(
                    customer_id=customer.id,
                    responsible_user_id=None,
                    code="FX-DEP",
                    name="Fixture Department",
                    line_storage_location=None,
                    department_storage_location="RD-SHELF-9",
                    description=None,
                )
                self.db.commit()

                Path(image_dir, "FX-GOOD.png").write_bytes(b"fixture-image")
                Path(image_dir, "FX-DEP.png").write_bytes(b"fixture-image")
                self.production_service.create_model_station(
                    ModelStationCreate(customer_id=customer.id, model_id=model.id, station_id=station.id)
                )
                self.production_service.create_fixture_requirement(
                    FixtureRequirementCreate(
                        customer_id=customer.id,
                        model_id=model.id,
                        station_id=station.id,
                        fixture_id=fixture_good.id,
                        required_qty=1,
                    )
                )
                self.production_service.create_fixture_requirement(
                    FixtureRequirementCreate(
                        customer_id=customer.id,
                        model_id=model.id,
                        station_id=station.id,
                        fixture_id=fixture_department_only.id,
                        required_qty=1,
                    )
                )
                self.ensure_transaction_actor()
                self.inventory_service.receipt(
                    StockTransactionCreate(
                        customer_id=customer.id,
                        created_by="Tester",
                        transaction_no="QLT-0001",
                        items=[
                            {
                                "fixture_id": fixture_good.id,
                                "ownership_type": "self_purchased",
                                "identifier": "1",
                                "quantity": 4,
                            },
                            {
                                "fixture_id": fixture_bad.id,
                                "ownership_type": "self_purchased",
                                "identifier": "2",
                                "quantity": 3,
                            },
                            {
                                "fixture_id": fixture_department_only.id,
                                "ownership_type": "self_purchased",
                                "identifier": "3",
                                "quantity": 2,
                            },
                        ],
                    )
                )

                good_level = self.inventory_service.repo.get_or_create_stock_level(fixture_good.id)
                good_level.min_stock_qty = 2
                bad_level = self.inventory_service.repo.get_or_create_stock_level(fixture_bad.id)
                bad_level.min_stock_qty = 0
                department_only_level = self.inventory_service.repo.get_or_create_stock_level(fixture_department_only.id)
                department_only_level.min_stock_qty = 1
                bad_summary = self.db.get(FixtureStockSummary, fixture_bad.id)
                self.assertIsNotNone(bad_summary)
                bad_summary.stock_qty = 5
                self.db.commit()

                report = self.master_service.build_fixture_quality_report(customer.id)

                self.assertEqual(report.total_fixture_count, 3)
                self.assertEqual(report.problematic_fixture_count, 1)
                self.assertEqual(report.missing_name_count, 1)
                self.assertEqual(report.missing_storage_location_count, 1)
                self.assertEqual(report.missing_image_count, 1)
                self.assertEqual(report.missing_min_stock_qty_count, 1)
                self.assertEqual(report.missing_model_relation_count, 1)
                self.assertEqual(report.stock_mismatch_count, 1)
                self.assertEqual([row.fixture_code for row in report.rows], ["FX-BAD"])
                self.assertEqual(
                    set(report.rows[0].issue_codes),
                    {
                        "missing_name",
                        "missing_storage_location",
                        "missing_image",
                        "missing_min_stock_qty",
                        "missing_model_relation",
                        "stock_mismatch",
                    },
                )
            finally:
                object.__setattr__(settings, "fixture_image_dir", original_image_dir)


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
    def test_model_query_uses_constant_query_count_for_many_requirements(self) -> None:
        bundle = self.seed_customer_bundle()
        self.production_service.create_model_station(
            ModelStationCreate(
                customer_id=bundle["customer"].id,
                model_id=bundle["model"].id,
                station_id=bundle["station"].id,
            )
        )
        fixtures = []
        for index in range(25):
            fixture = self.repo.create_fixture(
                customer_id=bundle["customer"].id,
                responsible_user_id=None,
                code=f"PERF-{index:03d}",
                name=f"Performance Fixture {index}",
                line_storage_location=None,
                department_storage_location=None,
                description=None,
            )
            fixtures.append(fixture)
            self.db.add_all(
                [
                    FixtureStockLevel(
                        fixture_id=fixture.id,
                        min_stock_qty=1,
                        warning_threshold=0,
                        alert_enabled=True,
                    ),
                    FixtureStockSummary(
                        fixture_id=fixture.id,
                        stock_qty=10,
                        returned_qty=0,
                        stock_status="normal",
                    ),
                    FixtureRequirement(
                        model_id=bundle["model"].id,
                        station_id=bundle["station"].id,
                        fixture_id=fixture.id,
                        required_qty=1,
                    ),
                ]
            )
        self.db.commit()
        model_id = bundle["model"].id
        customer_id = bundle["customer"].id
        statement_count = 0

        def count_statement(*_args) -> None:
            nonlocal statement_count
            statement_count += 1

        event.listen(self.engine, "before_cursor_execute", count_statement)
        try:
            result = self.production_service.get_model_query(
                model_id,
                customer_id=customer_id,
            )
        finally:
            event.remove(self.engine, "before_cursor_execute", count_statement)

        self.assertEqual(result["fixture_type_count"], len(fixtures))
        self.assertLessEqual(statement_count, 5)

    def test_designated_requirement_uses_only_selected_identifier_stock(self) -> None:
        bundle = self.seed_customer_bundle()
        self.inventory_service.receipt(
            StockTransactionCreate(
                customer_id=bundle["customer"].id,
                created_by="Admin",
                transaction_no="DESIGNATED-001",
                items=[
                    {
                        "fixture_id": bundle["fixture_a"].id,
                        "ownership_type": "self_purchased",
                        "identifier": "1",
                        "quantity": 3,
                    },
                    {
                        "fixture_id": bundle["fixture_a"].id,
                        "ownership_type": "self_purchased",
                        "identifier": "2",
                        "quantity": 8,
                    },
                ],
            )
        )

        requirement = self.production_service.create_fixture_requirement(
            FixtureRequirementCreate(
                customer_id=bundle["customer"].id,
                model_id=bundle["model"].id,
                station_id=bundle["station"].id,
                fixture_id=bundle["fixture_a"].id,
                required_qty=2,
                designated_mode=True,
                designated_identifiers=["1"],
            )
        )

        self.assertTrue(requirement.designated_mode)
        self.assertEqual(requirement.designated_identifiers, ["0001"])
        capacity = self.production_service.get_station_capacity(
            bundle["station"].id,
            bundle["model"].id,
            bundle["customer"].id,
        )
        self.assertEqual(capacity["max_open_station_count"], 1)
        listed = self.production_service.list_fixture_requirements(bundle["customer"].id)
        self.assertEqual(listed[0]["designated_identifiers"], ["0001"])
        model_query = self.production_service.get_model_query(
            bundle["model"].id,
            customer_id=bundle["customer"].id,
        )
        query_requirement = model_query["station_requirements"][0]
        self.assertTrue(query_requirement["designated_mode"])
        self.assertEqual(query_requirement["designated_identifiers"], ["0001"])
        self.assertEqual(query_requirement["stock_qty"], 3)
        self.assertEqual(query_requirement["max_open_station_count"], 1)

        preserved = self.production_service.update_fixture_requirement(
            requirement.id,
            FixtureRequirementCreate(
                customer_id=bundle["customer"].id,
                model_id=bundle["model"].id,
                station_id=bundle["station"].id,
                fixture_id=bundle["fixture_a"].id,
                required_qty=3,
            ),
        )
        self.assertTrue(preserved.designated_mode)
        self.assertEqual(preserved.designated_identifiers, ["0001"])

        with self.assertRaisesRegex(ValueError, "無可用庫存"):
            self.production_service.update_fixture_requirement(
                requirement.id,
                FixtureRequirementCreate(
                    customer_id=bundle["customer"].id,
                    model_id=bundle["model"].id,
                    station_id=bundle["station"].id,
                    fixture_id=bundle["fixture_a"].id,
                    required_qty=2,
                    designated_mode=True,
                    designated_identifiers=["9999"],
                ),
            )

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

    def test_create_fixture_requirement_auto_creates_model_station_mapping(self) -> None:
        bundle = self.seed_customer_bundle()

        created = self.production_service.create_fixture_requirement(
            FixtureRequirementCreate(
                customer_id=bundle["customer"].id,
                model_id=bundle["model"].id,
                station_id=bundle["station"].id,
                fixture_id=bundle["fixture_a"].id,
                required_qty=2,
            )
        )

        self.assertEqual(created.model_id, bundle["model"].id)
        self.assertEqual(created.station_id, bundle["station"].id)
        self.assertIsNotNone(
            self.production_service.repo.get_model_station(
                bundle["model"].id,
                bundle["station"].id,
                customer_id=bundle["customer"].id,
            )
        )

        capacity = self.production_service.get_station_capacity(
            bundle["station"].id,
            bundle["model"].id,
            bundle["customer"].id,
        )
        self.assertEqual(capacity["max_open_station_count"], 6)
        self.assertEqual(capacity["bottleneck_fixture_code"], "FX-A")

    def test_copy_fixture_requirements_is_safe_by_default_and_can_overwrite(self) -> None:
        bundle = self.seed_customer_bundle()
        target_station = self.repo.create_station(
            customer_id=bundle["customer"].id,
            code="ST-002",
            name="Station 2",
        )
        self.db.commit()
        self.production_service.create_model_station(
            ModelStationCreate(
                customer_id=bundle["customer"].id,
                model_id=bundle["model"].id,
                station_id=bundle["station"].id,
            )
        )
        for fixture, required_qty in (
            (bundle["fixture_a"], 2),
            (bundle["fixture_b"], 3),
        ):
            self.production_service.create_fixture_requirement(
                FixtureRequirementCreate(
                    customer_id=bundle["customer"].id,
                    model_id=bundle["model"].id,
                    station_id=bundle["station"].id,
                    fixture_id=fixture.id,
                    required_qty=required_qty,
                )
            )
        self.production_service.create_fixture_requirement(
            FixtureRequirementCreate(
                customer_id=bundle["customer"].id,
                model_id=bundle["model"].id,
                station_id=target_station.id,
                fixture_id=bundle["fixture_a"].id,
                required_qty=5,
            )
        )

        safe_result = self.production_service.copy_fixture_requirements(
            FixtureRequirementCopy(
                customer_id=bundle["customer"].id,
                source_model_id=bundle["model"].id,
                source_station_id=bundle["station"].id,
                target_model_id=bundle["model"].id,
                target_station_id=target_station.id,
            )
        )
        self.assertEqual(
            safe_result,
            {
                "source_requirement_count": 2,
                "created_count": 1,
                "updated_count": 0,
                "skipped_count": 1,
                "mapping_created": False,
            },
        )
        target_rows = self.production_service.repo.list_station_requirements(
            target_station.id,
            model_id=bundle["model"].id,
            customer_id=bundle["customer"].id,
        )
        self.assertEqual(
            {row.fixture_id: row.required_qty for row in target_rows},
            {
                bundle["fixture_a"].id: 5,
                bundle["fixture_b"].id: 3,
            },
        )

        overwrite_result = self.production_service.copy_fixture_requirements(
            FixtureRequirementCopy(
                customer_id=bundle["customer"].id,
                source_model_id=bundle["model"].id,
                source_station_id=bundle["station"].id,
                target_model_id=bundle["model"].id,
                target_station_id=target_station.id,
                overwrite_existing=True,
            )
        )
        self.assertEqual(overwrite_result["updated_count"], 1)
        self.assertEqual(overwrite_result["skipped_count"], 1)
        target_rows = self.production_service.repo.list_station_requirements(
            target_station.id,
            model_id=bundle["model"].id,
            customer_id=bundle["customer"].id,
        )
        self.assertEqual(
            {row.fixture_id: row.required_qty for row in target_rows},
            {
                bundle["fixture_a"].id: 2,
                bundle["fixture_b"].id: 3,
            },
        )
        audit_log = self.db.scalar(
            select(AuditLog)
            .where(AuditLog.entity_type == "fixture_requirement", AuditLog.action == "copy")
            .order_by(AuditLog.id.desc())
        )
        self.assertIsNotNone(audit_log)
        self.assertIn("ST-001", audit_log.summary)
        self.assertIn("ST-002", audit_log.summary)

    def test_shared_station_keeps_requirements_scoped_by_model(self) -> None:
        bundle = self.seed_customer_bundle()
        second_model = self.repo.create_model(customer_id=bundle["customer"].id, code="M-002", name="Model 2")
        fixture_c = self.repo.create_fixture(
            customer_id=bundle["customer"].id,
            responsible_user_id=None,
            code="FX-C",
            name="Fixture C",
            line_storage_location=None,
            department_storage_location=None,
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

    def test_model_query_uses_lowest_station_capacity_for_summary(self) -> None:
        bundle = self.seed_customer_bundle()
        second_station = self.repo.create_station(customer_id=bundle["customer"].id, code="ST-002", name="Station 2")
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
                model_id=bundle["model"].id,
                station_id=second_station.id,
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
                station_id=second_station.id,
                fixture_id=bundle["fixture_b"].id,
                required_qty=3,
            )
        )

        model_query = self.production_service.get_model_query(
            bundle["model"].id,
            customer_id=bundle["customer"].id,
        )

        self.assertEqual(model_query["max_open_station_count"], 3)
        station_rows = {row["station_code"]: row["max_open_station_count"] for row in model_query["stations"]}
        self.assertEqual(station_rows, {"ST-001": 6, "ST-002": 3})


class InventoryServiceTests(ServiceTestCase):
    def _make_receipt_payload(self, bundle, transaction_no: str = "12005436") -> StockTransactionCreate:
        return StockTransactionCreate(
            customer_id=bundle["customer"].id,
            created_by="Tester",
            occurred_at=datetime(2026, 6, 9, 8, 30, tzinfo=timezone.utc),
            transaction_no=transaction_no,
            items=[
                {
                    "fixture_id": bundle["fixture_a"].id,
                    "ownership_type": "self_purchased",
                    "identifier": "2606",
                    "quantity": 5,
                }
            ],
        )

    def test_receipt_identifier_is_left_padded_to_four_digits(self) -> None:
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
                    "identifier": "7",
                    "quantity": 5,
                }
            ],
        )

        self.inventory_service.receipt(payload)
        transaction = self.db.scalar(select(MaterialTransaction).where(MaterialTransaction.customer_id == bundle["customer"].id))
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.items[0].identifier, "0007")

    def test_receipt_updates_stock_summary(self) -> None:
        bundle = self.seed_customer_bundle()
        payload = self._make_receipt_payload(bundle)

        self.inventory_service.receipt(payload)
        summary = self.db.get(FixtureStockSummary, bundle["fixture_a"].id)
        self.assertIsNotNone(summary)
        self.assertEqual(summary.stock_qty, 17)

        transaction_count = self.db.scalar(select(func.count()).select_from(MaterialTransaction))
        self.assertEqual(transaction_count, 1)
        transaction = self.db.scalar(select(MaterialTransaction).where(MaterialTransaction.customer_id == bundle["customer"].id))
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.transaction_no, "12005436")

    def test_receipt_persists_authenticated_actor_and_display_name_snapshot(self) -> None:
        bundle = self.seed_customer_bundle()
        payload = self._make_receipt_payload(bundle, transaction_no="ACTOR-SNAPSHOT-001")

        self.inventory_service.receipt(payload)
        transaction = self.db.scalar(
            select(MaterialTransaction).where(MaterialTransaction.transaction_no == "ACTOR-SNAPSHOT-001")
        )
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.actor_user_id, self.transaction_actor.user_id)
        self.assertEqual(transaction.created_by, "Tester")

        actor_user = self.repo.get_user(self.transaction_actor.user_id)
        self.assertIsNotNone(actor_user)
        actor_user.display_name = "Renamed Operator"
        self.db.commit()
        self.db.refresh(transaction)

        self.assertEqual(transaction.actor_user_id, self.transaction_actor.user_id)
        self.assertEqual(transaction.created_by, "Tester")

    def test_stock_summary_exposes_customer_and_self_purchased_balances(self) -> None:
        bundle = self.seed_customer_bundle()
        fixture_id = bundle["fixture_a"].id
        summary = self.db.get(FixtureStockSummary, fixture_id)
        self.assertIsNotNone(summary)
        summary.stock_qty = 0
        self.db.commit()

        for transaction_no, ownership_type, quantity in [
            ("BREAKDOWN-CUSTOMER-001", "customer_supplied", 4),
            ("BREAKDOWN-SELF-001", "self_purchased", 6),
        ]:
            self.inventory_service.receipt(
                StockTransactionCreate(
                    customer_id=bundle["customer"].id,
                    created_by="Tester",
                    transaction_no=transaction_no,
                    items=[
                        {
                            "fixture_id": fixture_id,
                            "ownership_type": ownership_type,
                            "identifier": "2606",
                            "quantity": quantity,
                        }
                    ],
                )
            )

        self.inventory_service.return_material(
            StockTransactionCreate(
                customer_id=bundle["customer"].id,
                created_by="Tester",
                transaction_no="BREAKDOWN-RETURN-001",
                items=[
                    {
                        "fixture_id": fixture_id,
                        "ownership_type": "customer_supplied",
                        "identifier": "2606",
                        "quantity": 1,
                    }
                ],
            )
        )

        stock_row = next(
            row
            for row in self.inventory_service.list_stock_summary(bundle["customer"].id)
            if row["fixture_id"] == fixture_id
        )
        self.assertEqual(stock_row["customer_supplied_qty"], 3)
        self.assertEqual(stock_row["self_purchased_qty"], 6)
        self.assertEqual(stock_row["stock_qty"], 9)
        self.assertEqual(
            stock_row["stock_qty"],
            stock_row["customer_supplied_qty"] + stock_row["self_purchased_qty"],
        )

        identifier_row = next(
            row
            for row in self.inventory_service.list_identifier_stock_summary(bundle["customer"].id)
            if row["fixture_id"] == fixture_id and row["identifier"] == "2606"
        )
        self.assertEqual(identifier_row["stock_qty"], 9)
        self.assertEqual(identifier_row["customer_supplied_qty"], 3)
        self.assertEqual(identifier_row["self_purchased_qty"], 6)

    def test_return_rejects_quantity_from_a_different_ownership_type(self) -> None:
        bundle = self.seed_customer_bundle()
        fixture_id = bundle["fixture_a"].id
        summary = self.db.get(FixtureStockSummary, fixture_id)
        self.assertIsNotNone(summary)
        summary.stock_qty = 0
        self.db.commit()

        self.inventory_service.receipt(
            StockTransactionCreate(
                customer_id=bundle["customer"].id,
                created_by="Tester",
                transaction_no="OWNERSHIP-CUSTOMER-RECEIPT-001",
                items=[
                    {
                        "fixture_id": fixture_id,
                        "ownership_type": "customer_supplied",
                        "identifier": "2606",
                        "quantity": 5,
                    }
                ],
            )
        )

        with self.assertRaises(ValueError) as exc:
            self.inventory_service.return_material(
                StockTransactionCreate(
                    customer_id=bundle["customer"].id,
                    created_by="Tester",
                    transaction_no="OWNERSHIP-SELF-RETURN-001",
                    items=[
                        {
                            "fixture_id": fixture_id,
                            "ownership_type": "self_purchased",
                            "identifier": "2606",
                            "quantity": 3,
                        }
                    ],
                )
            )

        self.assertEqual(str(exc.exception), "第 1 筆：治具 FX-A 的識別碼 2606 不在目前庫存中")
        return_count = self.db.scalar(
            select(func.count())
            .select_from(MaterialTransaction)
            .where(MaterialTransaction.transaction_type == "return")
        )
        self.assertEqual(return_count, 0)

        stock_row = next(
            row
            for row in self.inventory_service.list_stock_summary(bundle["customer"].id)
            if row["fixture_id"] == fixture_id
        )
        self.assertEqual(stock_row["customer_supplied_qty"], 5)
        self.assertEqual(stock_row["self_purchased_qty"], 0)
        self.assertEqual(stock_row["stock_qty"], 5)

        identifier_row = next(
            row
            for row in self.inventory_service.list_identifier_stock_summary(bundle["customer"].id)
            if row["fixture_id"] == fixture_id and row["identifier"] == "2606"
        )
        self.assertEqual(identifier_row["customer_supplied_qty"], 5)
        self.assertEqual(identifier_row["self_purchased_qty"], 0)
        self.assertEqual(identifier_row["stock_qty"], 5)

    def test_return_rechecks_flushed_ownership_balance_within_one_batch(self) -> None:
        bundle = self.seed_customer_bundle()
        fixture_id = bundle["fixture_a"].id
        summary = self.db.get(FixtureStockSummary, fixture_id)
        self.assertIsNotNone(summary)
        summary.stock_qty = 0
        self.db.commit()

        self.inventory_service.receipt(
            StockTransactionCreate(
                customer_id=bundle["customer"].id,
                transaction_no="BATCH-OWNERSHIP-RECEIPT-001",
                items=[
                    {
                        "fixture_id": fixture_id,
                        "ownership_type": "customer_supplied",
                        "identifier": "2606",
                        "quantity": 3,
                    },
                    {
                        "fixture_id": fixture_id,
                        "ownership_type": "self_purchased",
                        "identifier": "2606",
                        "quantity": 10,
                    },
                ],
            )
        )

        with self.assertRaisesRegex(ValueError, "剩餘可退 1 pcs"):
            self.inventory_service.return_material(
                StockTransactionCreate(
                    customer_id=bundle["customer"].id,
                    transaction_no="BATCH-OWNERSHIP-RETURN-001",
                    items=[
                        {
                            "fixture_id": fixture_id,
                            "ownership_type": "customer_supplied",
                            "identifier": "2606",
                            "quantity": 2,
                        },
                        {
                            "fixture_id": fixture_id,
                            "ownership_type": "customer_supplied",
                            "identifier": "2606",
                            "quantity": 2,
                        },
                    ],
                )
            )

        stock_row = next(
            row
            for row in self.inventory_service.list_stock_summary(bundle["customer"].id)
            if row["fixture_id"] == fixture_id
        )
        self.assertEqual(stock_row["customer_supplied_qty"], 3)
        self.assertEqual(stock_row["self_purchased_qty"], 10)
        self.assertEqual(stock_row["stock_qty"], 13)

    def test_duplicate_transaction_guard_blocks_recent_identical_submission(self) -> None:
        bundle = self.seed_customer_bundle()
        payload = self._make_receipt_payload(bundle, transaction_no="DUP-0001")

        self.inventory_service.receipt(payload)
        transaction = self.db.scalar(select(MaterialTransaction).where(MaterialTransaction.transaction_no == "DUP-0001"))
        self.assertIsNotNone(transaction)
        transaction.created_at = datetime.now(tz=timezone.utc) - timedelta(seconds=75)
        self.db.commit()

        with self.assertRaises(DuplicateTransactionError) as exc:
            self.inventory_service.receipt(payload)

        self.assertIn("已有相同交易", str(exc.exception))

    def test_duplicate_transaction_guard_confirm_still_requires_unique_transaction_no(self) -> None:
        bundle = self.seed_customer_bundle()
        payload = self._make_receipt_payload(bundle, transaction_no="DUP-0002")

        self.inventory_service.receipt(payload)
        transaction = self.db.scalar(select(MaterialTransaction).where(MaterialTransaction.transaction_no == "DUP-0002"))
        self.assertIsNotNone(transaction)
        transaction.created_at = datetime.now(tz=timezone.utc) - timedelta(seconds=30)
        self.db.commit()

        with self.assertRaises(ValueError) as exc:
            self.inventory_service.receipt(payload, allow_duplicate=True)

        self.assertEqual(str(exc.exception), "單號 DUP-0002 已存在，若要重複送出請先修改單號")

    def test_legacy_numeric_identifier_longer_than_four_digits_is_preserved(self) -> None:
        bundle = self.seed_customer_bundle()
        payload = StockTransactionCreate(
            customer_id=bundle["customer"].id,
            created_by="Tester",
            transaction_no="LEGACY-NUMERIC-0001",
            items=[
                {
                    "fixture_id": bundle["fixture_a"].id,
                    "ownership_type": "self_purchased",
                    "identifier": "12345",
                    "quantity": 1,
                }
            ],
        )

        self.assertEqual(payload.items[0].identifier, "12345")

    def test_legacy_alphanumeric_identifier_is_preserved(self) -> None:
        bundle = self.seed_customer_bundle()
        payload = StockTransactionCreate(
            customer_id=bundle["customer"].id,
            created_by="Tester",
            transaction_no="LEGACY-ALPHANUMERIC-0001",
            items=[
                {
                    "fixture_id": bundle["fixture_a"].id,
                    "ownership_type": "self_purchased",
                    "identifier": "2024W12",
                    "quantity": 1,
                }
            ],
        )

        self.assertEqual(payload.items[0].identifier, "2024W12")

    def test_transaction_queries_match_numeric_identifier_across_legacy_padding_formats(self) -> None:
        bundle = self.seed_customer_bundle()

        self.inventory_service.receipt(
            StockTransactionCreate(
                customer_id=bundle["customer"].id,
                created_by="Tester",
                occurred_at=datetime(2026, 6, 9, 8, 30, tzinfo=timezone.utc),
                transaction_no="RCV-NEW-0001",
                items=[
                    {
                        "fixture_id": bundle["fixture_a"].id,
                        "ownership_type": "self_purchased",
                        "identifier": "1",
                        "quantity": 2,
                    }
                ],
            )
        )
        legacy_tx = self.inventory_service.repo.create_transaction(
            customer_id=bundle["customer"].id,
            transaction_type="receipt",
            occurred_at=datetime(2026, 6, 8, 8, 30, tzinfo=timezone.utc),
            actor_user_id=self.transaction_actor.user_id,
            created_by="Legacy Loader",
            transaction_no="RCV-LEGACY-0001",
            note=None,
        )
        self.inventory_service.repo.add_transaction_item(
            transaction_id=legacy_tx.id,
            fixture_id=bundle["fixture_a"].id,
            ownership_type="self_purchased",
            identifier="01",
            quantity=1,
            note=None,
        )
        self.db.commit()

        transactions = self.inventory_service.list_transactions(
            20,
            customer_id=bundle["customer"].id,
            identifier="0001",
        )

        self.assertEqual(
            {tx["transaction_no"] for tx in transactions},
            {"RCV-NEW-0001", "RCV-LEGACY-0001"},
        )

    def test_transaction_export_query_accepts_legacy_identifier_text(self) -> None:
        bundle = self.seed_customer_bundle()

        legacy_tx = self.inventory_service.repo.create_transaction(
            customer_id=bundle["customer"].id,
            transaction_type="receipt",
            occurred_at=datetime(2026, 6, 8, 8, 30, tzinfo=timezone.utc),
            actor_user_id=self.transaction_actor.user_id,
            created_by="Legacy Loader",
            transaction_no="RCV-LEGACY-DATECODE",
            note=None,
        )
        self.inventory_service.repo.add_transaction_item(
            transaction_id=legacy_tx.id,
            fixture_id=bundle["fixture_a"].id,
            ownership_type="self_purchased",
            identifier="2024W12",
            quantity=3,
            note=None,
        )
        self.db.commit()

        columns, rows = self.inventory_service.build_transaction_export_report(
            customer_id=bundle["customer"].id,
            report_type="detail",
            identifier="2024W12",
        )

        self.assertEqual(columns, ["治具編號", "識別碼", "收料數", "退料數", "總數"])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["治具編號"], "FX-A")
        self.assertEqual(rows[0]["識別碼"], "2024W12")
        self.assertEqual(rows[0]["收料數"], 3)

    def test_transaction_export_report_filters_detail_rows_by_ownership_type(self) -> None:
        bundle = self.seed_customer_bundle()
        transaction = self.inventory_service.repo.create_transaction(
            customer_id=bundle["customer"].id,
            transaction_type="receipt",
            occurred_at=datetime(2026, 6, 10, 8, 30, tzinfo=timezone.utc),
            actor_user_id=self.transaction_actor.user_id,
            created_by="Export Tester",
            transaction_no="RCV-EXPORT-SOURCE",
            note=None,
        )
        self.inventory_service.repo.add_transaction_item(
            transaction_id=transaction.id,
            fixture_id=bundle["fixture_a"].id,
            ownership_type="customer_supplied",
            identifier="CUSTOMER-001",
            quantity=5,
            note=None,
        )
        self.inventory_service.repo.add_transaction_item(
            transaction_id=transaction.id,
            fixture_id=bundle["fixture_a"].id,
            ownership_type="self_purchased",
            identifier="SELF-001",
            quantity=3,
            note=None,
        )
        self.db.commit()

        _, customer_rows = self.inventory_service.build_transaction_export_report(
            customer_id=bundle["customer"].id,
            report_type="detail",
            ownership_type="customer_supplied",
        )
        self.assertEqual([row["識別碼"] for row in customer_rows], ["CUSTOMER-001"])
        self.assertEqual(customer_rows[0]["收料數"], 5)

        self_preview = self.inventory_service.get_transaction_export_preview(
            customer_id=bundle["customer"].id,
            report_type="detail",
            ownership_type="self_purchased",
        )
        self.assertEqual(self_preview["raw_item_count"], 1)
        self.assertEqual(self_preview["export_row_count"], 1)

    def test_transaction_queries_match_legacy_identifier_by_exact_value(self) -> None:
        bundle = self.seed_customer_bundle()

        first_tx = self.inventory_service.repo.create_transaction(
            customer_id=bundle["customer"].id,
            transaction_type="receipt",
            occurred_at=datetime(2026, 6, 8, 8, 30, tzinfo=timezone.utc),
            actor_user_id=self.transaction_actor.user_id,
            created_by="Legacy Loader",
            transaction_no="RCV-LEGACY-12345",
            note=None,
        )
        self.inventory_service.repo.add_transaction_item(
            transaction_id=first_tx.id,
            fixture_id=bundle["fixture_a"].id,
            ownership_type="self_purchased",
            identifier="12345",
            quantity=1,
            note=None,
        )
        second_tx = self.inventory_service.repo.create_transaction(
            customer_id=bundle["customer"].id,
            transaction_type="receipt",
            occurred_at=datetime(2026, 6, 8, 9, 30, tzinfo=timezone.utc),
            actor_user_id=self.transaction_actor.user_id,
            created_by="Legacy Loader",
            transaction_no="RCV-LEGACY-123456",
            note=None,
        )
        self.inventory_service.repo.add_transaction_item(
            transaction_id=second_tx.id,
            fixture_id=bundle["fixture_a"].id,
            ownership_type="self_purchased",
            identifier="123456",
            quantity=1,
            note=None,
        )
        self.db.commit()

        transactions = self.inventory_service.list_transactions(
            20,
            customer_id=bundle["customer"].id,
            identifier="12345",
        )

        self.assertEqual(
            {tx["transaction_no"] for tx in transactions},
            {"RCV-LEGACY-12345"},
        )

    def test_transaction_overview_page_returns_paginated_detail_rows(self) -> None:
        bundle = self.seed_customer_bundle()
        customer_id = bundle["customer"].id

        self.inventory_service.receipt(
            StockTransactionCreate(
                customer_id=customer_id,
                created_by="Admin",
                occurred_at=datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc),
                transaction_no="OV-001",
                note="tx note",
                items=[
                    {
                        "fixture_id": bundle["fixture_a"].id,
                        "ownership_type": "self_purchased",
                        "identifier": "001",
                        "quantity": 2,
                    }
                ],
            )
        )
        self.inventory_service.receipt(
            StockTransactionCreate(
                customer_id=customer_id,
                created_by="Admin",
                occurred_at=datetime(2026, 1, 2, 8, 0, tzinfo=timezone.utc),
                transaction_no="OV-002",
                items=[
                    {
                        "fixture_id": bundle["fixture_b"].id,
                        "ownership_type": "customer_supplied",
                        "identifier": "002",
                        "quantity": 1,
                        "note": "item note",
                    }
                ],
            )
        )
        self.inventory_service.receipt(
            StockTransactionCreate(
                customer_id=customer_id,
                created_by="Alice",
                occurred_at=datetime(2026, 1, 3, 8, 0, tzinfo=timezone.utc),
                transaction_no="OV-003",
                items=[
                    {
                        "fixture_id": bundle["fixture_a"].id,
                        "ownership_type": "self_purchased",
                        "identifier": "003",
                        "quantity": 5,
                    }
                ],
            )
        )

        first_page = self.inventory_service.list_transaction_overview_page(page=1, page_size=2, customer_id=customer_id)
        self.assertEqual(first_page["page"], 1)
        self.assertEqual(first_page["page_size"], 2)
        self.assertEqual(first_page["total"], 3)
        self.assertEqual([row["transaction_no"] for row in first_page["items"]], ["OV-003", "OV-002"])
        self.assertEqual(first_page["items"][1]["note"], "item note")

        filtered = self.inventory_service.list_transaction_overview_page(
            page=1,
            page_size=10,
            customer_id=customer_id,
            fixture_code="FX-A",
        )
        self.assertEqual(filtered["total"], 2)
        self.assertEqual({row["fixture_code"] for row in filtered["items"]}, {"FX-A"})
        self.assertEqual(filtered["items"][1]["note"], "tx note")

        customer_supplied = self.inventory_service.list_transaction_overview_page(
            page=1,
            page_size=10,
            customer_id=customer_id,
            ownership_type="customer_supplied",
        )
        self.assertEqual(customer_supplied["total"], 1)
        self.assertEqual(customer_supplied["items"][0]["transaction_no"], "OV-002")
        self.assertEqual(customer_supplied["items"][0]["ownership_type"], "customer_supplied")

        self_purchased = self.inventory_service.list_transaction_overview_page(
            page=1,
            page_size=10,
            customer_id=customer_id,
            ownership_type="self_purchased",
        )
        self.assertEqual(self_purchased["total"], 2)
        self.assertEqual(
            {row["transaction_no"] for row in self_purchased["items"]},
            {"OV-001", "OV-003"},
        )

    def test_return_error_message_includes_item_index_and_identifier_context(self) -> None:
        bundle = self.seed_customer_bundle()
        self.inventory_service.receipt(
            StockTransactionCreate(
                customer_id=bundle["customer"].id,
                created_by="Tester",
                transaction_no="RETURN-CONTEXT-RECEIPT-0001",
                items=[
                    {
                        "fixture_id": bundle["fixture_a"].id,
                        "ownership_type": "self_purchased",
                        "identifier": "2606",
                        "quantity": 1,
                    }
                ],
            )
        )

        with self.assertRaises(ValueError) as exc:
            self.inventory_service.return_material(
                StockTransactionCreate(
                    customer_id=bundle["customer"].id,
                    created_by="Tester",
                    transaction_no="RETURN-CONTEXT-RETURN-0001",
                    items=[
                        {
                            "fixture_id": bundle["fixture_b"].id,
                            "ownership_type": "self_purchased",
                            "identifier": "9999",
                            "quantity": 1,
                        }
                    ],
                )
            )

        self.assertEqual(str(exc.exception), "第 1 筆：治具 FX-B 的識別碼 9999 不在目前庫存中")

    def test_import_transactions_csv_rolls_back_on_invalid_row(self) -> None:
        bundle = self.seed_customer_bundle()
        csv_content = (
            "transaction_type,transaction_no,fixture_code,ownership_type,identifier,quantity,created_by,occurred_at,note\n"
            "receipt,CSV-VALID-0001,FX-A,self_purchased,2606,5,Tester,2026-06-09T08:30:00+00:00,\n"
            "receipt,CSV-INVALID-0001,NOT-EXIST,self_purchased,2606,5,Tester,2026-06-09T08:30:00+00:00,\n"
        )

        with self.assertRaises(ValueError) as exc:
            self.inventory_service.import_transactions_csv(
                bundle["customer"].id,
                payload=CsvImportPayload(content=csv_content),
            )

        self.assertEqual(str(exc.exception), "CSV 第 3 列：找不到治具編號 NOT-EXIST")

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
        self.repo.replace_allowed_users_for_customer(bundle["customer"].id, [self.admin["id"]])
        self.db.commit()
        second_model = self.repo.create_model(customer_id=bundle["customer"].id, code="M-002", name="Model 2")
        fixture_c = self.repo.create_fixture(
            customer_id=bundle["customer"].id,
            responsible_user_id=None,
            code="FX-C",
            name="Fixture C",
            line_storage_location=None,
            department_storage_location=None,
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

    def test_copy_fixture_requirements_supports_cross_model_target(self) -> None:
        bundle = self.seed_customer_bundle()
        self.repo.replace_allowed_users_for_customer(bundle["customer"].id, [self.admin["id"]])
        target_model = self.repo.create_model(
            customer_id=bundle["customer"].id,
            code="M-002",
            name="Model 2",
        )
        target_station = self.repo.create_station(
            customer_id=bundle["customer"].id,
            code="ST-002",
            name="Station 2",
        )
        self.db.commit()
        self.production_service.create_model_station(
            ModelStationCreate(
                customer_id=bundle["customer"].id,
                model_id=bundle["model"].id,
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

        response = self.client.post(
            f"{settings.api_v2_prefix}/production/fixture-requirements/copy",
            headers=self._auth_headers(),
            json={
                "customer_id": bundle["customer"].id,
                "source_model_id": bundle["model"].id,
                "source_station_id": bundle["station"].id,
                "target_model_id": target_model.id,
                "target_station_id": target_station.id,
                "overwrite_existing": False,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "source_requirement_count": 1,
                "created_count": 1,
                "updated_count": 0,
                "skipped_count": 0,
                "mapping_created": True,
            },
        )
        target_query = self.client.get(
            f"{settings.api_v2_prefix}/production/models/{target_model.id}/query",
            params={
                "station_id": target_station.id,
                "customer_id": bundle["customer"].id,
            },
            headers=self._auth_headers(),
        )
        self.assertEqual(target_query.status_code, 200)
        self.assertEqual(
            {row["fixture_code"] for row in target_query.json()["fixtures"]},
            {"FX-A"},
        )

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

    def test_only_admin_can_delete_fixture(self) -> None:
        bundle = self.seed_customer_bundle()
        scoped_user = self.auth_service.create_user(
            UserCreate(
                username="fixture-editor",
                password="secret123",
                display_name="Fixture Editor",
                role="user",
                is_active=True,
                allowed_customer_ids=[],
            )
        )
        self.repo.replace_allowed_users_for_customer(
            bundle["customer"].id,
            [scoped_user["id"], self.admin["id"]],
        )
        self.db.commit()
        scoped_token = create_session_token(mode="user", user=self.repo.get_user(scoped_user["id"]))
        scoped_headers = {"Authorization": f"Bearer {scoped_token}"}

        forbidden = self.client.delete(
            f"/api/v2/master/fixtures/{bundle['fixture_a'].id}",
            params={"customer_id": bundle["customer"].id, "delete_transactions": False},
            headers=scoped_headers,
        )
        self.assertEqual(forbidden.status_code, 403)
        self.assertIsNotNone(self.repo.get_fixture(bundle["fixture_a"].id))

        deleted = self.client.delete(
            f"/api/v2/master/fixtures/{bundle['fixture_a'].id}",
            params={"customer_id": bundle["customer"].id, "delete_transactions": False},
            headers=self._auth_headers(),
        )
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(deleted.json()["fixture_code"], "FX-A")
        self.assertFalse(deleted.json()["transaction_records_deleted"])
        self.assertIsNone(self.repo.get_fixture(bundle["fixture_a"].id))

    def test_only_admin_can_delete_model_and_station(self) -> None:
        bundle = self.seed_customer_bundle()
        self.production_service.create_model_station(
            ModelStationCreate(
                customer_id=bundle["customer"].id,
                model_id=bundle["model"].id,
                station_id=bundle["station"].id,
            )
        )
        self.repo.replace_allowed_users_for_customer(bundle["customer"].id, [self.admin["id"]])
        scoped_user = self.auth_service.create_user(
            UserCreate(
                username="model-station-editor",
                password="secret123",
                display_name="Model Station Editor",
                role="user",
                is_active=True,
                allowed_customer_ids=[],
            )
        )
        self.repo.replace_allowed_users_for_customer(bundle["customer"].id, [self.admin["id"], scoped_user["id"]])
        self.db.commit()
        scoped_token = create_session_token(mode="user", user=self.repo.get_user(scoped_user["id"]))
        scoped_headers = {"Authorization": f"Bearer {scoped_token}"}

        forbidden_model = self.client.delete(
            f"/api/v2/master/models/{bundle['model'].id}",
            params={"customer_id": bundle["customer"].id},
            headers=scoped_headers,
        )
        self.assertEqual(forbidden_model.status_code, 403)

        forbidden_station = self.client.delete(
            f"/api/v2/master/stations/{bundle['station'].id}",
            params={"customer_id": bundle["customer"].id},
            headers=scoped_headers,
        )
        self.assertEqual(forbidden_station.status_code, 403)

        deleted_model = self.client.delete(
            f"/api/v2/master/models/{bundle['model'].id}",
            params={"customer_id": bundle["customer"].id},
            headers=self._auth_headers(),
        )
        self.assertEqual(deleted_model.status_code, 200)
        self.assertEqual(deleted_model.json()["model_code"], "M-001")

        recreated_model = self.repo.create_model(customer_id=bundle["customer"].id, code="M-NEW", name="Model New")
        recreated_station = self.repo.create_station(customer_id=bundle["customer"].id, code="ST-NEW", name="Station New")
        self.db.commit()

        deleted_station = self.client.delete(
            f"/api/v2/master/stations/{recreated_station.id}",
            params={"customer_id": bundle["customer"].id},
            headers=self._auth_headers(),
        )
        self.assertEqual(deleted_station.status_code, 200)
        self.assertEqual(deleted_station.json()["station_code"], "ST-NEW")



if __name__ == "__main__":
    unittest.main()
