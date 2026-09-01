from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.auth import SessionContext
from backend.app.models.storage import FixturePlacement, StorageCode, StorageContainer
from backend.app.repositories.storage_repository import StorageRepository
from backend.app.schemas.storage import (
    FixturePlacementInput,
    FixturePlacementUpdate,
    StorageCodeOrganize,
    StorageCodeRegister,
    StorageContainerCreate,
    StorageContainerUpdate,
)
from backend.app.services.audit_service import AuditService


class StorageService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = StorageRepository(db)
        self.audit = AuditService(db)

    @staticmethod
    def parse_location_codes(*values: str | None) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            for raw_token in (value or "").replace("，", ",").split(","):
                token = raw_token.strip().upper()
                if not token or token in seen:
                    continue
                seen.add(token)
                result.append(token)
        return result

    @staticmethod
    def _clean_text(value: str | None) -> str | None:
        normalized = (value or "").strip()
        return normalized or None

    @staticmethod
    def _placement_key(row: FixturePlacement) -> tuple:
        if row.target_type == "storage_code":
            return ("storage_code", row.storage_code_id)
        return ("model_station", row.model_id, row.station_id)

    def create_container(
        self, payload: StorageContainerCreate, actor: SessionContext | None = None
    ) -> dict:
        try:
            row = self.repo.create_container(
                customer_id=payload.customer_id,
                name=payload.name.strip(),
                description=self._clean_text(payload.description),
            )
            self.audit.record(
                customer_id=payload.customer_id,
                entity_type="storage_container",
                entity_key=row.name,
                action="create",
                summary=f"建立收納處 {row.name}",
                actor=actor,
            )
            self.db.commit()
            self.db.refresh(row)
            return self._serialize_container(row)
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("同一客戶下已存在相同名稱的收納處") from exc

    def update_container(
        self,
        container_id: int,
        customer_id: int,
        payload: StorageContainerUpdate,
        actor: SessionContext | None = None,
    ) -> dict:
        row = self.repo.get_container(container_id, customer_id)
        if row is None:
            raise ValueError(f"storage container {container_id} not found")
        before_name = row.name
        try:
            row.name = payload.name.strip()
            row.description = self._clean_text(payload.description)
            self.db.flush()
            self.audit.record(
                customer_id=customer_id,
                entity_type="storage_container",
                entity_key=row.name,
                action="update",
                summary=f"更新收納處 {before_name} -> {row.name}",
                actor=actor,
            )
            self.db.commit()
            self.db.refresh(row)
            return self._serialize_container(row)
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("同一客戶下已存在相同名稱的收納處") from exc

    def delete_container(
        self, container_id: int, customer_id: int, actor: SessionContext | None = None
    ) -> None:
        row = self.repo.get_container(container_id, customer_id)
        if row is None:
            raise ValueError(f"storage container {container_id} not found")
        name = row.name
        self.repo.delete_container(row)
        self.audit.record(
            customer_id=customer_id,
            entity_type="storage_container",
            entity_key=name,
            action="delete",
            summary=f"刪除收納處 {name}；位置編號已移回未整理",
            actor=actor,
        )
        self.db.commit()

    def organize_codes(
        self, payload: StorageCodeOrganize, actor: SessionContext | None = None
    ) -> dict:
        container = None
        if payload.container_id is not None:
            container = self.repo.get_container(payload.container_id, payload.customer_id)
            if container is None:
                raise ValueError(f"storage container {payload.container_id} not found")
        code_ids = sorted(set(payload.storage_code_ids))
        codes: list[StorageCode] = []
        for code_id in code_ids:
            row = self.repo.get_code(code_id, payload.customer_id)
            if row is None:
                raise ValueError(f"storage code {code_id} not found")
            codes.append(row)
        for row in codes:
            row.container_id = None if container is None else container.id
        self.db.flush()
        target = "未整理" if container is None else container.name
        self.audit.record(
            customer_id=payload.customer_id,
            entity_type="storage_code",
            entity_key=", ".join(row.code for row in codes),
            action="organize",
            summary=f"整理 {len(codes)} 個位置編號至 {target}",
            actor=actor,
        )
        self.db.commit()
        return self.get_overview(payload.customer_id)

    def register_codes(
        self, payload: StorageCodeRegister, actor: SessionContext | None = None
    ) -> dict:
        tokens = self.parse_location_codes(payload.location_text)
        if not tokens:
            raise ValueError("請輸入至少一個位置編號")
        for token in tokens:
            self.repo.get_or_create_code(payload.customer_id, token)
        self.audit.record(
            customer_id=payload.customer_id,
            entity_type="storage_code",
            entity_key=", ".join(tokens),
            action="register",
            summary=f"登記位置編號，共 {len(tokens)} 個",
            actor=actor,
        )
        self.db.commit()
        return self.get_overview(payload.customer_id)

    def get_fixture_customer_id(self, fixture_id: int) -> int:
        fixture = self.repo.get_fixture(fixture_id)
        if fixture is None:
            raise ValueError(f"fixture {fixture_id} not found")
        return fixture.customer_id

    def sync_fixture_storage_fields(
        self,
        fixture,
        line_storage_location: str | None,
        department_storage_location: str | None,
    ) -> None:
        tokens = self.parse_location_codes(line_storage_location, department_storage_location)
        station_options = self.repo.list_station_options(fixture.id, fixture.customer_id)
        station_by_code: dict[str, list[dict]] = {}
        for option in station_options:
            station_by_code.setdefault(option["station_code"].strip().upper(), []).append(option)

        existing = self.repo.list_placements(fixture.id)
        valid_station_keys = {
            ("model_station", option["model_id"], option["station_id"])
            for option in station_options
        }
        for row in list(existing):
            if row.target_type == "model_station" and self._placement_key(row) not in valid_station_keys:
                self.repo.delete_placement(row)
                existing.remove(row)
        existing_by_key = {self._placement_key(row): row for row in existing}
        desired_keys: set[tuple] = set()
        for token in tokens:
            candidates = station_by_code.get(token, [])
            if len(candidates) == 1:
                option = candidates[0]
                key = ("model_station", option["model_id"], option["station_id"])
                values = {
                    "fixture_id": fixture.id,
                    "target_type": "model_station",
                    "storage_code_id": None,
                    "model_id": option["model_id"],
                    "station_id": option["station_id"],
                    "quantity": None,
                    "source": "fixture_field",
                }
            else:
                code = self.repo.get_or_create_code(fixture.customer_id, token)
                key = ("storage_code", code.id)
                values = {
                    "fixture_id": fixture.id,
                    "target_type": "storage_code",
                    "storage_code_id": code.id,
                    "model_id": None,
                    "station_id": None,
                    "quantity": None,
                    "source": "fixture_field",
                }
            desired_keys.add(key)
            if key not in existing_by_key:
                self.repo.create_placement(**values)

        for row in existing:
            if row.source == "fixture_field" and self._placement_key(row) not in desired_keys:
                self.repo.delete_placement(row)

    def resync_fixture(
        self, fixture_id: int, actor: SessionContext | None = None
    ) -> dict:
        fixture = self.repo.get_fixture(fixture_id)
        if fixture is None:
            raise ValueError(f"fixture {fixture_id} not found")
        self.sync_fixture_storage_fields(
            fixture,
            fixture.line_storage_location,
            fixture.department_storage_location,
        )
        self.audit.record(
            customer_id=fixture.customer_id,
            entity_type="fixture_placement",
            entity_key=fixture.code,
            action="sync",
            summary=f"依治具儲位欄位重新解析位置 {fixture.code}",
            actor=actor,
        )
        self.db.commit()
        return self.get_fixture_placements(fixture_id)

    def replace_fixture_placements(
        self,
        fixture_id: int,
        payload: FixturePlacementUpdate,
        actor: SessionContext | None = None,
    ) -> dict:
        fixture = self.repo.get_fixture(fixture_id)
        if fixture is None:
            raise ValueError(f"fixture {fixture_id} not found")
        stock_qty = self.repo.get_stock_qty(fixture_id)
        allocated_qty = sum(row.quantity or 0 for row in payload.placements)
        if allocated_qty > stock_qty:
            raise ValueError(f"位置分配數量 {allocated_qty} 不可超過目前庫存 {stock_qty}")

        keys: set[tuple] = set()
        validated: list[FixturePlacementInput] = []
        for item in payload.placements:
            if item.target_type == "storage_code":
                code = self.repo.get_code(int(item.storage_code_id), fixture.customer_id)
                if code is None:
                    raise ValueError(f"storage code {item.storage_code_id} not found")
                key = ("storage_code", code.id)
            else:
                model = self.repo.get_model(int(item.model_id))
                station = self.repo.get_station(int(item.station_id))
                if (
                    model is None
                    or station is None
                    or model.customer_id != fixture.customer_id
                    or station.customer_id != fixture.customer_id
                    or not self.repo.has_requirement(fixture.id, model.id, station.id)
                ):
                    raise ValueError("選擇的機種站點未綁定此治具")
                key = ("model_station", model.id, station.id)
            if key in keys:
                raise ValueError("同一位置不可重複分配")
            keys.add(key)
            validated.append(item)

        self.repo.clear_placements(fixture_id)
        for item in validated:
            self.repo.create_placement(
                fixture_id=fixture_id,
                target_type=item.target_type,
                storage_code_id=item.storage_code_id,
                model_id=item.model_id,
                station_id=item.station_id,
                quantity=item.quantity,
                source="manual",
            )
        self.audit.record(
            customer_id=fixture.customer_id,
            entity_type="fixture_placement",
            entity_key=fixture.code,
            action="update",
            summary=f"更新治具位置 {fixture.code}；{len(validated)} 個位置，已分配 {allocated_qty}/{stock_qty}",
            actor=actor,
        )
        self.db.commit()
        return self.get_fixture_placements(fixture_id)

    def get_fixture_placements(self, fixture_id: int) -> dict:
        fixture = self.repo.get_fixture(fixture_id)
        if fixture is None:
            raise ValueError(f"fixture {fixture_id} not found")
        stock_qty = self.repo.get_stock_qty(fixture_id)
        rows = [self._serialize_placement(row) for row in self.repo.list_placements(fixture_id)]
        allocated_qty = sum(row["quantity"] or 0 for row in rows)
        return {
            "fixture_id": fixture.id,
            "fixture_code": fixture.code,
            "fixture_name": fixture.name,
            "customer_id": fixture.customer_id,
            "stock_qty": stock_qty,
            "allocated_qty": allocated_qty,
            "unallocated_qty": max(stock_qty - allocated_qty, 0),
            "has_pending_quantities": any(row["quantity"] is None for row in rows),
            "placements": rows,
            "station_options": self.repo.list_station_options(fixture.id, fixture.customer_id),
        }

    def get_overview(self, customer_id: int, keyword: str = "") -> dict:
        containers = self.repo.list_containers(customer_id, keyword)
        code_rows = self.repo.list_code_overview_rows(customer_id, keyword)
        code_rows_by_container: dict[int, list[dict]] = {}
        for row in code_rows:
            if row["container_id"] is not None:
                code_rows_by_container.setdefault(row["container_id"], []).append(row)
        container_rows = []
        for container in containers:
            related = code_rows_by_container.get(container.id, [])
            row = self._serialize_container(container)
            row.update(
                code_count=len(related),
                fixture_type_count=sum(item["fixture_type_count"] for item in related),
                total_quantity=sum(item["total_quantity"] for item in related),
                pending_quantity_count=sum(item["pending_quantity_count"] for item in related),
            )
            container_rows.append(row)
        return {
            "customer_id": customer_id,
            "containers": container_rows,
            "codes": code_rows,
            "ungrouped_code_count": sum(1 for row in code_rows if row["container_id"] is None),
            "pending_quantity_count": sum(row["pending_quantity_count"] for row in code_rows),
        }

    def _serialize_container(self, row: StorageContainer) -> dict:
        return {
            "id": row.id,
            "customer_id": row.customer_id,
            "name": row.name,
            "description": row.description,
            "code_count": 0,
            "fixture_type_count": 0,
            "total_quantity": 0,
            "pending_quantity_count": 0,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }

    def _serialize_placement(self, row: FixturePlacement) -> dict:
        code = self.repo.get_code(row.storage_code_id) if row.storage_code_id is not None else None
        container = self.repo.get_container(code.container_id) if code is not None and code.container_id is not None else None
        model = self.repo.get_model(row.model_id) if row.model_id is not None else None
        station = self.repo.get_station(row.station_id) if row.station_id is not None else None
        if row.target_type == "storage_code":
            display_label = " / ".join(part for part in [None if container is None else container.name, None if code is None else code.code] if part)
        else:
            display_label = " / ".join(part for part in [None if model is None else model.name, None if station is None else station.code] if part)
        return {
            "id": row.id,
            "fixture_id": row.fixture_id,
            "target_type": row.target_type,
            "storage_code_id": row.storage_code_id,
            "storage_code": None if code is None else code.code,
            "container_id": None if container is None else container.id,
            "container_name": None if container is None else container.name,
            "model_id": row.model_id,
            "model_code": None if model is None else model.code,
            "model_name": None if model is None else model.name,
            "station_id": row.station_id,
            "station_code": None if station is None else station.code,
            "station_name": None if station is None else station.name,
            "quantity": row.quantity,
            "source": row.source,
            "display_label": display_label,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
