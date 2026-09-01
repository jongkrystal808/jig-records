from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.models import Base
from backend.app.models.inventory import FixtureStockSummary
from backend.app.models.production import FixtureRequirement
from backend.app.repositories.master_repository import MasterRepository
from backend.app.schemas.master import FixtureUpdate
from backend.app.schemas.storage import (
    FixturePlacementInput,
    FixturePlacementUpdate,
    StorageCodeOrganize,
    StorageCodeRegister,
    StorageContainerCreate,
)
from backend.app.services.master_service import MasterService
from backend.app.services.production_service import ProductionService
from backend.app.services.storage_service import StorageService


class StorageServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_file.close()
        self.db_path = Path(temp_file.name)
        self.engine = create_engine(f"sqlite:///{self.db_path}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.SessionLocal()
        repo = MasterRepository(self.db)
        self.customer = repo.create_customer(code="C-001", name="Customer")
        self.model = repo.create_model(customer_id=self.customer.id, code="E1210", name="ioLogik E1210")
        self.station = repo.create_station(customer_id=self.customer.id, code="T2", name="Test 2")
        self.fixture = repo.create_fixture(
            customer_id=self.customer.id,
            responsible_user_id=None,
            code="L-00091",
            name="Fixture",
            line_storage_location=None,
            department_storage_location=None,
            description=None,
        )
        self.db.add(
            FixtureRequirement(
                fixture_id=self.fixture.id,
                model_id=self.model.id,
                station_id=self.station.id,
                required_qty=1,
            )
        )
        self.db.add(FixtureStockSummary(fixture_id=self.fixture.id, stock_qty=6, returned_qty=0, stock_status="normal"))
        self.db.commit()
        self.service = StorageService(self.db)

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()
        self.db_path.unlink(missing_ok=True)

    def test_fixture_field_parsing_resolves_unique_station_and_registers_codes(self) -> None:
        MasterService(self.db).update_fixture(
            self.fixture.id,
            FixtureUpdate(
                customer_id=self.customer.id,
                code=self.fixture.code,
                name=self.fixture.name,
                line_storage_location="T2, AXG001， MOXA001, AXG001",
                department_storage_location=None,
                min_stock_qty=0,
                description=None,
                is_active=True,
            ),
        )

        detail = self.service.get_fixture_placements(self.fixture.id)
        self.assertEqual(len(detail["placements"]), 3)
        station_rows = [row for row in detail["placements"] if row["target_type"] == "model_station"]
        self.assertEqual(len(station_rows), 1)
        self.assertEqual(station_rows[0]["display_label"], "ioLogik E1210 / T2")
        overview = self.service.get_overview(self.customer.id)
        self.assertEqual([row["code"] for row in overview["codes"]], ["AXG001", "MOXA001"])
        self.assertEqual(overview["pending_quantity_count"], 2)

    def test_register_organize_and_allocate_quantities(self) -> None:
        overview = self.service.register_codes(
            StorageCodeRegister(customer_id=self.customer.id, location_text="AXG001, MOXA001")
        )
        container = self.service.create_container(
            StorageContainerCreate(customer_id=self.customer.id, name="機櫃1")
        )
        code_ids = [row["id"] for row in overview["codes"]]
        organized = self.service.organize_codes(
            StorageCodeOrganize(
                customer_id=self.customer.id,
                storage_code_ids=code_ids,
                container_id=container["id"],
            )
        )
        self.assertTrue(all(row["container_name"] == "機櫃1" for row in organized["codes"]))

        detail = self.service.replace_fixture_placements(
            self.fixture.id,
            FixturePlacementUpdate(
                placements=[
                    FixturePlacementInput(
                        target_type="model_station",
                        model_id=self.model.id,
                        station_id=self.station.id,
                        quantity=3,
                    ),
                    FixturePlacementInput(
                        target_type="storage_code",
                        storage_code_id=code_ids[0],
                        quantity=2,
                    ),
                    FixturePlacementInput(
                        target_type="storage_code",
                        storage_code_id=code_ids[1],
                        quantity=None,
                    ),
                ]
            ),
        )
        self.assertEqual(detail["allocated_qty"], 5)
        self.assertEqual(detail["unallocated_qty"], 1)
        self.assertTrue(detail["has_pending_quantities"])

    def test_allocation_cannot_exceed_stock(self) -> None:
        overview = self.service.register_codes(
            StorageCodeRegister(customer_id=self.customer.id, location_text="AXG001")
        )
        with self.assertRaisesRegex(ValueError, "不可超過目前庫存"):
            self.service.replace_fixture_placements(
                self.fixture.id,
                FixturePlacementUpdate(
                    placements=[
                        FixturePlacementInput(
                            target_type="storage_code",
                            storage_code_id=overview["codes"][0]["id"],
                            quantity=7,
                        )
                    ]
                ),
            )

    def test_removing_fixture_requirement_converts_field_station_back_to_code(self) -> None:
        MasterService(self.db).update_fixture(
            self.fixture.id,
            FixtureUpdate(
                customer_id=self.customer.id,
                code=self.fixture.code,
                name=self.fixture.name,
                line_storage_location="T2",
                department_storage_location=None,
                min_stock_qty=0,
                description=None,
                is_active=True,
            ),
        )
        requirement = self.db.query(FixtureRequirement).filter_by(fixture_id=self.fixture.id).one()

        ProductionService(self.db).delete_fixture_requirement(requirement.id, customer_id=self.customer.id)

        detail = self.service.get_fixture_placements(self.fixture.id)
        self.assertEqual(len(detail["placements"]), 1)
        self.assertEqual(detail["placements"][0]["target_type"], "storage_code")
        self.assertEqual(detail["placements"][0]["storage_code"], "T2")


if __name__ == "__main__":
    unittest.main()
