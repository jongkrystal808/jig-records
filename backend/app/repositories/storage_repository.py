from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from backend.app.models.inventory import FixtureStockSummary
from backend.app.models.master import Fixture, MachineModel, Station
from backend.app.models.production import FixtureRequirement
from backend.app.models.storage import FixturePlacement, StorageCode, StorageContainer


class StorageRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_fixture(self, fixture_id: int) -> Fixture | None:
        return self.db.get(Fixture, fixture_id)

    def get_stock_qty(self, fixture_id: int) -> int:
        return int(
            self.db.scalar(
                select(FixtureStockSummary.stock_qty).where(FixtureStockSummary.fixture_id == fixture_id)
            )
            or 0
        )

    def list_station_options(self, fixture_id: int, customer_id: int) -> list[dict]:
        stmt = (
            select(
                MachineModel.id.label("model_id"),
                MachineModel.code.label("model_code"),
                MachineModel.name.label("model_name"),
                Station.id.label("station_id"),
                Station.code.label("station_code"),
                Station.name.label("station_name"),
            )
            .join(FixtureRequirement, FixtureRequirement.model_id == MachineModel.id)
            .join(Station, Station.id == FixtureRequirement.station_id)
            .where(
                FixtureRequirement.fixture_id == fixture_id,
                MachineModel.customer_id == customer_id,
                Station.customer_id == customer_id,
            )
            .distinct()
            .order_by(MachineModel.code, Station.code)
        )
        return [dict(row._mapping) for row in self.db.execute(stmt)]

    def get_container(self, container_id: int, customer_id: int | None = None) -> StorageContainer | None:
        stmt = select(StorageContainer).where(StorageContainer.id == container_id)
        if customer_id is not None:
            stmt = stmt.where(StorageContainer.customer_id == customer_id)
        return self.db.scalar(stmt)

    def create_container(self, *, customer_id: int, name: str, description: str | None) -> StorageContainer:
        row = StorageContainer(customer_id=customer_id, name=name, description=description)
        self.db.add(row)
        self.db.flush()
        return row

    def delete_container(self, row: StorageContainer) -> None:
        self.db.execute(
            StorageCode.__table__.update()
            .where(StorageCode.container_id == row.id)
            .values(container_id=None)
        )
        self.db.delete(row)
        self.db.flush()

    def get_code(self, code_id: int, customer_id: int | None = None) -> StorageCode | None:
        stmt = select(StorageCode).where(StorageCode.id == code_id)
        if customer_id is not None:
            stmt = stmt.where(StorageCode.customer_id == customer_id)
        return self.db.scalar(stmt)

    def get_code_by_value(self, customer_id: int, code: str) -> StorageCode | None:
        return self.db.scalar(
            select(StorageCode).where(StorageCode.customer_id == customer_id, StorageCode.code == code)
        )

    def get_or_create_code(self, customer_id: int, code: str) -> StorageCode:
        row = self.get_code_by_value(customer_id, code)
        if row is not None:
            return row
        row = StorageCode(customer_id=customer_id, code=code, is_active=True)
        self.db.add(row)
        self.db.flush()
        return row

    def list_containers(self, customer_id: int, keyword: str = "") -> list[StorageContainer]:
        stmt = select(StorageContainer).where(StorageContainer.customer_id == customer_id)
        normalized = keyword.strip()
        if normalized:
            stmt = stmt.where(
                or_(StorageContainer.name.ilike(f"%{normalized}%"), StorageContainer.description.ilike(f"%{normalized}%"))
            )
        return list(self.db.scalars(stmt.order_by(StorageContainer.name)))

    def list_codes(self, customer_id: int, keyword: str = "") -> list[StorageCode]:
        stmt = select(StorageCode).where(StorageCode.customer_id == customer_id)
        normalized = keyword.strip()
        if normalized:
            matching_container_ids = select(StorageContainer.id).where(
                StorageContainer.customer_id == customer_id,
                StorageContainer.name.ilike(f"%{normalized}%"),
            )
            stmt = stmt.where(
                or_(StorageCode.code.ilike(f"%{normalized}%"), StorageCode.container_id.in_(matching_container_ids))
            )
        return list(self.db.scalars(stmt.order_by(StorageCode.code)))

    def list_placements(self, fixture_id: int) -> list[FixturePlacement]:
        return list(
            self.db.scalars(
                select(FixturePlacement)
                .where(FixturePlacement.fixture_id == fixture_id)
                .order_by(FixturePlacement.target_type, FixturePlacement.id)
            )
        )

    def placement_counts_for_code(self, code_id: int) -> tuple[int, int, int]:
        row = self.db.execute(
            select(
                func.count(func.distinct(FixturePlacement.fixture_id)),
                func.coalesce(func.sum(FixturePlacement.quantity), 0),
                func.coalesce(func.sum(case((FixturePlacement.quantity.is_(None), 1), else_=0)), 0),
            ).where(FixturePlacement.storage_code_id == code_id)
        ).one()
        return int(row[0] or 0), int(row[1] or 0), int(row[2] or 0)

    def create_placement(self, **values) -> FixturePlacement:
        row = FixturePlacement(**values)
        self.db.add(row)
        self.db.flush()
        return row

    def delete_placement(self, row: FixturePlacement) -> None:
        self.db.delete(row)
        self.db.flush()

    def clear_placements(self, fixture_id: int) -> None:
        for row in self.list_placements(fixture_id):
            self.db.delete(row)
        self.db.flush()

    def has_requirement(self, fixture_id: int, model_id: int, station_id: int) -> bool:
        return self.db.scalar(
            select(FixtureRequirement.id).where(
                FixtureRequirement.fixture_id == fixture_id,
                FixtureRequirement.model_id == model_id,
                FixtureRequirement.station_id == station_id,
            )
        ) is not None

    def get_model(self, model_id: int) -> MachineModel | None:
        return self.db.get(MachineModel, model_id)

    def get_station(self, station_id: int) -> Station | None:
        return self.db.get(Station, station_id)
