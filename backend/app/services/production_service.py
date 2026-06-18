from math import floor
from sqlalchemy.exc import IntegrityError

from sqlalchemy.orm import Session

from backend.app.core.auth import SessionContext
from backend.app.repositories.production_repository import ProductionRepository
from backend.app.schemas.common import CsvImportPayload
from backend.app.schemas.production import FixtureRequirementCreate, ModelStationCreate
from backend.app.services.audit_service import AuditService
from backend.app.utils.csv_tools import parse_csv_bytes, render_csv_text


class ProductionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProductionRepository(db)
        self.audit = AuditService(db)

    def create_model_station(self, payload: ModelStationCreate, actor: SessionContext | None = None):
        model = self.repo.get_model(payload.model_id, customer_id=payload.customer_id)
        if model is None:
            raise ValueError(f"model {payload.model_id} not found")

        station = self.repo.get_station(payload.station_id, customer_id=payload.customer_id)
        if station is None:
            raise ValueError(f"station {payload.station_id} not found")

        try:
            model_station = self.repo.create_model_station(model_id=payload.model_id, station_id=payload.station_id)
            self.audit.record(
                customer_id=payload.customer_id,
                entity_type="model_station",
                entity_key=f"{model.code}->{station.code}",
                action="create",
                summary=f"建立機種站點對應 {model.code} / {station.code}",
                actor=actor,
            )
            self.db.commit()
            self.db.refresh(model_station)
            return model_station
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("model-station mapping already exists") from exc

    def update_model_station(self, row_id: int, payload: ModelStationCreate, actor: SessionContext | None = None):
        row = self.repo.get_model_station_by_id(row_id, customer_id=payload.customer_id)
        if row is None:
            raise ValueError(f"mapping {row_id} not found")

        model = self.repo.get_model(payload.model_id, customer_id=payload.customer_id)
        if model is None:
            raise ValueError(f"model {payload.model_id} not found")

        station = self.repo.get_station(payload.station_id, customer_id=payload.customer_id)
        if station is None:
            raise ValueError(f"station {payload.station_id} not found")

        existing = self.repo.get_model_station(payload.model_id, payload.station_id, customer_id=payload.customer_id)
        if existing is not None and existing.id != row_id:
            raise ValueError("model-station mapping already exists")

        try:
            updated = self.repo.update_model_station(row, model_id=payload.model_id, station_id=payload.station_id)
            self.audit.record(
                customer_id=payload.customer_id,
                entity_type="model_station",
                entity_key=f"{model.code}->{station.code}",
                action="update",
                summary=f"更新機種站點對應 {model.code} / {station.code}",
                actor=actor,
            )
            self.db.commit()
            self.db.refresh(updated)
            return updated
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("model-station mapping already exists") from exc

    def list_model_stations(self, customer_id: int | None = None):
        return self.repo.list_model_stations(customer_id=customer_id)

    def delete_model_station(self, row_id: int, customer_id: int | None = None, actor: SessionContext | None = None) -> None:
        row = self.repo.get_model_station_by_id(row_id, customer_id=customer_id)
        if row is None:
            raise ValueError(f"mapping {row_id} not found")
        model = self.repo.get_model(row.model_id, customer_id=customer_id)
        station = self.repo.get_station(row.station_id, customer_id=customer_id)
        self.repo.delete_model_station(row)
        self.audit.record(
            customer_id=customer_id,
            entity_type="model_station",
            entity_key=f"{model.code if model else row.model_id}->{station.code if station else row.station_id}",
            action="delete",
            summary=f"刪除機種站點對應 {model.code if model else row.model_id} / {station.code if station else row.station_id}",
            actor=actor,
        )
        self.db.commit()

    def create_fixture_requirement(self, payload: FixtureRequirementCreate, actor: SessionContext | None = None):
        model = self.repo.get_model(payload.model_id, customer_id=payload.customer_id)
        if model is None:
            raise ValueError(f"model {payload.model_id} not found")

        fixture = self.repo.get_fixture(payload.fixture_id, customer_id=payload.customer_id)
        if fixture is None:
            raise ValueError(f"fixture {payload.fixture_id} not found")

        station = self.repo.get_station(payload.station_id, customer_id=payload.customer_id)
        if station is None:
            raise ValueError(f"station {payload.station_id} not found")

        if self.repo.get_model_station(payload.model_id, payload.station_id, customer_id=payload.customer_id) is None:
            raise ValueError("station is not mapped to the selected model")

        requirement = self.repo.create_or_update_requirement(
            model_id=payload.model_id,
            station_id=payload.station_id,
            fixture_id=payload.fixture_id,
            required_qty=payload.required_qty,
        )
        self.audit.record(
            customer_id=payload.customer_id,
            entity_type="fixture_requirement",
            entity_key=f"{model.code}->{station.code}->{fixture.code}",
            action="create",
            summary=f"建立治具需求 {model.code} / {station.code} / {fixture.code} = {payload.required_qty}",
            actor=actor,
        )
        self.db.commit()
        self.db.refresh(requirement)
        return requirement

    def update_fixture_requirement(self, requirement_id: int, payload: FixtureRequirementCreate, actor: SessionContext | None = None):
        requirement = self.repo.get_requirement_by_id(requirement_id, customer_id=payload.customer_id)
        if requirement is None:
            raise ValueError(f"requirement {requirement_id} not found")

        model = self.repo.get_model(payload.model_id, customer_id=payload.customer_id)
        if model is None:
            raise ValueError(f"model {payload.model_id} not found")

        fixture = self.repo.get_fixture(payload.fixture_id, customer_id=payload.customer_id)
        if fixture is None:
            raise ValueError(f"fixture {payload.fixture_id} not found")

        station = self.repo.get_station(payload.station_id, customer_id=payload.customer_id)
        if station is None:
            raise ValueError(f"station {payload.station_id} not found")

        if self.repo.get_model_station(payload.model_id, payload.station_id, customer_id=payload.customer_id) is None:
            raise ValueError("station is not mapped to the selected model")

        existing = self.repo.get_requirement(
            model_id=payload.model_id,
            station_id=payload.station_id,
            fixture_id=payload.fixture_id,
        )
        if existing is not None and existing.id != requirement_id:
            raise ValueError("fixture requirement already exists")

        try:
            updated = self.repo.update_requirement(
                requirement,
                model_id=payload.model_id,
                station_id=payload.station_id,
                fixture_id=payload.fixture_id,
                required_qty=payload.required_qty,
            )
            self.audit.record(
                customer_id=payload.customer_id,
                entity_type="fixture_requirement",
                entity_key=f"{model.code}->{station.code}->{fixture.code}",
                action="update",
                summary=f"更新治具需求 {model.code} / {station.code} / {fixture.code} = {payload.required_qty}",
                actor=actor,
            )
            self.db.commit()
            self.db.refresh(updated)
            return updated
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("fixture requirement already exists") from exc

    def delete_fixture_requirement(self, requirement_id: int, customer_id: int | None = None, actor: SessionContext | None = None) -> None:
        requirement = self.repo.get_requirement_by_id(requirement_id, customer_id=customer_id)
        if requirement is None:
            raise ValueError(f"requirement {requirement_id} not found")
        model = self.repo.get_model(requirement.model_id, customer_id=customer_id)
        station = self.repo.get_station(requirement.station_id, customer_id=customer_id)
        fixture = self.repo.get_fixture(requirement.fixture_id, customer_id=customer_id)
        self.repo.delete_requirement(requirement)
        self.audit.record(
            customer_id=customer_id,
            entity_type="fixture_requirement",
            entity_key=(
                f"{model.code if model else requirement.model_id}->"
                f"{station.code if station else requirement.station_id}->"
                f"{fixture.code if fixture else requirement.fixture_id}"
            ),
            action="delete",
            summary=(
                f"刪除治具需求 {model.code if model else requirement.model_id} / "
                f"{station.code if station else requirement.station_id} / "
                f"{fixture.code if fixture else requirement.fixture_id}"
            ),
            actor=actor,
        )
        self.db.commit()

    def get_affected_station_ids_by_fixture(self, fixture_id: int, customer_id: int | None = None) -> list[int]:
        return self.repo.list_affected_station_ids_by_fixture(fixture_id, customer_id=customer_id)

    def get_affected_station_model_pairs_by_fixture(
        self,
        fixture_id: int,
        customer_id: int | None = None,
    ) -> list[tuple[int, int]]:
        return self.repo.list_affected_station_model_pairs_by_fixture(fixture_id, customer_id=customer_id)

    def recalculate_station_capacity(
        self,
        station_id: int,
        *,
        model_id: int,
        customer_id: int | None = None,
    ) -> tuple[int, str | None]:
        requirements = self.repo.list_station_requirements(station_id, model_id=model_id, customer_id=customer_id)
        if not requirements:
            return 0, None

        min_capacity: int | None = None
        bottleneck_code: str | None = None

        for req in requirements:
            if req.required_qty <= 0:
                continue
            stock_qty = self.repo.get_stock_qty(req.fixture_id)
            capacity = floor(stock_qty / req.required_qty)
            fixture = self.repo.get_fixture(req.fixture_id, customer_id=customer_id)
            fixture_code = "unknown" if fixture is None else fixture.code

            if min_capacity is None or capacity < min_capacity:
                min_capacity = capacity
                bottleneck_code = fixture_code

        max_count = 0 if min_capacity is None else min_capacity
        return max_count, bottleneck_code

    def get_station_capacity(self, station_id: int, model_id: int, customer_id: int | None = None) -> dict:
        model = self.repo.get_model(model_id, customer_id=customer_id)
        if model is None:
            raise ValueError(f"model {model_id} not found")
        station = self.repo.get_station(station_id, customer_id=customer_id)
        if station is None:
            raise ValueError(f"station {station_id} not found")
        if self.repo.get_model_station(model_id, station_id, customer_id=customer_id) is None:
            raise ValueError("station is not mapped to the selected model")

        max_count, bottleneck = self.recalculate_station_capacity(
            station_id,
            model_id=model_id,
            customer_id=customer_id,
        )
        self.db.commit()
        return {
            "model_id": model.id,
            "model_code": model.code,
            "station_id": station.id,
            "station_code": station.code,
            "station_name": station.name,
            "max_open_station_count": max_count,
            "bottleneck_fixture_code": bottleneck,
        }

    def get_model_query(self, model_id: int, station_id: int | None = None, customer_id: int | None = None) -> dict:
        model = self.repo.get_model(model_id, customer_id=customer_id)
        if model is None:
            raise ValueError(f"model {model_id} not found")

        station_ids = self.repo.list_station_ids_by_model(model_id, customer_id=customer_id)
        if station_id is not None:
            if station_id not in station_ids:
                raise ValueError("station is not mapped to the selected model")
            station_ids = [station_id]

        station_id_set = set(station_ids)
        station_rows_raw = [
            row
            for row in self.repo.list_stations_by_model(model_id, customer_id=customer_id)
            if row["station_id"] in station_id_set
        ]
        station_requirements: dict[int, list] = {}
        for station_id in station_ids:
            station_requirements[station_id] = self.repo.list_station_requirements(
                station_id,
                model_id=model_id,
                customer_id=customer_id,
            )

        fixture_rows: dict[int, dict] = {}
        station_requirement_rows: list[dict] = []
        station_query_rows: list[dict] = []
        station_capacity_values: list[int] = []
        for station_row in station_rows_raw:
            requirements = station_requirements.get(station_row["station_id"], [])
            min_capacity: int | None = None
            bottleneck_code: str | None = None
            for req in requirements:
                if req.required_qty <= 0:
                    continue
                fixture = self.repo.get_fixture(req.fixture_id, customer_id=customer_id)
                if fixture is None:
                    continue
                stock_qty = self.repo.get_stock_qty(req.fixture_id)
                level = self.repo.get_stock_level(req.fixture_id)
                min_stock_qty = 0 if level is None else level.min_stock_qty
                if stock_qty <= 0:
                    stock_status = "out_of_stock"
                elif stock_qty < min_stock_qty:
                    stock_status = "low_stock"
                else:
                    stock_status = "normal"
                capacity = floor(stock_qty / req.required_qty)
                station_requirement_rows.append(
                    {
                        "model_id": model.id,
                        "model_code": model.code,
                        "station_id": station_row["station_id"],
                        "station_code": station_row["station_code"],
                        "fixture_id": fixture.id,
                        "fixture_code": fixture.code,
                        "fixture_name": fixture.name,
                        "required_qty": req.required_qty,
                        "stock_qty": stock_qty,
                        "max_open_station_count": capacity,
                        "stock_status": stock_status,
                    }
                )
                if req.fixture_id not in fixture_rows:
                    fixture_rows[req.fixture_id] = {
                        "fixture_id": fixture.id,
                        "fixture_code": fixture.code,
                        "fixture_name": fixture.name,
                        "stock_qty": stock_qty,
                        "min_stock_qty": min_stock_qty,
                        "required_per_station": req.required_qty,
                        "stock_status": stock_status,
                    }
                else:
                    fixture_rows[req.fixture_id]["required_per_station"] = max(
                        fixture_rows[req.fixture_id]["required_per_station"], req.required_qty
                    )

                if min_capacity is None or capacity < min_capacity:
                    min_capacity = capacity
                    bottleneck_code = fixture.code

            station_capacity = 0 if min_capacity is None else min_capacity
            station_query_rows.append(
                {
                    "station_id": station_row["station_id"],
                    "station_code": station_row["station_code"],
                    "station_name": station_row["station_name"],
                    "max_open_station_count": station_capacity,
                    "bottleneck_fixture_code": bottleneck_code,
                }
            )
            station_capacity_values.append(station_capacity)

        fixtures: list[dict] = []
        total_stock = 0
        for row in fixture_rows.values():
            required = row["required_per_station"]
            max_open = 0 if required <= 0 else floor(row["stock_qty"] / required)
            row["max_open_station_count"] = max_open
            fixtures.append(row)
            total_stock += row["stock_qty"]

        fixtures.sort(key=lambda item: item["fixture_code"])
        station_query_rows.sort(key=lambda item: item["station_code"])
        model_max_open = 0 if not station_capacity_values else station_capacity_values[0]

        return {
            "model_id": model.id,
            "model_code": model.code,
            "model_name": model.name,
            "max_open_station_count": model_max_open,
            "station_count": len(set(station_ids)),
            "fixture_type_count": len(fixtures),
            "total_stock_qty": total_stock,
            "stations": station_query_rows,
            "station_requirements": station_requirement_rows,
            "fixtures": fixtures,
        }

    def export_model_stations_csv(self, customer_id: int | None = None) -> str:
        mappings = self.repo.list_model_stations(customer_id=customer_id)
        rows = []
        for row in mappings:
            model = self.repo.get_model(row.model_id, customer_id=customer_id)
            station = self.repo.get_station(row.station_id, customer_id=customer_id)
            rows.append(
                {
                    "model_code": model.code if model else "",
                    "station_code": station.code if station else "",
                }
            )
        return render_csv_text(["model_code", "station_code"], rows)

    def model_station_template_csv(self) -> str:
        return render_csv_text(["model_code", "station_code"], [{"model_code": "VPort-254", "station_code": "ST-01"}])

    def import_model_stations_csv(self, customer_id: int | None, payload: CsvImportPayload, actor: SessionContext | None = None) -> int:
        if customer_id is None:
            raise ValueError("customer_id is required")
        rows = parse_csv_bytes(payload.content.encode("utf-8"))
        imported_count = 0
        for row in rows:
            model_code = row.get("model_code", "")
            station_code = row.get("station_code", "")
            if not model_code or not station_code:
                continue
            model = self.repo.get_model_by_code(model_code, customer_id=customer_id)
            station = self.repo.get_station_by_code(station_code, customer_id=customer_id)
            if model is None or station is None:
                raise ValueError(f"mapping not found: {model_code} / {station_code}")
            if self.repo.get_model_station(model.id, station.id, customer_id=customer_id) is None:
                self.repo.create_model_station(model_id=model.id, station_id=station.id)
                imported_count += 1
        self.audit.record(
            customer_id=customer_id,
            entity_type="model_station",
            entity_key="import",
            action="import",
            summary=f"匯入機種站點對應，共 {imported_count} 筆",
            actor=actor,
        )
        self.db.commit()
        return imported_count

    def export_fixture_requirements_csv(self, customer_id: int | None = None) -> str:
        requirements = self.repo.list_all_requirements(customer_id=customer_id)
        rows = []
        for row in requirements:
            model = self.repo.get_model(row.model_id, customer_id=customer_id)
            station = self.repo.get_station(row.station_id, customer_id=customer_id)
            fixture = self.repo.get_fixture(row.fixture_id, customer_id=customer_id)
            rows.append(
                {
                    "model_code": model.code if model else "",
                    "station_code": station.code if station else "",
                    "fixture_code": fixture.code if fixture else "",
                    "required_qty": row.required_qty,
                }
            )
        return render_csv_text(["model_code", "station_code", "fixture_code", "required_qty"], rows)

    def list_fixture_requirements(self, customer_id: int | None = None) -> list[dict]:
        return self.repo.list_requirement_rows(customer_id=customer_id)

    def list_station_requirements(self, station_id: int, model_id: int, customer_id: int | None = None) -> list[dict]:
        rows = self.repo.list_requirement_rows(customer_id=customer_id)
        return [row for row in rows if row["station_id"] == station_id and row["model_id"] == model_id]

    def fixture_requirement_template_csv(self) -> str:
        return render_csv_text(
            ["model_code", "station_code", "fixture_code", "required_qty"],
            [{"model_code": "VPort-254", "station_code": "ST-01", "fixture_code": "C-00001", "required_qty": "2"}],
        )

    def import_fixture_requirements_csv(self, customer_id: int | None, payload: CsvImportPayload, actor: SessionContext | None = None) -> int:
        if customer_id is None:
            raise ValueError("customer_id is required")
        rows = parse_csv_bytes(payload.content.encode("utf-8"))
        imported_count = 0
        for row in rows:
            model_code = row.get("model_code", "")
            station_code = row.get("station_code", "")
            fixture_code = row.get("fixture_code", "")
            required_qty = int(row.get("required_qty", "0") or "0")
            if not model_code or not station_code or not fixture_code or required_qty <= 0:
                continue
            model = self.repo.get_model_by_code(model_code, customer_id=customer_id)
            station = self.repo.get_station_by_code(station_code, customer_id=customer_id)
            fixture = self.repo.get_fixture_by_code(fixture_code, customer_id=customer_id)
            if model is None or station is None or fixture is None:
                raise ValueError(f"requirement not found: {model_code} / {station_code} / {fixture_code}")
            if self.repo.get_model_station(model.id, station.id, customer_id=customer_id) is None:
                raise ValueError(f"mapping not found: {model_code} / {station_code}")
            self.repo.create_or_update_requirement(
                model_id=model.id,
                station_id=station.id,
                fixture_id=fixture.id,
                required_qty=required_qty,
            )
            imported_count += 1
        self.audit.record(
            customer_id=customer_id,
            entity_type="fixture_requirement",
            entity_key="import",
            action="import",
            summary=f"匯入治具需求，共 {imported_count} 筆",
            actor=actor,
        )
        self.db.commit()
        return imported_count
