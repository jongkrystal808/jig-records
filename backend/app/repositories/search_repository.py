from typing import Literal

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from backend.app.models.inventory import FixtureStockSummary
from backend.app.models.master import Fixture, MachineModel, Station


SearchEntityType = Literal["fixture", "model", "station"]


class SearchRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _normalized_query(q: str) -> tuple[str, str, str]:
        normalized = q.strip().lower()
        return normalized, f"{normalized}%", f"%{normalized}%"

    def search_fixtures(self, q: str, *, customer_id: int | None = None, limit: int = 20, offset: int = 0) -> tuple[list[dict], int]:
        normalized, prefix_pattern, contains_pattern = self._normalized_query(q)
        score_expr = case(
            (func.lower(Fixture.code) == normalized, 0),
            (func.lower(Fixture.code).like(prefix_pattern), 10),
            (func.lower(Fixture.name) == normalized, 20),
            (func.lower(Fixture.name).like(prefix_pattern), 30),
            (func.lower(Fixture.code).like(contains_pattern), 40),
            (func.lower(Fixture.name).like(contains_pattern), 50),
            (func.lower(func.coalesce(Fixture.storage_location, "")).like(contains_pattern), 60),
            else_=90,
        ).label("match_score")
        active_rank_expr = case((Fixture.is_active.is_(True), 0), else_=1).label("active_rank")
        conditions = or_(
            func.lower(Fixture.code).like(contains_pattern),
            func.lower(Fixture.name).like(contains_pattern),
            func.lower(func.coalesce(Fixture.storage_location, "")).like(contains_pattern),
        )

        count_stmt = select(func.count()).select_from(Fixture).where(conditions)
        stmt = (
            select(
                Fixture.id.label("id"),
                Fixture.code.label("code"),
                Fixture.name.label("name"),
                Fixture.is_active.label("is_active"),
                FixtureStockSummary.stock_qty.label("stock_qty"),
                FixtureStockSummary.stock_status.label("stock_status"),
                Fixture.storage_location.label("location_code"),
                score_expr,
                active_rank_expr,
            )
            .outerjoin(FixtureStockSummary, FixtureStockSummary.fixture_id == Fixture.id)
            .where(conditions)
        )
        if customer_id is not None:
            count_stmt = count_stmt.where(Fixture.customer_id == customer_id)
            stmt = stmt.where(Fixture.customer_id == customer_id)
        stmt = stmt.order_by(active_rank_expr, score_expr, Fixture.code.asc()).offset(offset).limit(limit)
        total = int(self.db.scalar(count_stmt) or 0)
        return [dict(row._mapping) for row in self.db.execute(stmt).all()], total

    def search_models(self, q: str, *, customer_id: int | None = None, limit: int = 20, offset: int = 0) -> tuple[list[dict], int]:
        normalized, prefix_pattern, contains_pattern = self._normalized_query(q)
        score_expr = case(
            (func.lower(MachineModel.code) == normalized, 0),
            (func.lower(MachineModel.code).like(prefix_pattern), 10),
            (func.lower(MachineModel.name) == normalized, 20),
            (func.lower(MachineModel.name).like(prefix_pattern), 30),
            (func.lower(MachineModel.code).like(contains_pattern), 40),
            (func.lower(MachineModel.name).like(contains_pattern), 50),
            else_=90,
        ).label("match_score")
        active_rank_expr = case((MachineModel.is_active.is_(True), 0), else_=1).label("active_rank")
        conditions = or_(
            func.lower(MachineModel.code).like(contains_pattern),
            func.lower(MachineModel.name).like(contains_pattern),
        )

        count_stmt = select(func.count()).select_from(MachineModel).where(conditions)
        stmt = (
            select(
                MachineModel.id.label("id"),
                MachineModel.code.label("code"),
                MachineModel.name.label("name"),
                MachineModel.is_active.label("is_active"),
                score_expr,
                active_rank_expr,
            )
            .where(conditions)
        )
        if customer_id is not None:
            count_stmt = count_stmt.where(MachineModel.customer_id == customer_id)
            stmt = stmt.where(MachineModel.customer_id == customer_id)
        stmt = stmt.order_by(active_rank_expr, score_expr, MachineModel.code.asc()).offset(offset).limit(limit)
        total = int(self.db.scalar(count_stmt) or 0)
        return [dict(row._mapping) for row in self.db.execute(stmt).all()], total

    def search_stations(self, q: str, *, customer_id: int | None = None, limit: int = 20, offset: int = 0) -> tuple[list[dict], int]:
        normalized, prefix_pattern, contains_pattern = self._normalized_query(q)
        score_expr = case(
            (func.lower(Station.code) == normalized, 0),
            (func.lower(Station.code).like(prefix_pattern), 10),
            (func.lower(Station.name) == normalized, 20),
            (func.lower(Station.name).like(prefix_pattern), 30),
            (func.lower(Station.code).like(contains_pattern), 40),
            (func.lower(Station.name).like(contains_pattern), 50),
            else_=90,
        ).label("match_score")
        active_rank_expr = case((Station.is_active.is_(True), 0), else_=1).label("active_rank")
        conditions = or_(
            func.lower(Station.code).like(contains_pattern),
            func.lower(Station.name).like(contains_pattern),
        )

        count_stmt = select(func.count()).select_from(Station).where(conditions)
        stmt = (
            select(
                Station.id.label("id"),
                Station.code.label("code"),
                Station.name.label("name"),
                Station.is_active.label("is_active"),
                score_expr,
                active_rank_expr,
            )
            .where(conditions)
        )
        if customer_id is not None:
            count_stmt = count_stmt.where(Station.customer_id == customer_id)
            stmt = stmt.where(Station.customer_id == customer_id)
        stmt = stmt.order_by(active_rank_expr, score_expr, Station.code.asc()).offset(offset).limit(limit)
        total = int(self.db.scalar(count_stmt) or 0)
        return [dict(row._mapping) for row in self.db.execute(stmt).all()], total

    def search_entities(
        self,
        entity_type: SearchEntityType,
        q: str,
        *,
        customer_id: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        if entity_type == "fixture":
            return self.search_fixtures(q, customer_id=customer_id, limit=limit, offset=offset)
        if entity_type == "model":
            return self.search_models(q, customer_id=customer_id, limit=limit, offset=offset)
        return self.search_stations(q, customer_id=customer_id, limit=limit, offset=offset)
