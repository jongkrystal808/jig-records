from math import floor
from sqlalchemy.exc import IntegrityError

from sqlalchemy.orm import Session

from backend.app.core.auth import SessionContext
from backend.app.repositories.inventory_repository import InventoryRepository
from backend.app.repositories.production_repository import ProductionRepository
from backend.app.schemas.common import CsvImportPayload
from backend.app.schemas.production import (
    FixtureRequirementCopy,
    FixtureRequirementCreate,
    ModelStationCreate,
    ProductionCsvImportPayload,
)
from backend.app.services.audit_service import AuditService
from backend.app.utils.csv_tools import parse_csv_bytes, render_csv_text, stream_csv_text
from backend.app.utils.identifier_rules import normalize_identifier_for_write


class ProductionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProductionRepository(db)
        self.audit = AuditService(db)

    def _validate_designated_identifiers(self, payload: FixtureRequirementCreate) -> list[str]:
        if not payload.designated_mode:
            return []
        identifiers = list(
            dict.fromkeys(
                normalize_identifier_for_write(identifier)
                for identifier in payload.designated_identifiers
            )
        )
        if not identifiers:
            raise ValueError("指定模式至少需要選擇一個有庫存的 identifier")
        available_rows = InventoryRepository(self.db).list_identifier_stock_summary_rows(
            customer_id=payload.customer_id,
            fixture_id=payload.fixture_id,
        )
        available = {str(row["identifier"]) for row in available_rows if int(row["stock_qty"]) > 0}
        missing = [identifier for identifier in identifiers if identifier not in available]
        if missing:
            raise ValueError(f"指定的 identifier 無可用庫存：{', '.join(missing)}")
        return identifiers

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

    def list_model_stations_page(self, **kwargs) -> dict:
        items, total = self.repo.list_model_stations_page(**kwargs)
        return {"items": items, "page": kwargs["page"], "page_size": kwargs["page_size"], "total": total}

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

    def _ensure_model_station(self, *, customer_id: int, model_id: int, station_id: int) -> None:
        if self.repo.get_model_station(model_id, station_id, customer_id=customer_id) is None:
            self.repo.create_model_station(model_id=model_id, station_id=station_id)

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

        designated_identifiers = self._validate_designated_identifiers(payload)

        self._ensure_model_station(
            customer_id=payload.customer_id,
            model_id=payload.model_id,
            station_id=payload.station_id,
        )

        requirement = self.repo.create_or_update_requirement(
            model_id=payload.model_id,
            station_id=payload.station_id,
            fixture_id=payload.fixture_id,
            required_qty=payload.required_qty,
            designated_mode=payload.designated_mode,
            designated_identifiers=designated_identifiers,
        )
        from backend.app.services.storage_service import StorageService

        StorageService(self.db).sync_fixture_storage_fields(
            fixture, fixture.line_storage_location, fixture.department_storage_location
        )
        self.audit.record(
            customer_id=payload.customer_id,
            entity_type="fixture_requirement",
            entity_key=f"{model.code}->{station.code}->{fixture.code}",
            action="create",
            summary=(
                f"建立治具需求 {model.code} / {station.code} / {fixture.code} = {payload.required_qty}"
                + (f"；指定 identifier：{', '.join(designated_identifiers)}" if payload.designated_mode else "")
            ),
            actor=actor,
        )
        self.db.commit()
        self.db.refresh(requirement)
        return requirement

    def copy_fixture_requirements(
        self,
        payload: FixtureRequirementCopy,
        actor: SessionContext | None = None,
    ) -> dict:
        source_model = self.repo.get_model(payload.source_model_id, customer_id=payload.customer_id)
        if source_model is None:
            raise ValueError(f"source model {payload.source_model_id} not found")
        source_station = self.repo.get_station(payload.source_station_id, customer_id=payload.customer_id)
        if source_station is None:
            raise ValueError(f"source station {payload.source_station_id} not found")
        if (
            self.repo.get_model_station(
                payload.source_model_id,
                payload.source_station_id,
                customer_id=payload.customer_id,
            )
            is None
        ):
            raise ValueError("source station is not mapped to the selected model")

        target_model = self.repo.get_model(payload.target_model_id, customer_id=payload.customer_id)
        if target_model is None:
            raise ValueError(f"target model {payload.target_model_id} not found")
        target_station = self.repo.get_station(payload.target_station_id, customer_id=payload.customer_id)
        if target_station is None:
            raise ValueError(f"target station {payload.target_station_id} not found")
        if (
            payload.source_model_id == payload.target_model_id
            and payload.source_station_id == payload.target_station_id
        ):
            raise ValueError("source and target station must be different")

        source_requirements = self.repo.list_station_requirements(
            payload.source_station_id,
            model_id=payload.source_model_id,
            customer_id=payload.customer_id,
        )
        if not source_requirements:
            raise ValueError("source station has no fixture requirements")

        mapping_created = (
            self.repo.get_model_station(
                payload.target_model_id,
                payload.target_station_id,
                customer_id=payload.customer_id,
            )
            is None
        )
        if mapping_created:
            self.repo.create_model_station(
                model_id=payload.target_model_id,
                station_id=payload.target_station_id,
            )

        created_count = 0
        updated_count = 0
        skipped_count = 0
        for source_requirement in source_requirements:
            target_requirement = self.repo.get_requirement(
                model_id=payload.target_model_id,
                station_id=payload.target_station_id,
                fixture_id=source_requirement.fixture_id,
            )
            if target_requirement is None:
                self.repo.create_or_update_requirement(
                    model_id=payload.target_model_id,
                    station_id=payload.target_station_id,
                    fixture_id=source_requirement.fixture_id,
                    required_qty=source_requirement.required_qty,
                    designated_mode=source_requirement.designated_mode,
                    designated_identifiers=source_requirement.designated_identifiers,
                )
                created_count += 1
                continue

            target_matches_source = (
                target_requirement.required_qty == source_requirement.required_qty
                and target_requirement.designated_mode == source_requirement.designated_mode
                and target_requirement.designated_identifiers == source_requirement.designated_identifiers
            )
            if not payload.overwrite_existing or target_matches_source:
                skipped_count += 1
                continue

            self.repo.update_requirement(
                target_requirement,
                model_id=payload.target_model_id,
                station_id=payload.target_station_id,
                fixture_id=source_requirement.fixture_id,
                required_qty=source_requirement.required_qty,
                designated_mode=source_requirement.designated_mode,
                designated_identifiers=source_requirement.designated_identifiers,
            )
            updated_count += 1

        self.audit.record(
            customer_id=payload.customer_id,
            entity_type="fixture_requirement",
            entity_key=(
                f"{source_model.code}->{source_station.code}"
                f"=>{target_model.code}->{target_station.code}"
            ),
            action="copy",
            summary=(
                f"複製治具需求 {source_model.code} / {source_station.code} → "
                f"{target_model.code} / {target_station.code}；"
                f"新增 {created_count}、更新 {updated_count}、跳過 {skipped_count}"
            ),
            actor=actor,
        )
        self.db.commit()
        return {
            "source_requirement_count": len(source_requirements),
            "created_count": created_count,
            "updated_count": updated_count,
            "skipped_count": skipped_count,
            "mapping_created": mapping_created,
        }

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

        designation_supplied = bool(
            {"designated_mode", "designated_identifiers"} & payload.model_fields_set
        )
        designated_identifiers = self._validate_designated_identifiers(payload) if designation_supplied else []

        self._ensure_model_station(
            customer_id=payload.customer_id,
            model_id=payload.model_id,
            station_id=payload.station_id,
        )

        existing = self.repo.get_requirement(
            model_id=payload.model_id,
            station_id=payload.station_id,
            fixture_id=payload.fixture_id,
        )
        if existing is not None and existing.id != requirement_id:
            raise ValueError("fixture requirement already exists")

        previous_fixture_id = requirement.fixture_id
        try:
            updated = self.repo.update_requirement(
                requirement,
                model_id=payload.model_id,
                station_id=payload.station_id,
                fixture_id=payload.fixture_id,
                required_qty=payload.required_qty,
                designated_mode=payload.designated_mode if designation_supplied else None,
                designated_identifiers=designated_identifiers if designation_supplied else None,
            )
            from backend.app.services.storage_service import StorageService

            storage_service = StorageService(self.db)
            if previous_fixture_id != fixture.id:
                previous_fixture = self.repo.get_fixture(previous_fixture_id, customer_id=payload.customer_id)
                if previous_fixture is not None:
                    storage_service.sync_fixture_storage_fields(
                        previous_fixture,
                        previous_fixture.line_storage_location,
                        previous_fixture.department_storage_location,
                    )
            storage_service.sync_fixture_storage_fields(
                fixture, fixture.line_storage_location, fixture.department_storage_location
            )
            self.audit.record(
                customer_id=payload.customer_id,
                entity_type="fixture_requirement",
                entity_key=f"{model.code}->{station.code}->{fixture.code}",
                action="update",
                summary=(
                    f"更新治具需求 {model.code} / {station.code} / {fixture.code} = {payload.required_qty}"
                    + (f"；指定 identifier：{', '.join(designated_identifiers)}" if designation_supplied and payload.designated_mode else "")
                ),
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
        if fixture is not None:
            from backend.app.services.storage_service import StorageService

            StorageService(self.db).sync_fixture_storage_fields(
                fixture, fixture.line_storage_location, fixture.department_storage_location
            )
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
            stock_qty = self.repo.get_requirement_stock_qty(req)
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
                stock_qty = self.repo.get_requirement_stock_qty(req)
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
                        "designated_mode": req.designated_mode,
                        "designated_identifiers": req.designated_identifiers,
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
        model_max_open = min(station_capacity_values, default=0)

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

    def stream_form_export_csv(
        self,
        *,
        entity: str,
        customer_id: int,
        model_id: int | None = None,
        station_id: int | None = None,
        keyword: str = "",
    ):
        if entity == "mappings":
            source = self.repo.iter_model_station_rows(
                customer_id=customer_id,
                model_id=model_id,
                station_id=station_id,
                keyword=keyword,
            )
            rows = (
                {
                    "機種編號": row["model_code"],
                    "機種名稱": row["model_name"],
                    "站點編號": row["station_code"],
                    "站點名稱": row["station_name"],
                    "狀態": "已配置",
                }
                for row in source
            )
            return stream_csv_text(["機種編號", "機種名稱", "站點編號", "站點名稱", "狀態"], rows)
        if entity != "requirements":
            raise ValueError(f"unsupported form export entity: {entity}")
        source = self.repo.iter_requirement_export_rows(
            customer_id=customer_id,
            model_id=model_id,
            station_id=station_id,
            keyword=keyword,
        )
        rows = (
            {
                "機種": row["model_code"],
                "站點": row["station_code"],
                "治具": row["fixture_code"],
                "治具名稱": row["fixture_name"],
                "每站需求": row["required_qty"],
                "使用模式": "指定 identifier" if row["designated_mode"] else "不限 identifier",
                "指定 identifier": str(row["designated_identifiers"] or "").replace(",", "、"),
                "目前庫存": row["stock_qty"],
                "可開站": int(row["stock_qty"] or 0) // int(row["required_qty"]),
            }
            for row in source
        )
        return stream_csv_text(
            ["機種", "站點", "治具", "治具名稱", "每站需求", "使用模式", "指定 identifier", "目前庫存", "可開站"],
            rows,
        )

    def model_station_template_csv(self) -> str:
        return render_csv_text(["model_code", "station_code"], [{"model_code": "VPort-254", "station_code": "ST-01"}])

    @staticmethod
    def _summarize_import_preview(rows: list[dict]) -> dict:
        return {
            "rows": rows,
            "new_count": sum(row["status"] == "new" for row in rows),
            "unchanged_count": sum(row["status"] == "unchanged" for row in rows),
            "conflict_count": sum(row["status"] == "conflict" for row in rows),
            "error_count": sum(row["status"] == "error" for row in rows),
        }

    def preview_model_stations_csv(self, customer_id: int | None, payload: CsvImportPayload) -> dict:
        if customer_id is None:
            raise ValueError("customer_id is required")
        rows = parse_csv_bytes(payload.content.encode("utf-8"))
        preview_rows: list[dict] = []
        seen: set[tuple[str, str]] = set()
        for index, row in enumerate(rows, start=2):
            model_code = row.get("model_code", "").strip()
            station_code = row.get("station_code", "").strip()
            preview = {
                "line": index,
                "model_code": model_code,
                "station_code": station_code,
                "status": "error",
                "message": "",
            }
            if not model_code or not station_code:
                preview["message"] = "機種編號與站點編號不可空白"
                preview_rows.append(preview)
                continue
            key = (model_code.casefold(), station_code.casefold())
            if key in seen:
                preview["message"] = "同一份貼上資料中已有重複的機種站點綁定"
                preview_rows.append(preview)
                continue
            seen.add(key)
            model = self.repo.get_model_by_code(model_code, customer_id=customer_id)
            station = self.repo.get_station_by_code(station_code, customer_id=customer_id)
            if model is None or station is None:
                preview["message"] = f"找不到機種或站點：{model_code} / {station_code}"
            elif self.repo.get_model_station(model.id, station.id, customer_id=customer_id) is None:
                preview.update(status="new", message="將新增機種站點綁定")
            else:
                preview.update(status="unchanged", message="已存在相同綁定，將略過")
            preview_rows.append(preview)
        return self._summarize_import_preview(preview_rows)

    def import_model_stations_csv(
        self,
        customer_id: int | None,
        payload: ProductionCsvImportPayload,
        actor: SessionContext | None = None,
    ) -> dict:
        preview = self.preview_model_stations_csv(customer_id, payload)
        if preview["error_count"]:
            first_error = next(row for row in preview["rows"] if row["status"] == "error")
            raise ValueError(f"第 {first_error['line']} 行：{first_error['message']}")
        created_count = 0
        for row in preview["rows"]:
            if row["status"] != "new":
                continue
            model = self.repo.get_model_by_code(row["model_code"], customer_id=customer_id)
            station = self.repo.get_station_by_code(row["station_code"], customer_id=customer_id)
            if model is None or station is None:
                raise ValueError(f"mapping not found: {row['model_code']} / {row['station_code']}")
            self.repo.create_model_station(model_id=model.id, station_id=station.id)
            created_count += 1
        skipped_count = preview["unchanged_count"]
        self.audit.record(
            customer_id=customer_id,
            entity_type="model_station",
            entity_key="import",
            action="import",
            summary=f"匯入機種站點對應，新增 {created_count} 筆、略過 {skipped_count} 筆",
            actor=actor,
        )
        self.db.commit()
        return {
            "imported_count": created_count,
            "created_count": created_count,
            "updated_count": 0,
            "skipped_count": skipped_count,
        }

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
                    "designated_mode": "yes" if row.designated_mode else "no",
                    "designated_identifiers": ",".join(row.designated_identifiers),
                }
            )
        return render_csv_text(
            ["model_code", "station_code", "fixture_code", "required_qty", "designated_mode", "designated_identifiers"],
            rows,
        )

    def list_fixture_requirements(self, customer_id: int | None = None) -> list[dict]:
        return self.repo.list_requirement_rows(customer_id=customer_id)

    def list_fixture_requirements_page(self, **kwargs) -> dict:
        items, total = self.repo.list_requirement_rows_page(**kwargs)
        return {"items": items, "page": kwargs["page"], "page_size": kwargs["page_size"], "total": total}

    def list_station_requirements(self, station_id: int, model_id: int, customer_id: int | None = None) -> list[dict]:
        rows = self.repo.list_requirement_rows(customer_id=customer_id)
        return [row for row in rows if row["station_id"] == station_id and row["model_id"] == model_id]

    def fixture_requirement_template_csv(self) -> str:
        return render_csv_text(
            ["model_code", "station_code", "fixture_code", "required_qty"],
            [{"model_code": "VPort-254", "station_code": "ST-01", "fixture_code": "C-00001", "required_qty": "2"}],
        )

    def preview_fixture_requirements_csv(self, customer_id: int | None, payload: CsvImportPayload) -> dict:
        if customer_id is None:
            raise ValueError("customer_id is required")
        rows = parse_csv_bytes(payload.content.encode("utf-8"))
        preview_rows: list[dict] = []
        seen: set[tuple[str, str, str]] = set()
        for index, row in enumerate(rows, start=2):
            model_code = row.get("model_code", "").strip()
            station_code = row.get("station_code", "").strip()
            fixture_code = row.get("fixture_code", "").strip()
            required_qty_text = row.get("required_qty", "").strip()
            required_qty = int(required_qty_text) if required_qty_text.isdigit() else 0
            preview = {
                "line": index,
                "model_code": model_code,
                "station_code": station_code,
                "fixture_code": fixture_code,
                "incoming_required_qty": required_qty if required_qty > 0 else None,
                "existing_required_qty": None,
                "status": "error",
                "message": "",
            }
            if not model_code or not station_code or not fixture_code or required_qty <= 0:
                preview["message"] = "機種、站點、治具不可空白，且每站需求量須為大於 0 的整數"
                preview_rows.append(preview)
                continue
            key = (model_code.casefold(), station_code.casefold(), fixture_code.casefold())
            if key in seen:
                preview["message"] = "同一份貼上資料中已有重複的機種站點治具綁定"
                preview_rows.append(preview)
                continue
            seen.add(key)
            model = self.repo.get_model_by_code(model_code, customer_id=customer_id)
            station = self.repo.get_station_by_code(station_code, customer_id=customer_id)
            fixture = self.repo.get_fixture_by_code(fixture_code, customer_id=customer_id)
            if model is None or station is None or fixture is None:
                preview["message"] = f"找不到機種、站點或治具：{model_code} / {station_code} / {fixture_code}"
                preview_rows.append(preview)
                continue
            if self.repo.get_model_station(model.id, station.id, customer_id=customer_id) is None:
                preview["message"] = f"機種 {model_code} 尚未綁定站點 {station_code}"
                preview_rows.append(preview)
                continue
            existing = self.repo.get_requirement(
                model_id=model.id,
                station_id=station.id,
                fixture_id=fixture.id,
            )
            if existing is None:
                preview.update(status="new", message="將新增治具需求綁定")
            elif existing.required_qty == required_qty:
                preview.update(
                    existing_required_qty=existing.required_qty,
                    status="unchanged",
                    message="與現有資料相同，將略過",
                )
            else:
                preview.update(
                    existing_required_qty=existing.required_qty,
                    status="conflict",
                    message=f"每站需求量將由 {existing.required_qty} 取代為 {required_qty}",
                )
            preview_rows.append(preview)
        return self._summarize_import_preview(preview_rows)

    def import_fixture_requirements_csv(
        self,
        customer_id: int | None,
        payload: ProductionCsvImportPayload,
        actor: SessionContext | None = None,
    ) -> dict:
        preview = self.preview_fixture_requirements_csv(customer_id, payload)
        if preview["error_count"]:
            first_error = next(row for row in preview["rows"] if row["status"] == "error")
            raise ValueError(f"第 {first_error['line']} 行：{first_error['message']}")
        created_count = 0
        updated_count = 0
        skipped_count = 0
        for row in preview["rows"]:
            if row["status"] == "unchanged" or (row["status"] == "conflict" and not payload.overwrite_existing):
                skipped_count += 1
                continue
            model = self.repo.get_model_by_code(row["model_code"], customer_id=customer_id)
            station = self.repo.get_station_by_code(row["station_code"], customer_id=customer_id)
            fixture = self.repo.get_fixture_by_code(row["fixture_code"], customer_id=customer_id)
            if model is None or station is None or fixture is None:
                raise ValueError(f"requirement not found: {row['model_code']} / {row['station_code']} / {row['fixture_code']}")
            self.repo.create_or_update_requirement(
                model_id=model.id,
                station_id=station.id,
                fixture_id=fixture.id,
                required_qty=row["incoming_required_qty"],
            )
            if row["status"] == "conflict":
                updated_count += 1
            else:
                created_count += 1
        imported_count = created_count + updated_count
        self.audit.record(
            customer_id=customer_id,
            entity_type="fixture_requirement",
            entity_key="import",
            action="import",
            summary=f"匯入治具需求，新增 {created_count} 筆、取代 {updated_count} 筆、略過 {skipped_count} 筆",
            actor=actor,
        )
        self.db.commit()
        return {
            "imported_count": imported_count,
            "created_count": created_count,
            "updated_count": updated_count,
            "skipped_count": skipped_count,
        }
