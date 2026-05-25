from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.inventory import FixtureStockSummary
from backend.app.models.master import Fixture, Station
from backend.app.models.production import FixtureRequirement, MachineCapacitySummary


class ProductionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_or_update_requirement(self, *, station_id: int, fixture_id: int, required_qty: int) -> FixtureRequirement:
        stmt = select(FixtureRequirement).where(
            FixtureRequirement.station_id == station_id, FixtureRequirement.fixture_id == fixture_id
        )
        requirement = self.db.scalar(stmt)
        if requirement:
            requirement.required_qty = required_qty
            self.db.flush()
            return requirement

        requirement = FixtureRequirement(station_id=station_id, fixture_id=fixture_id, required_qty=required_qty)
        self.db.add(requirement)
        self.db.flush()
        return requirement

    def list_station_requirements(self, station_id: int) -> list[FixtureRequirement]:
        stmt = select(FixtureRequirement).where(FixtureRequirement.station_id == station_id)
        return list(self.db.scalars(stmt))

    def list_affected_station_ids_by_fixture(self, fixture_id: int) -> list[int]:
        stmt = select(FixtureRequirement.station_id).where(FixtureRequirement.fixture_id == fixture_id).distinct()
        return list(self.db.scalars(stmt))

    def get_fixture(self, fixture_id: int) -> Fixture | None:
        return self.db.get(Fixture, fixture_id)

    def get_station(self, station_id: int) -> Station | None:
        return self.db.get(Station, station_id)

    def get_stock_qty(self, fixture_id: int) -> int:
        summary = self.db.get(FixtureStockSummary, fixture_id)
        return 0 if summary is None else summary.stock_qty

    def upsert_station_capacity(self, *, station_id: int, max_count: int, bottleneck_fixture_code: str | None) -> None:
        summary = self.db.get(MachineCapacitySummary, station_id)
        if summary:
            summary.max_open_station_count = max_count
            summary.bottleneck_fixture_code = bottleneck_fixture_code
            self.db.flush()
            return

        summary = MachineCapacitySummary(
            station_id=station_id, max_open_station_count=max_count, bottleneck_fixture_code=bottleneck_fixture_code
        )
        self.db.add(summary)
        self.db.flush()
