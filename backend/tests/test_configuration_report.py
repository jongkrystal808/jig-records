from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, time, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.models import Base
from backend.app.models.inventory import (
    FixtureStockLevel,
    FixtureStockSummary,
    MaterialTransaction,
    MaterialTransactionItem,
)
from backend.app.repositories.master_repository import MasterRepository
from backend.app.schemas.production import FixtureRequirementCreate, ModelStationCreate
from backend.app.services.configuration_report_service import ConfigurationReportService
from backend.app.services.production_service import ProductionService


class ConfigurationReportTests(unittest.TestCase):
    def setUp(self) -> None:
        temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_file.close()
        self.db_path = Path(temp_file.name)
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.SessionLocal()
        self.master = MasterRepository(self.db)
        self.production = ProductionService(self.db)
        self.report = ConfigurationReportService(self.db)
        self.bundle = self._seed()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()
        self.db_path.unlink(missing_ok=True)

    def _seed(self) -> dict:
        customer = self.master.create_customer(code="C-REPORT", name="Report Customer")
        model = self.master.create_model(customer_id=customer.id, code="MODEL-A", name="Model A")
        model_missing = self.master.create_model(
            customer_id=customer.id,
            code="MODEL-B",
            name="Model B",
        )
        model_unmapped = self.master.create_model(
            customer_id=customer.id,
            code="MODEL-C",
            name="Model C",
        )
        station = self.master.create_station(
            customer_id=customer.id,
            code="ST-01",
            name="Station 1",
        )
        station_missing = self.master.create_station(
            customer_id=customer.id,
            code="ST-02",
            name="Station 2",
        )
        station_unmapped = self.master.create_station(
            customer_id=customer.id,
            code="ST-03",
            name="Station 3",
        )
        fixture_a = self.master.create_fixture(
            customer_id=customer.id,
            responsible_user_id=None,
            code="FX-A",
            name="Fixture A",
            line_storage_location="LINE-01",
            department_storage_location="DEP-01",
            description=None,
        )
        fixture_b = self.master.create_fixture(
            customer_id=customer.id,
            responsible_user_id=None,
            code="FX-B",
            name="Fixture B",
            line_storage_location="LINE-02",
            department_storage_location=None,
            description=None,
        )
        self.db.add_all(
            [
                FixtureStockLevel(
                    fixture_id=fixture_a.id,
                    min_stock_qty=3,
                    warning_threshold=0,
                    alert_enabled=True,
                ),
                FixtureStockSummary(
                    fixture_id=fixture_a.id,
                    stock_qty=10,
                    returned_qty=2,
                    stock_status="normal",
                ),
                FixtureStockLevel(
                    fixture_id=fixture_b.id,
                    min_stock_qty=2,
                    warning_threshold=0,
                    alert_enabled=True,
                ),
                FixtureStockSummary(
                    fixture_id=fixture_b.id,
                    stock_qty=1,
                    returned_qty=0,
                    stock_status="low_stock",
                ),
            ]
        )
        self.db.commit()
        self.production.create_model_station(
            ModelStationCreate(
                customer_id=customer.id,
                model_id=model.id,
                station_id=station.id,
            )
        )
        self.production.create_model_station(
            ModelStationCreate(
                customer_id=customer.id,
                model_id=model_missing.id,
                station_id=station_missing.id,
            )
        )
        self.production.create_fixture_requirement(
            FixtureRequirementCreate(
                customer_id=customer.id,
                model_id=model.id,
                station_id=station.id,
                fixture_id=fixture_a.id,
                required_qty=2,
            )
        )
        self.production.create_fixture_requirement(
            FixtureRequirementCreate(
                customer_id=customer.id,
                model_id=model.id,
                station_id=station.id,
                fixture_id=fixture_b.id,
                required_qty=1,
            )
        )

        receipt = MaterialTransaction(
            customer_id=customer.id,
            transaction_type="receipt",
            transaction_no="R-001",
            occurred_at=datetime(2026, 7, 20, tzinfo=timezone.utc),
            created_by="tester",
        )
        self.db.add(receipt)
        self.db.flush()
        self.db.add_all(
            [
                MaterialTransactionItem(
                    transaction_id=receipt.id,
                    fixture_id=fixture_a.id,
                    ownership_type="customer_supplied",
                    identifier="DC-01",
                    quantity=8,
                ),
                MaterialTransactionItem(
                    transaction_id=receipt.id,
                    fixture_id=fixture_a.id,
                    ownership_type="self_purchased",
                    identifier="DC-02",
                    quantity=4,
                ),
            ]
        )
        returned = MaterialTransaction(
            customer_id=customer.id,
            transaction_type="return",
            transaction_no="T-001",
            occurred_at=datetime(2026, 7, 21, tzinfo=timezone.utc),
            created_by="tester",
        )
        self.db.add(returned)
        self.db.flush()
        self.db.add(
            MaterialTransactionItem(
                transaction_id=returned.id,
                fixture_id=fixture_a.id,
                ownership_type="customer_supplied",
                identifier="DC-01",
                quantity=2,
            )
        )
        self.db.commit()
        return {
            "customer": customer,
            "model": model,
            "fixture_a": fixture_a,
            "fixture_b": fixture_b,
        }

    @staticmethod
    def empty_filters() -> dict:
        return {
            "keyword": None,
            "fixture_status": "active",
            "fixture_id": None,
            "model_id": None,
            "station_id": None,
            "water_status": None,
            "storage": None,
            "configuration_status": None,
            "transaction_type": None,
            "ownership_type": None,
            "date_from": None,
            "date_to": None,
        }

    def test_report_aggregates_rows_summary_and_ownership_stock(self) -> None:
        result = self.report.get_page(
            customer_id=self.bundle["customer"].id,
            page=1,
            page_size=50,
            filters=self.empty_filters(),
            sort_by="fixture_code",
            sort_direction="asc",
            include_transaction_details=False,
        )

        self.assertEqual(result["total"], 5)
        self.assertEqual(result["fixture_count"], 2)
        self.assertEqual(result["attention_fixture_count"], 1)
        self.assertEqual(result["missing_configuration_count"], 3)
        self.assertEqual(result["total_stock_qty"], 11)
        self.assertEqual(result["customer_supplied_qty"], 6)
        self.assertEqual(result["self_purchased_qty"], 4)
        fixture_a = next(row for row in result["items"] if row["fixture_code"] == "FX-A")
        self.assertEqual(fixture_a["customer_supplied_qty"], 6)
        self.assertEqual(fixture_a["self_purchased_qty"], 4)
        self.assertEqual(fixture_a["max_open_station_count"], 1)
        self.assertIn("departmentStorage", result["populated_columns"])
        self.assertIn("maxOpenStationCount", result["populated_columns"])

    def test_report_capacity_uses_only_designated_identifier_stock(self) -> None:
        requirement = next(
            row
            for row in self.production.repo.list_all_requirements(self.bundle["customer"].id)
            if row.fixture_id == self.bundle["fixture_a"].id
        )
        self.production.repo.update_requirement(
            requirement,
            model_id=requirement.model_id,
            station_id=requirement.station_id,
            fixture_id=requirement.fixture_id,
            required_qty=requirement.required_qty,
            designated_mode=True,
            designated_identifiers=["DC-02"],
        )
        fixture_b_summary = self.db.get(FixtureStockSummary, self.bundle["fixture_b"].id)
        fixture_b_summary.stock_qty = 20
        self.db.commit()

        result = self.report.get_page(
            customer_id=self.bundle["customer"].id,
            page=1,
            page_size=50,
            filters=self.empty_filters(),
            sort_by="fixture_code",
            sort_direction="asc",
            include_transaction_details=False,
        )

        fixture_a = next(row for row in result["items"] if row["fixture_code"] == "FX-A")
        self.assertEqual(fixture_a["stock_qty"], 10)
        self.assertEqual(fixture_a["max_open_station_count"], 2)

    def test_report_populated_columns_cover_the_full_filtered_result(self) -> None:
        filters = self.empty_filters()
        filters["fixture_id"] = self.bundle["fixture_b"].id
        result = self.report.get_page(
            customer_id=self.bundle["customer"].id,
            page=1,
            page_size=1,
            filters=filters,
            sort_by="fixture_code",
            sort_direction="asc",
            include_transaction_details=False,
        )

        self.assertEqual(result["total"], 1)
        self.assertIn("lineStorage", result["populated_columns"])
        self.assertIn("modelCode", result["populated_columns"])
        self.assertNotIn("departmentStorage", result["populated_columns"])

    def test_fixture_status_defaults_to_active_and_can_show_inactive_or_all(self) -> None:
        self.bundle["fixture_b"].is_active = False
        self.db.commit()

        active_result = self.report.get_page(
            customer_id=self.bundle["customer"].id,
            page=1,
            page_size=50,
            filters=self.empty_filters(),
            sort_by="fixture_code",
            sort_direction="asc",
            include_transaction_details=False,
        )
        self.assertFalse(any(row["fixture_code"] == "FX-B" for row in active_result["items"]))
        self.assertEqual(active_result["missing_configuration_count"], 3)

        inactive_filters = self.empty_filters()
        inactive_filters["fixture_status"] = "inactive"
        inactive_result = self.report.get_page(
            customer_id=self.bundle["customer"].id,
            page=1,
            page_size=50,
            filters=inactive_filters,
            sort_by="fixture_code",
            sort_direction="asc",
            include_transaction_details=False,
        )
        self.assertEqual([row["fixture_code"] for row in inactive_result["items"]], ["FX-B"])
        self.assertEqual(inactive_result["missing_configuration_count"], 0)

        all_filters = self.empty_filters()
        all_filters["fixture_status"] = "all"
        all_result = self.report.get_page(
            customer_id=self.bundle["customer"].id,
            page=1,
            page_size=50,
            filters=all_filters,
            sort_by="fixture_code",
            sort_direction="asc",
            include_transaction_details=False,
        )
        self.assertTrue(any(row["fixture_code"] == "FX-B" for row in all_result["items"]))
        self.assertEqual(all_result["total"], 5)

    def test_fixture_status_accepts_repeated_multi_value_filters(self) -> None:
        self.bundle["fixture_b"].is_active = False
        self.db.commit()

        filters = self.empty_filters()
        filters["fixture_status"] = ["active", "inactive"]
        result = self.report.get_page(
            customer_id=self.bundle["customer"].id,
            page=1,
            page_size=50,
            filters=filters,
            sort_by="fixture_code",
            sort_direction="asc",
            include_transaction_details=False,
        )

        self.assertEqual(result["total"], 5)
        self.assertTrue(any(row["fixture_code"] == "FX-B" for row in result["items"]))

    def test_transaction_filter_runs_in_database_and_returns_page_details(self) -> None:
        filters = self.empty_filters()
        filters.update(
            {
                "transaction_type": "receipt",
                "ownership_type": "customer_supplied",
                "date_from": datetime.combine(
                    datetime(2026, 7, 20).date(),
                    time.min,
                    tzinfo=timezone.utc,
                ),
                "date_to": datetime.combine(
                    datetime(2026, 7, 20).date(),
                    time.max,
                    tzinfo=timezone.utc,
                ),
            }
        )
        result = self.report.get_page(
            customer_id=self.bundle["customer"].id,
            page=1,
            page_size=50,
            filters=filters,
            sort_by="fixture_code",
            sort_direction="asc",
            include_transaction_details=True,
        )

        self.assertEqual(result["total"], 1)
        self.assertEqual(result["transaction_detail_count"], 1)
        self.assertEqual(len(result["transaction_details"]), 1)
        self.assertEqual(result["transaction_details"][0]["transaction_no"], "R-001")
        self.assertEqual(result["transaction_details"][0]["identifier"], "DC-01")
        self.assertEqual(
            result["transaction_details"][0]["ownership_type"],
            "customer_supplied",
        )

    def test_filter_options_follow_priority_and_server_export_supports_xlsx(self) -> None:
        filters = self.empty_filters()
        filters["fixture_id"] = self.bundle["fixture_a"].id
        options = self.report.get_options(
            customer_id=self.bundle["customer"].id,
            filters=filters,
            priority="fixture_id",
        )
        self.assertEqual([row["code"] for row in options["models"]], ["MODEL-A"])

        headers, rows = self.report.build_export(
            customer_id=self.bundle["customer"].id,
            filters=filters,
            sort_by="fixture_code",
            sort_direction="asc",
            columns=[
                "fixtureCode",
                "stockQty",
                "customerSuppliedQty",
                "selfPurchasedQty",
                "maxOpenStationCount",
            ],
            include_transaction_details=False,
        )
        self.assertEqual(
            headers,
            ["治具代碼", "總庫存", "客供庫存", "自購庫存", "可開站"],
        )
        self.assertEqual(rows, [["FX-A", 10, 6, 4, 1]])
        self.assertTrue(self.report.render_xlsx(headers, rows).startswith(b"PK"))

        detail_headers, detail_rows = self.report.build_export(
            customer_id=self.bundle["customer"].id,
            filters=filters,
            sort_by="fixture_code",
            sort_direction="asc",
            columns=["fixtureCode"],
            include_transaction_details=True,
        )
        self.assertEqual(
            detail_headers,
            [
                "治具代碼",
                "收退料類型",
                "交易來源",
                "交易日期",
                "單號",
                "datecode/編號",
                "交易數量",
            ],
        )
        self.assertEqual({row[2] for row in detail_rows}, {"客供", "自購"})


if __name__ == "__main__":
    unittest.main()
