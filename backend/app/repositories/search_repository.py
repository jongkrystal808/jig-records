from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.app.models.inventory import FixtureSerial, FixtureStockSummary
from backend.app.models.master import Fixture, MachineModel, Station
from backend.app.models.warehouse import FixtureLocationAssignment, StorageLocation


class SearchRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def search_fixtures(self, q: str) -> list[dict]:
        stmt = (
            select(
                Fixture.id.label("id"),
                Fixture.code.label("code"),
                Fixture.name.label("name"),
                FixtureStockSummary.stock_qty.label("stock_qty"),
                FixtureStockSummary.stock_status.label("stock_status"),
                StorageLocation.code.label("location_code"),
            )
            .outerjoin(FixtureStockSummary, FixtureStockSummary.fixture_id == Fixture.id)
            .outerjoin(FixtureLocationAssignment, FixtureLocationAssignment.fixture_id == Fixture.id)
            .outerjoin(StorageLocation, StorageLocation.id == FixtureLocationAssignment.location_id)
            .where(or_(Fixture.code.ilike(f"%{q}%"), Fixture.name.ilike(f"%{q}%")))
            .limit(20)
        )
        return [dict(row._mapping) for row in self.db.execute(stmt).all()]

    def search_models(self, q: str) -> list[MachineModel]:
        stmt = select(MachineModel).where(
            or_(MachineModel.code.ilike(f"%{q}%"), MachineModel.name.ilike(f"%{q}%"))
        ).limit(20)
        return list(self.db.scalars(stmt))

    def search_stations(self, q: str) -> list[Station]:
        stmt = select(Station).where(or_(Station.code.ilike(f"%{q}%"), Station.name.ilike(f"%{q}%"))).limit(20)
        return list(self.db.scalars(stmt))

    def search_locations(self, q: str) -> list[StorageLocation]:
        stmt = select(StorageLocation).where(StorageLocation.code.ilike(f"%{q}%")).limit(20)
        return list(self.db.scalars(stmt))

    def search_serials(self, q: str) -> list[dict]:
        stmt = (
            select(FixtureSerial.id, FixtureSerial.serial_no, Fixture.code, Fixture.name)
            .join(Fixture, Fixture.id == FixtureSerial.fixture_id)
            .where(FixtureSerial.serial_no.ilike(f"%{q}%"))
            .limit(20)
        )
        return [dict(row._mapping) for row in self.db.execute(stmt).all()]
