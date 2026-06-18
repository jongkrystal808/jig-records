from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.inventory import FixtureStockLevel, FixtureStockSummary
from backend.app.models.master import Fixture, MachineModel, ModelStation, Station
from backend.app.models.production import FixtureRequirement, MachineCapacitySummary


class ProductionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_model_station(self, *, model_id: int, station_id: int) -> ModelStation:
        row = ModelStation(model_id=model_id, station_id=station_id)
        self.db.add(row)
        self.db.flush()
        return row

    def update_model_station(self, row: ModelStation, *, model_id: int, station_id: int) -> ModelStation:
        row.model_id = model_id
        row.station_id = station_id
        self.db.flush()
        return row

    def list_model_stations(self, customer_id: int | None = None) -> list[ModelStation]:
        stmt = select(ModelStation).order_by(ModelStation.model_id, ModelStation.station_id)
        if customer_id is not None:
            stmt = (
                stmt.join(MachineModel, MachineModel.id == ModelStation.model_id)
                .join(Station, Station.id == ModelStation.station_id)
                .where(MachineModel.customer_id == customer_id, Station.customer_id == customer_id)
            )
        return list(self.db.scalars(stmt))

    def get_model_station(self, model_id: int, station_id: int, customer_id: int | None = None) -> ModelStation | None:
        stmt = select(ModelStation).where(ModelStation.model_id == model_id, ModelStation.station_id == station_id)
        if customer_id is not None:
            stmt = (
                stmt.join(MachineModel, MachineModel.id == ModelStation.model_id)
                .join(Station, Station.id == ModelStation.station_id)
                .where(MachineModel.customer_id == customer_id, Station.customer_id == customer_id)
            )
        return self.db.scalar(stmt)

    def get_model_station_by_id(self, row_id: int, customer_id: int | None = None) -> ModelStation | None:
        stmt = select(ModelStation).where(ModelStation.id == row_id)
        if customer_id is not None:
            stmt = (
                stmt.join(MachineModel, MachineModel.id == ModelStation.model_id)
                .join(Station, Station.id == ModelStation.station_id)
                .where(MachineModel.customer_id == customer_id, Station.customer_id == customer_id)
            )
        return self.db.scalar(stmt)

    def delete_model_station(self, row: ModelStation) -> None:
        self.db.delete(row)
        self.db.flush()

    def get_model_by_code(self, code: str, customer_id: int | None = None) -> MachineModel | None:
        stmt = select(MachineModel).where(MachineModel.code == code)
        if customer_id is not None:
            stmt = stmt.where(MachineModel.customer_id == customer_id)
        return self.db.scalar(stmt)

    def count_mapped_models_by_station(self, station_id: int, customer_id: int | None = None) -> int:
        stmt = select(ModelStation.model_id).where(ModelStation.station_id == station_id).distinct()
        if customer_id is not None:
            stmt = stmt.join(MachineModel, MachineModel.id == ModelStation.model_id).where(MachineModel.customer_id == customer_id)
        return len(list(self.db.scalars(stmt)))

    def list_station_ids_by_model(self, model_id: int, customer_id: int | None = None) -> list[int]:
        stmt = select(ModelStation.station_id).where(ModelStation.model_id == model_id)
        if customer_id is not None:
            stmt = stmt.join(Station, Station.id == ModelStation.station_id).where(Station.customer_id == customer_id)
        return list(self.db.scalars(stmt))

    def list_stations_by_model(self, model_id: int, customer_id: int | None = None) -> list[dict]:
        stmt = (
            select(
                Station.id.label("station_id"),
                Station.code.label("station_code"),
                Station.name.label("station_name"),
            )
            .join(ModelStation, ModelStation.station_id == Station.id)
            .where(ModelStation.model_id == model_id)
            .order_by(Station.code)
        )
        if customer_id is not None:
            stmt = stmt.where(Station.customer_id == customer_id)
        return [dict(row._mapping) for row in self.db.execute(stmt).all()]

    def get_model(self, model_id: int, customer_id: int | None = None) -> MachineModel | None:
        stmt = select(MachineModel).where(MachineModel.id == model_id)
        if customer_id is not None:
            stmt = stmt.where(MachineModel.customer_id == customer_id)
        return self.db.scalar(stmt)

    def create_or_update_requirement(self, *, model_id: int, station_id: int, fixture_id: int, required_qty: int) -> FixtureRequirement:
        stmt = select(FixtureRequirement).where(
            FixtureRequirement.model_id == model_id,
            FixtureRequirement.station_id == station_id,
            FixtureRequirement.fixture_id == fixture_id,
        )
        requirement = self.db.scalar(stmt)
        if requirement:
            requirement.required_qty = required_qty
            self.db.flush()
            return requirement

        requirement = FixtureRequirement(
            model_id=model_id,
            station_id=station_id,
            fixture_id=fixture_id,
            required_qty=required_qty,
        )
        self.db.add(requirement)
        self.db.flush()
        return requirement

    def get_requirement(self, *, model_id: int, station_id: int, fixture_id: int) -> FixtureRequirement | None:
        stmt = select(FixtureRequirement).where(
            FixtureRequirement.model_id == model_id,
            FixtureRequirement.station_id == station_id,
            FixtureRequirement.fixture_id == fixture_id,
        )
        return self.db.scalar(stmt)

    def update_requirement(
        self,
        requirement: FixtureRequirement,
        *,
        model_id: int,
        station_id: int,
        fixture_id: int,
        required_qty: int,
    ) -> FixtureRequirement:
        requirement.model_id = model_id
        requirement.station_id = station_id
        requirement.fixture_id = fixture_id
        requirement.required_qty = required_qty
        self.db.flush()
        return requirement

    def get_requirement_by_id(self, requirement_id: int, customer_id: int | None = None) -> FixtureRequirement | None:
        stmt = select(FixtureRequirement).where(FixtureRequirement.id == requirement_id)
        if customer_id is not None:
            stmt = stmt.join(Station, Station.id == FixtureRequirement.station_id).where(Station.customer_id == customer_id)
        return self.db.scalar(stmt)

    def delete_requirement(self, requirement: FixtureRequirement) -> None:
        self.db.delete(requirement)
        self.db.flush()

    def list_station_requirements(
        self,
        station_id: int,
        *,
        model_id: int | None = None,
        customer_id: int | None = None,
    ) -> list[FixtureRequirement]:
        stmt = select(FixtureRequirement).where(FixtureRequirement.station_id == station_id)
        if model_id is not None:
            stmt = stmt.where(FixtureRequirement.model_id == model_id)
        if customer_id is not None:
            stmt = (
                stmt.join(Station, Station.id == FixtureRequirement.station_id)
                .join(MachineModel, MachineModel.id == FixtureRequirement.model_id)
                .where(Station.customer_id == customer_id, MachineModel.customer_id == customer_id)
            )
        return list(self.db.scalars(stmt))

    def list_all_requirements(self, customer_id: int | None = None) -> list[FixtureRequirement]:
        stmt = select(FixtureRequirement).order_by(
            FixtureRequirement.model_id,
            FixtureRequirement.station_id,
            FixtureRequirement.fixture_id,
        )
        if customer_id is not None:
            stmt = (
                stmt.join(MachineModel, MachineModel.id == FixtureRequirement.model_id)
                .join(Station, Station.id == FixtureRequirement.station_id)
                .join(Fixture, Fixture.id == FixtureRequirement.fixture_id)
                .where(
                    MachineModel.customer_id == customer_id,
                    Station.customer_id == customer_id,
                    Fixture.customer_id == customer_id,
                )
            )
        return list(self.db.scalars(stmt))

    def list_requirement_rows(self, customer_id: int | None = None) -> list[dict]:
        stmt = (
            select(
                FixtureRequirement.id.label("id"),
                FixtureRequirement.model_id.label("model_id"),
                MachineModel.code.label("model_code"),
                FixtureRequirement.station_id.label("station_id"),
                Station.code.label("station_code"),
                FixtureRequirement.fixture_id.label("fixture_id"),
                Fixture.code.label("fixture_code"),
                Fixture.name.label("fixture_name"),
                FixtureRequirement.required_qty.label("required_qty"),
            )
            .join(MachineModel, MachineModel.id == FixtureRequirement.model_id)
            .join(Station, Station.id == FixtureRequirement.station_id)
            .join(Fixture, Fixture.id == FixtureRequirement.fixture_id)
            .order_by(MachineModel.code, Station.code, Fixture.code)
        )
        if customer_id is not None:
            stmt = stmt.where(
                MachineModel.customer_id == customer_id,
                Station.customer_id == customer_id,
                Fixture.customer_id == customer_id,
            )
        return [dict(row._mapping) for row in self.db.execute(stmt).all()]

    def list_affected_station_ids_by_fixture(self, fixture_id: int, customer_id: int | None = None) -> list[int]:
        stmt = select(FixtureRequirement.station_id).where(FixtureRequirement.fixture_id == fixture_id).distinct()
        if customer_id is not None:
            stmt = stmt.join(Station, Station.id == FixtureRequirement.station_id).where(Station.customer_id == customer_id)
        return list(self.db.scalars(stmt))

    def list_affected_station_model_pairs_by_fixture(
        self,
        fixture_id: int,
        customer_id: int | None = None,
    ) -> list[tuple[int, int]]:
        stmt = (
            select(FixtureRequirement.station_id, FixtureRequirement.model_id)
            .where(FixtureRequirement.fixture_id == fixture_id)
            .distinct()
        )
        if customer_id is not None:
            stmt = (
                stmt.join(Station, Station.id == FixtureRequirement.station_id)
                .join(MachineModel, MachineModel.id == FixtureRequirement.model_id)
                .where(Station.customer_id == customer_id, MachineModel.customer_id == customer_id)
            )
        return [(int(row.station_id), int(row.model_id)) for row in self.db.execute(stmt).all()]

    def get_fixture(self, fixture_id: int, customer_id: int | None = None) -> Fixture | None:
        stmt = select(Fixture).where(Fixture.id == fixture_id)
        if customer_id is not None:
            stmt = stmt.where(Fixture.customer_id == customer_id)
        return self.db.scalar(stmt)

    def get_stock_level(self, fixture_id: int) -> FixtureStockLevel | None:
        return self.db.get(FixtureStockLevel, fixture_id)

    def get_station(self, station_id: int, customer_id: int | None = None) -> Station | None:
        stmt = select(Station).where(Station.id == station_id)
        if customer_id is not None:
            stmt = stmt.where(Station.customer_id == customer_id)
        return self.db.scalar(stmt)

    def get_station_by_code(self, code: str, customer_id: int | None = None) -> Station | None:
        stmt = select(Station).where(Station.code == code)
        if customer_id is not None:
            stmt = stmt.where(Station.customer_id == customer_id)
        return self.db.scalar(stmt)

    def get_fixture_by_code(self, code: str, customer_id: int | None = None) -> Fixture | None:
        stmt = select(Fixture).where(Fixture.code == code)
        if customer_id is not None:
            stmt = stmt.where(Fixture.customer_id == customer_id)
        return self.db.scalar(stmt)

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
