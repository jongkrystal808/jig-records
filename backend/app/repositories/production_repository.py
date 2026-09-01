from collections.abc import Iterator

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, selectinload

from backend.app.models.inventory import (
    FixtureStockLevel,
    FixtureStockSummary,
    MaterialTransaction,
    MaterialTransactionItem,
)
from backend.app.models.master import Fixture, MachineModel, ModelStation, Station
from backend.app.models.production import (
    FixtureRequirement,
    FixtureRequirementIdentifier,
    MachineCapacitySummary,
)


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

    def list_model_stations_page(
        self,
        *,
        customer_id: int,
        page: int,
        page_size: int,
        model_id: int | None = None,
        station_id: int | None = None,
        keyword: str = "",
    ) -> tuple[list[dict], int]:
        stmt = (
            select(
                ModelStation.id.label("id"),
                ModelStation.model_id.label("model_id"),
                ModelStation.station_id.label("station_id"),
                MachineModel.code.label("model_code"),
                MachineModel.name.label("model_name"),
                Station.code.label("station_code"),
                Station.name.label("station_name"),
            )
            .join(MachineModel, MachineModel.id == ModelStation.model_id)
            .join(Station, Station.id == ModelStation.station_id)
            .where(MachineModel.customer_id == customer_id, Station.customer_id == customer_id)
        )
        if model_id is not None:
            stmt = stmt.where(ModelStation.model_id == model_id)
        if station_id is not None:
            stmt = stmt.where(ModelStation.station_id == station_id)
        normalized = keyword.strip()
        if normalized:
            pattern = f"%{normalized}%"
            stmt = stmt.where(or_(MachineModel.code.ilike(pattern), MachineModel.name.ilike(pattern), Station.code.ilike(pattern), Station.name.ilike(pattern)))
        total = int(self.db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0)
        rows = self.db.execute(stmt.order_by(MachineModel.code, Station.code).offset((page - 1) * page_size).limit(page_size)).all()
        return [dict(row._mapping) for row in rows], total

    def iter_model_station_rows(
        self,
        *,
        customer_id: int,
        model_id: int | None = None,
        station_id: int | None = None,
        keyword: str = "",
    ) -> Iterator[dict]:
        stmt = (
            select(
                MachineModel.code.label("model_code"),
                MachineModel.name.label("model_name"),
                Station.code.label("station_code"),
                Station.name.label("station_name"),
            )
            .join(ModelStation, ModelStation.model_id == MachineModel.id)
            .join(Station, Station.id == ModelStation.station_id)
            .where(MachineModel.customer_id == customer_id, Station.customer_id == customer_id)
        )
        if model_id is not None:
            stmt = stmt.where(ModelStation.model_id == model_id)
        if station_id is not None:
            stmt = stmt.where(ModelStation.station_id == station_id)
        normalized = keyword.strip()
        if normalized:
            pattern = f"%{normalized}%"
            stmt = stmt.where(
                or_(
                    MachineModel.code.ilike(pattern),
                    MachineModel.name.ilike(pattern),
                    Station.code.ilike(pattern),
                    Station.name.ilike(pattern),
                )
            )
        rows = self.db.execute(
            stmt.order_by(MachineModel.code, Station.code).execution_options(yield_per=500)
        )
        for row in rows:
            yield dict(row._mapping)

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

    @staticmethod
    def _replace_designated_identifiers(
        requirement: FixtureRequirement,
        *,
        designated_mode: bool,
        designated_identifiers: list[str],
    ) -> None:
        requirement.designated_mode = designated_mode
        requirement.designated_identifier_rows = [
            FixtureRequirementIdentifier(identifier=identifier)
            for identifier in designated_identifiers
        ] if designated_mode else []

    def create_or_update_requirement(
        self,
        *,
        model_id: int,
        station_id: int,
        fixture_id: int,
        required_qty: int,
        designated_mode: bool | None = None,
        designated_identifiers: list[str] | None = None,
    ) -> FixtureRequirement:
        stmt = select(FixtureRequirement).options(selectinload(FixtureRequirement.designated_identifier_rows)).where(
            FixtureRequirement.model_id == model_id,
            FixtureRequirement.station_id == station_id,
            FixtureRequirement.fixture_id == fixture_id,
        )
        requirement = self.db.scalar(stmt)
        if requirement:
            requirement.required_qty = required_qty
            if designated_mode is not None:
                self._replace_designated_identifiers(
                    requirement,
                    designated_mode=designated_mode,
                    designated_identifiers=designated_identifiers or [],
                )
            self.db.flush()
            return requirement

        requirement = FixtureRequirement(
            model_id=model_id,
            station_id=station_id,
            fixture_id=fixture_id,
            required_qty=required_qty,
            designated_mode=False,
        )
        if designated_mode:
            self._replace_designated_identifiers(
                requirement,
                designated_mode=True,
                designated_identifiers=designated_identifiers or [],
            )
        self.db.add(requirement)
        self.db.flush()
        return requirement

    def get_requirement(self, *, model_id: int, station_id: int, fixture_id: int) -> FixtureRequirement | None:
        stmt = select(FixtureRequirement).options(selectinload(FixtureRequirement.designated_identifier_rows)).where(
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
        designated_mode: bool | None = None,
        designated_identifiers: list[str] | None = None,
    ) -> FixtureRequirement:
        requirement.model_id = model_id
        requirement.station_id = station_id
        requirement.fixture_id = fixture_id
        requirement.required_qty = required_qty
        if designated_mode is not None:
            self._replace_designated_identifiers(
                requirement,
                designated_mode=designated_mode,
                designated_identifiers=designated_identifiers or [],
            )
        self.db.flush()
        return requirement

    def get_requirement_by_id(self, requirement_id: int, customer_id: int | None = None) -> FixtureRequirement | None:
        stmt = select(FixtureRequirement).options(selectinload(FixtureRequirement.designated_identifier_rows)).where(FixtureRequirement.id == requirement_id)
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
        stmt = select(FixtureRequirement).options(selectinload(FixtureRequirement.designated_identifier_rows)).where(FixtureRequirement.station_id == station_id)
        if model_id is not None:
            stmt = stmt.where(FixtureRequirement.model_id == model_id)
        if customer_id is not None:
            stmt = (
                stmt.join(Station, Station.id == FixtureRequirement.station_id)
                .join(MachineModel, MachineModel.id == FixtureRequirement.model_id)
                .where(Station.customer_id == customer_id, MachineModel.customer_id == customer_id)
            )
        return list(self.db.scalars(stmt))

    def list_model_query_requirement_rows(
        self,
        *,
        model_id: int,
        station_ids: list[int],
        customer_id: int | None = None,
    ) -> list[dict]:
        if not station_ids:
            return []
        signed_qty = case(
            (MaterialTransaction.transaction_type == "receipt", MaterialTransactionItem.quantity),
            else_=-MaterialTransactionItem.quantity,
        )
        designated_stock = (
            select(
                FixtureRequirementIdentifier.requirement_id.label("requirement_id"),
                func.coalesce(func.sum(signed_qty), 0).label("stock_qty"),
            )
            .select_from(FixtureRequirementIdentifier)
            .join(
                FixtureRequirement,
                FixtureRequirement.id == FixtureRequirementIdentifier.requirement_id,
            )
            .join(
                MaterialTransactionItem,
                (MaterialTransactionItem.fixture_id == FixtureRequirement.fixture_id)
                & (MaterialTransactionItem.identifier == FixtureRequirementIdentifier.identifier),
            )
            .join(MaterialTransaction, MaterialTransaction.id == MaterialTransactionItem.transaction_id)
            .group_by(FixtureRequirementIdentifier.requirement_id)
            .subquery("model_query_designated_stock")
        )
        stmt = (
            select(
                FixtureRequirement.id.label("id"),
                FixtureRequirement.station_id.label("station_id"),
                FixtureRequirement.fixture_id.label("fixture_id"),
                Fixture.code.label("fixture_code"),
                Fixture.name.label("fixture_name"),
                FixtureRequirement.required_qty.label("required_qty"),
                FixtureRequirement.designated_mode.label("designated_mode"),
                case(
                    (
                        FixtureRequirement.designated_mode.is_(True),
                        func.coalesce(designated_stock.c.stock_qty, 0),
                    ),
                    else_=func.coalesce(FixtureStockSummary.stock_qty, 0),
                ).label("stock_qty"),
                func.coalesce(FixtureStockLevel.min_stock_qty, 0).label("min_stock_qty"),
            )
            .join(MachineModel, MachineModel.id == FixtureRequirement.model_id)
            .join(Station, Station.id == FixtureRequirement.station_id)
            .join(Fixture, Fixture.id == FixtureRequirement.fixture_id)
            .outerjoin(FixtureStockSummary, FixtureStockSummary.fixture_id == FixtureRequirement.fixture_id)
            .outerjoin(FixtureStockLevel, FixtureStockLevel.fixture_id == FixtureRequirement.fixture_id)
            .outerjoin(
                designated_stock,
                designated_stock.c.requirement_id == FixtureRequirement.id,
            )
            .where(
                FixtureRequirement.model_id == model_id,
                FixtureRequirement.station_id.in_(station_ids),
            )
        )
        if customer_id is not None:
            stmt = stmt.where(
                MachineModel.customer_id == customer_id,
                Station.customer_id == customer_id,
                Fixture.customer_id == customer_id,
            )
        rows = [
            dict(row._mapping)
            for row in self.db.execute(
                stmt.order_by(FixtureRequirement.station_id, Fixture.code)
            ).all()
        ]
        requirement_ids = [int(row["id"]) for row in rows]
        identifiers_by_requirement = {requirement_id: [] for requirement_id in requirement_ids}
        if requirement_ids:
            identifier_rows = self.db.execute(
                select(
                    FixtureRequirementIdentifier.requirement_id,
                    FixtureRequirementIdentifier.identifier,
                )
                .where(FixtureRequirementIdentifier.requirement_id.in_(requirement_ids))
                .order_by(
                    FixtureRequirementIdentifier.requirement_id,
                    FixtureRequirementIdentifier.identifier,
                )
            ).all()
            for requirement_id, identifier in identifier_rows:
                identifiers_by_requirement[int(requirement_id)].append(str(identifier))
        for row in rows:
            row["designated_mode"] = bool(row["designated_mode"])
            row["designated_identifiers"] = identifiers_by_requirement[int(row["id"])]
            row["stock_qty"] = int(row["stock_qty"] or 0)
            row["min_stock_qty"] = int(row["min_stock_qty"] or 0)
        return rows

    def list_all_requirements(self, customer_id: int | None = None) -> list[FixtureRequirement]:
        stmt = select(FixtureRequirement).options(selectinload(FixtureRequirement.designated_identifier_rows)).order_by(
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
        return self._attach_designated_identifiers([dict(row._mapping) for row in self.db.execute(stmt).all()])

    def list_requirement_rows_page(
        self,
        *,
        customer_id: int,
        page: int,
        page_size: int,
        model_id: int | None = None,
        station_id: int | None = None,
        keyword: str = "",
    ) -> tuple[list[dict], int]:
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
                FixtureRequirement.designated_mode.label("designated_mode"),
                func.coalesce(FixtureStockSummary.stock_qty, 0).label("stock_qty"),
            )
            .join(MachineModel, MachineModel.id == FixtureRequirement.model_id)
            .join(Station, Station.id == FixtureRequirement.station_id)
            .join(Fixture, Fixture.id == FixtureRequirement.fixture_id)
            .outerjoin(FixtureStockSummary, FixtureStockSummary.fixture_id == FixtureRequirement.fixture_id)
            .where(
                MachineModel.customer_id == customer_id,
                Station.customer_id == customer_id,
                Fixture.customer_id == customer_id,
            )
        )
        if model_id is not None:
            stmt = stmt.where(FixtureRequirement.model_id == model_id)
        if station_id is not None:
            stmt = stmt.where(FixtureRequirement.station_id == station_id)
        normalized = keyword.strip()
        if normalized:
            pattern = f"%{normalized}%"
            stmt = stmt.where(or_(MachineModel.code.ilike(pattern), Station.code.ilike(pattern), Fixture.code.ilike(pattern), Fixture.name.ilike(pattern)))
        total = int(self.db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0)
        rows = self.db.execute(stmt.order_by(MachineModel.code, Station.code, Fixture.code).offset((page - 1) * page_size).limit(page_size)).all()
        return self._attach_designated_identifiers([dict(row._mapping) for row in rows]), total

    def _attach_designated_identifiers(self, rows: list[dict]) -> list[dict]:
        requirement_ids = [int(row["id"]) for row in rows]
        requirements = {
            requirement.id: requirement
            for requirement in self.db.scalars(
                select(FixtureRequirement)
                .options(selectinload(FixtureRequirement.designated_identifier_rows))
                .where(FixtureRequirement.id.in_(requirement_ids))
            )
        } if requirement_ids else {}
        for row in rows:
            requirement_id = int(row["id"])
            requirement = requirements.get(requirement_id)
            row["designated_mode"] = bool(requirement and requirement.designated_mode)
            row["designated_identifiers"] = [] if requirement is None else requirement.designated_identifiers
            if requirement is not None and requirement.designated_mode and "stock_qty" in row:
                row["stock_qty"] = self.get_requirement_stock_qty(requirement)
        return rows

    def iter_requirement_export_rows(
        self,
        *,
        customer_id: int,
        model_id: int | None = None,
        station_id: int | None = None,
        keyword: str = "",
    ) -> Iterator[dict]:
        signed_qty = case(
            (MaterialTransaction.transaction_type == "receipt", MaterialTransactionItem.quantity),
            else_=-MaterialTransactionItem.quantity,
        )
        designated_stock_qty = (
            select(func.coalesce(func.sum(signed_qty), 0))
            .select_from(FixtureRequirementIdentifier)
            .join(
                MaterialTransactionItem,
                (MaterialTransactionItem.fixture_id == FixtureRequirement.fixture_id)
                & (MaterialTransactionItem.identifier == FixtureRequirementIdentifier.identifier),
            )
            .join(MaterialTransaction, MaterialTransaction.id == MaterialTransactionItem.transaction_id)
            .where(FixtureRequirementIdentifier.requirement_id == FixtureRequirement.id)
            .correlate(FixtureRequirement)
            .scalar_subquery()
        )
        designated_identifier_text = (
            select(func.group_concat(FixtureRequirementIdentifier.identifier))
            .where(FixtureRequirementIdentifier.requirement_id == FixtureRequirement.id)
            .correlate(FixtureRequirement)
            .scalar_subquery()
        )
        stmt = (
            select(
                MachineModel.code.label("model_code"),
                Station.code.label("station_code"),
                Fixture.code.label("fixture_code"),
                Fixture.name.label("fixture_name"),
                FixtureRequirement.required_qty.label("required_qty"),
                FixtureRequirement.designated_mode.label("designated_mode"),
                func.coalesce(designated_identifier_text, "").label("designated_identifiers"),
                case(
                    (FixtureRequirement.designated_mode.is_(True), designated_stock_qty),
                    else_=func.coalesce(FixtureStockSummary.stock_qty, 0),
                ).label("stock_qty"),
            )
            .join(MachineModel, MachineModel.id == FixtureRequirement.model_id)
            .join(Station, Station.id == FixtureRequirement.station_id)
            .join(Fixture, Fixture.id == FixtureRequirement.fixture_id)
            .outerjoin(FixtureStockSummary, FixtureStockSummary.fixture_id == FixtureRequirement.fixture_id)
            .where(
                MachineModel.customer_id == customer_id,
                Station.customer_id == customer_id,
                Fixture.customer_id == customer_id,
            )
        )
        if model_id is not None:
            stmt = stmt.where(FixtureRequirement.model_id == model_id)
        if station_id is not None:
            stmt = stmt.where(FixtureRequirement.station_id == station_id)
        normalized = keyword.strip()
        if normalized:
            pattern = f"%{normalized}%"
            stmt = stmt.where(
                or_(
                    MachineModel.code.ilike(pattern),
                    Station.code.ilike(pattern),
                    Fixture.code.ilike(pattern),
                    Fixture.name.ilike(pattern),
                )
            )
        rows = self.db.execute(
            stmt.order_by(MachineModel.code, Station.code, Fixture.code).execution_options(yield_per=500)
        )
        for row in rows:
            yield dict(row._mapping)

    def list_requirement_rows_by_fixture(self, fixture_id: int, customer_id: int | None = None) -> list[dict]:
        stmt = (
            select(
                FixtureRequirement.model_id.label("model_id"),
                MachineModel.code.label("model_code"),
                MachineModel.name.label("model_name"),
                FixtureRequirement.station_id.label("station_id"),
                Station.code.label("station_code"),
                Station.name.label("station_name"),
                FixtureRequirement.required_qty.label("required_qty"),
            )
            .join(MachineModel, MachineModel.id == FixtureRequirement.model_id)
            .join(Station, Station.id == FixtureRequirement.station_id)
            .join(Fixture, Fixture.id == FixtureRequirement.fixture_id)
            .where(FixtureRequirement.fixture_id == fixture_id)
            .order_by(MachineModel.code, Station.code)
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

    def get_requirement_stock_qty(self, requirement: FixtureRequirement) -> int:
        if not requirement.designated_mode:
            return self.get_stock_qty(requirement.fixture_id)
        signed_qty = case(
            (MaterialTransaction.transaction_type == "receipt", MaterialTransactionItem.quantity),
            else_=-MaterialTransactionItem.quantity,
        )
        stock_qty = self.db.scalar(
            select(func.coalesce(func.sum(signed_qty), 0))
            .select_from(FixtureRequirementIdentifier)
            .join(
                MaterialTransactionItem,
                (MaterialTransactionItem.fixture_id == requirement.fixture_id)
                & (MaterialTransactionItem.identifier == FixtureRequirementIdentifier.identifier),
            )
            .join(MaterialTransaction, MaterialTransaction.id == MaterialTransactionItem.transaction_id)
            .where(FixtureRequirementIdentifier.requirement_id == requirement.id)
        )
        return int(stock_qty or 0)

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
