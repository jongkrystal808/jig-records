from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.app.models.inventory import FixtureStockSummary
from backend.app.models.master import Fixture, MachineModel, Station


class SearchRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def search_fixtures(self, q: str, customer_id: int | None = None) -> list[dict]:
        stmt = (
            select(
                Fixture.id.label("id"),
                Fixture.code.label("code"),
                Fixture.name.label("name"),
                FixtureStockSummary.stock_qty.label("stock_qty"),
                FixtureStockSummary.stock_status.label("stock_status"),
                Fixture.storage_location.label("location_code"),
            )
            .outerjoin(FixtureStockSummary, FixtureStockSummary.fixture_id == Fixture.id)
            .where(or_(Fixture.code.ilike(f"%{q}%"), Fixture.name.ilike(f"%{q}%")))
            .limit(20)
        )
        if customer_id is not None:
            stmt = stmt.where(Fixture.customer_id == customer_id)
        return [dict(row._mapping) for row in self.db.execute(stmt).all()]

    def search_models(self, q: str, customer_id: int | None = None) -> list[MachineModel]:
        stmt = select(MachineModel).where(
            or_(MachineModel.code.ilike(f"%{q}%"), MachineModel.name.ilike(f"%{q}%"))
        )
        if customer_id is not None:
            stmt = stmt.where(MachineModel.customer_id == customer_id)
        stmt = stmt.limit(20)
        return list(self.db.scalars(stmt))

    def search_stations(self, q: str, customer_id: int | None = None) -> list[Station]:
        stmt = select(Station).where(or_(Station.code.ilike(f"%{q}%"), Station.name.ilike(f"%{q}%")))
        if customer_id is not None:
            stmt = stmt.where(Station.customer_id == customer_id)
        stmt = stmt.limit(20)
        return list(self.db.scalars(stmt))
