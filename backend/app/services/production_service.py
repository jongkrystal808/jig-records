from math import floor
from sqlalchemy.exc import IntegrityError

from sqlalchemy.orm import Session

from backend.app.repositories.production_repository import ProductionRepository
from backend.app.schemas.production import FixtureRequirementCreate, ModelStationCreate


class ProductionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProductionRepository(db)

    def create_model_station(self, payload: ModelStationCreate):
        model = self.repo.get_model(payload.model_id)
        if model is None:
            raise ValueError(f"model {payload.model_id} not found")

        station = self.repo.get_station(payload.station_id)
        if station is None:
            raise ValueError(f"station {payload.station_id} not found")

        try:
            model_station = self.repo.create_model_station(model_id=payload.model_id, station_id=payload.station_id)
            self.db.commit()
            self.db.refresh(model_station)
            return model_station
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("model-station mapping already exists") from exc

    def list_model_stations(self):
        return self.repo.list_model_stations()

    def create_fixture_requirement(self, payload: FixtureRequirementCreate):
        fixture = self.repo.get_fixture(payload.fixture_id)
        if fixture is None:
            raise ValueError(f"fixture {payload.fixture_id} not found")

        station = self.repo.get_station(payload.station_id)
        if station is None:
            raise ValueError(f"station {payload.station_id} not found")

        requirement = self.repo.create_or_update_requirement(
            station_id=payload.station_id, fixture_id=payload.fixture_id, required_qty=payload.required_qty
        )
        self.recalculate_station_capacity(payload.station_id)
        self.db.commit()
        self.db.refresh(requirement)
        return requirement

    def get_affected_station_ids_by_fixture(self, fixture_id: int) -> list[int]:
        return self.repo.list_affected_station_ids_by_fixture(fixture_id)

    def recalculate_station_capacity(self, station_id: int) -> tuple[int, str | None]:
        requirements = self.repo.list_station_requirements(station_id)
        if not requirements:
            self.repo.upsert_station_capacity(station_id=station_id, max_count=0, bottleneck_fixture_code=None)
            return 0, None

        min_capacity: int | None = None
        bottleneck_code: str | None = None

        for req in requirements:
            stock_qty = self.repo.get_stock_qty(req.fixture_id)
            capacity = floor(stock_qty / req.required_qty)
            fixture = self.repo.get_fixture(req.fixture_id)
            fixture_code = "unknown" if fixture is None else fixture.code

            if min_capacity is None or capacity < min_capacity:
                min_capacity = capacity
                bottleneck_code = fixture_code

        max_count = 0 if min_capacity is None else min_capacity
        self.repo.upsert_station_capacity(station_id=station_id, max_count=max_count, bottleneck_fixture_code=bottleneck_code)
        return max_count, bottleneck_code

    def get_station_capacity(self, station_id: int) -> dict:
        station = self.repo.get_station(station_id)
        if station is None:
            raise ValueError(f"station {station_id} not found")

        max_count, bottleneck = self.recalculate_station_capacity(station_id)
        self.db.commit()
        return {
            "station_id": station.id,
            "station_code": station.code,
            "station_name": station.name,
            "max_open_station_count": max_count,
            "bottleneck_fixture_code": bottleneck,
        }
