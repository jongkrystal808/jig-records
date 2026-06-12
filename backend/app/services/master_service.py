from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.auth import SessionContext
from backend.app.repositories.master_repository import MasterRepository
from backend.app.services.audit_service import AuditService
from backend.app.schemas.common import CsvImportPayload
from backend.app.schemas.master import (
    CustomerCreate,
    FixtureCreate,
    FixtureUpdate,
    MachineModelCreate,
    MachineModelUpdate,
    OwnerCreate,
    OwnerUpdate,
    StationCreate,
    StationUpdate,
)
from backend.app.utils.csv_tools import parse_csv_bytes, render_csv_text


def _parse_bool(value: str, *, default: bool = True) -> bool:
    normalized = value.strip().lower()
    if not normalized:
        return default
    return normalized in {"1", "true", "yes", "y", "on", "啟用", "啟用中"}


class MasterService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = MasterRepository(db)
        self.audit = AuditService(db)

    @staticmethod
    def _normalize_storage_location(value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    def create_customer(self, payload: CustomerCreate, actor: SessionContext | None = None):
        try:
            customer = self.repo.create_customer(code=payload.code, name=payload.name)
            self.audit.record(
                customer_id=customer.id,
                entity_type="customer",
                entity_key=customer.code,
                action="create",
                summary=f"建立客戶 {customer.code} / {customer.name}",
                actor=actor,
            )
            self.db.commit()
            self.db.refresh(customer)
            return customer
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("customer code or name already exists") from exc

    def list_customers(self):
        return self.repo.list_customers()

    def create_fixture(self, payload: FixtureCreate, actor: SessionContext | None = None):
        customer = self.repo.get_customer(payload.customer_id)
        if customer is None:
            raise ValueError(f"customer {payload.customer_id} not found")
        if payload.owner_id is not None and self.repo.get_owner(payload.owner_id) is None:
            raise ValueError(f"owner {payload.owner_id} not found")
        try:
            fixture = self.repo.create_fixture(
                customer_id=payload.customer_id,
                owner_id=payload.owner_id,
                code=payload.code,
                name=payload.name,
                manage_type=payload.manage_type,
                storage_location=self._normalize_storage_location(payload.storage_location),
                description=payload.description,
            )
            level = self.repo.get_or_create_stock_level(fixture.id)
            if payload.min_stock_qty is not None:
                level.min_stock_qty = payload.min_stock_qty
            self.audit.record(
                customer_id=payload.customer_id,
                entity_type="fixture",
                entity_key=fixture.code,
                action="create",
                summary=f"建立治具 {fixture.code} / {fixture.name}",
                actor=actor,
            )
            self.db.commit()
            self.db.refresh(fixture)
            return self._serialize_fixture(fixture, level.min_stock_qty)
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("fixture code already exists") from exc

    def list_fixtures(self, customer_id: int | None = None):
        fixtures = self.repo.list_fixtures(customer_id=customer_id)
        return [
            self._serialize_fixture(
                fixture,
                0 if (level := self.repo.get_stock_level(fixture.id)) is None else level.min_stock_qty,
            )
            for fixture in fixtures
        ]

    def update_fixture(self, fixture_id: int, payload: FixtureUpdate, actor: SessionContext | None = None):
        fixture = self.repo.get_fixture(fixture_id)
        if fixture is None:
            raise ValueError(f"fixture {fixture_id} not found")
        customer = self.repo.get_customer(payload.customer_id)
        if customer is None:
            raise ValueError(f"customer {payload.customer_id} not found")
        if payload.owner_id is not None and self.repo.get_owner(payload.owner_id) is None:
            raise ValueError(f"owner {payload.owner_id} not found")
        try:
            fixture = self.repo.update_fixture(
                fixture,
                customer_id=payload.customer_id,
                owner_id=payload.owner_id,
                code=payload.code,
                name=payload.name,
                manage_type=payload.manage_type,
                storage_location=self._normalize_storage_location(payload.storage_location),
                description=payload.description,
                is_active=payload.is_active,
            )
            level = self.repo.get_or_create_stock_level(fixture.id)
            if payload.min_stock_qty is not None:
                level.min_stock_qty = payload.min_stock_qty
            self.audit.record(
                customer_id=payload.customer_id,
                entity_type="fixture",
                entity_key=fixture.code,
                action="update",
                summary=f"更新治具 {fixture.code} / {fixture.name}",
                actor=actor,
            )
            self.db.commit()
            self.db.refresh(fixture)
            return self._serialize_fixture(fixture, level.min_stock_qty)
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("fixture code already exists") from exc

    def create_model(self, payload: MachineModelCreate, actor: SessionContext | None = None):
        customer = self.repo.get_customer(payload.customer_id)
        if customer is None:
            raise ValueError(f"customer {payload.customer_id} not found")
        existing = self.repo.get_model_by_code(payload.code, customer_id=payload.customer_id)
        if existing is not None:
            raise ValueError("model code already exists")
        try:
            model = self.repo.create_model(customer_id=payload.customer_id, code=payload.code, name=payload.name)
            self.audit.record(
                customer_id=payload.customer_id,
                entity_type="model",
                entity_key=model.code,
                action="create",
                summary=f"建立機種 {model.code} / {model.name}",
                actor=actor,
            )
            self.db.commit()
            self.db.refresh(model)
            return model
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("model code already exists") from exc

    def list_models(self, customer_id: int | None = None):
        return self.repo.list_models(customer_id=customer_id)

    def update_model(self, model_id: int, payload: MachineModelUpdate, actor: SessionContext | None = None):
        customer = self.repo.get_customer(payload.customer_id)
        if customer is None:
            raise ValueError(f"customer {payload.customer_id} not found")
        model = self.repo.get_model(model_id, customer_id=payload.customer_id)
        if model is None:
            raise ValueError(f"model {model_id} not found")
        before_code = model.code
        before_name = model.name
        before_active = model.is_active
        try:
            model = self.repo.update_model(model, code=payload.code, name=payload.name, is_active=payload.is_active)
            self.audit.record(
                customer_id=payload.customer_id,
                entity_type="model",
                entity_key=model.code,
                action="update",
                summary=(
                    f"更新機種 {before_code}：{before_name} / {'啟用' if before_active else '停用'}"
                    f" -> {model.code} / {model.name} / {'啟用' if model.is_active else '停用'}"
                ),
                actor=actor,
            )
            self.db.commit()
            self.db.refresh(model)
            return model
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("model code already exists") from exc

    def create_station(self, payload: StationCreate, actor: SessionContext | None = None):
        customer = self.repo.get_customer(payload.customer_id)
        if customer is None:
            raise ValueError(f"customer {payload.customer_id} not found")
        existing = self.repo.get_station_by_code(payload.code, customer_id=payload.customer_id)
        if existing is not None:
            raise ValueError("station code already exists")
        try:
            station = self.repo.create_station(customer_id=payload.customer_id, code=payload.code, name=payload.name)
            self.audit.record(
                customer_id=payload.customer_id,
                entity_type="station",
                entity_key=station.code,
                action="create",
                summary=f"建立站點 {station.code} / {station.name}",
                actor=actor,
            )
            self.db.commit()
            self.db.refresh(station)
            return station
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("station code already exists") from exc

    def list_stations(self, customer_id: int | None = None):
        return self.repo.list_stations(customer_id=customer_id)

    def update_station(self, station_id: int, payload: StationUpdate, actor: SessionContext | None = None):
        customer = self.repo.get_customer(payload.customer_id)
        if customer is None:
            raise ValueError(f"customer {payload.customer_id} not found")
        station = self.repo.get_station(station_id, customer_id=payload.customer_id)
        if station is None:
            raise ValueError(f"station {station_id} not found")
        before_code = station.code
        before_name = station.name
        before_active = station.is_active
        try:
            station = self.repo.update_station(station, code=payload.code, name=payload.name, is_active=payload.is_active)
            self.audit.record(
                customer_id=payload.customer_id,
                entity_type="station",
                entity_key=station.code,
                action="update",
                summary=(
                    f"更新站點 {before_code}：{before_name} / {'啟用' if before_active else '停用'}"
                    f" -> {station.code} / {station.name} / {'啟用' if station.is_active else '停用'}"
                ),
                actor=actor,
            )
            self.db.commit()
            self.db.refresh(station)
            return station
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("station code already exists") from exc

    def create_owner(self, payload: OwnerCreate, actor: SessionContext | None = None):
        try:
            owner = self.repo.create_owner(name=payload.name)
            self.audit.record(
                customer_id=None,
                entity_type="owner",
                entity_key=owner.name,
                action="create",
                summary=f"建立負責人 {owner.name}",
                actor=actor,
            )
            self.db.commit()
            self.db.refresh(owner)
            return owner
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("owner name already exists") from exc

    def list_owners(self):
        return self.repo.list_owners()

    def update_owner(self, owner_id: int, payload: OwnerUpdate, actor: SessionContext | None = None):
        owner = self.repo.get_owner(owner_id)
        if owner is None:
            raise ValueError(f"owner {owner_id} not found")
        before_name = owner.name
        before_active = owner.is_active
        try:
            owner = self.repo.update_owner(owner, name=payload.name, is_active=payload.is_active)
            self.audit.record(
                customer_id=None,
                entity_type="owner",
                entity_key=owner.name,
                action="update",
                summary=(
                    f"更新負責人 {before_name}：{'啟用' if before_active else '停用'}"
                    f" -> {owner.name} / {'啟用' if owner.is_active else '停用'}"
                ),
                actor=actor,
            )
            self.db.commit()
            self.db.refresh(owner)
            return owner
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("owner name already exists") from exc

    def export_fixtures_csv(self, customer_id: int) -> str:
        fixtures = self.repo.list_fixtures(customer_id=customer_id)
        owner_map = {owner.id: owner.name for owner in self.repo.list_owners()}
        rows = [
            {
                "code": fixture.code,
                "name": fixture.name,
                "manage_type": fixture.manage_type,
                "storage_location": fixture.storage_location or "",
                "owner_name": owner_map.get(fixture.owner_id, "") if fixture.owner_id else "",
                "min_stock_qty": 0 if (level := self.repo.get_stock_level(fixture.id)) is None else level.min_stock_qty,
                "description": fixture.description or "",
                "is_active": str(fixture.is_active),
            }
            for fixture in fixtures
        ]
        return render_csv_text(
            ["code", "name", "manage_type", "storage_location", "owner_name", "min_stock_qty", "description", "is_active"],
            rows,
        )

    def fixture_template_csv(self) -> str:
        return render_csv_text(
            ["code", "name", "manage_type", "storage_location", "owner_name", "min_stock_qty", "description", "is_active"],
            [
                {
                    "code": "C-00001",
                    "name": "RJ45 Fixture",
                    "manage_type": "datecode",
                    "storage_location": "A-01-01",
                    "owner_name": "",
                    "min_stock_qty": "10",
                    "description": "sample",
                    "is_active": "true",
                }
            ],
        )

    def import_fixtures_csv(self, customer_id: int, payload: CsvImportPayload, actor: SessionContext | None = None) -> int:
        customer = self.repo.get_customer(customer_id)
        if customer is None:
            raise ValueError(f"customer {customer_id} not found")
        rows = parse_csv_bytes(payload.content.encode("utf-8"))
        imported_count = 0
        for row in rows:
            code = row.get("code", "")
            name = row.get("name", "")
            manage_type = row.get("manage_type", "datecode") or "datecode"
            if not code or not name:
                continue
            storage_location = self._normalize_storage_location(row.get("storage_location", ""))
            owner_name = row.get("owner_name", "")
            owner = self.repo.get_owner_by_name(owner_name) if owner_name else None
            min_stock_qty = int(row.get("min_stock_qty", "0") or "0")
            description = row.get("description", "") or None
            is_active = _parse_bool(row.get("is_active", ""), default=True)
            fixture = self.repo.get_fixture_by_code(code, customer_id=customer_id)
            if fixture is None:
                fixture = self.repo.create_fixture(
                    customer_id=customer_id,
                    owner_id=owner.id if owner else None,
                    code=code,
                    name=name,
                    manage_type=manage_type,
                    storage_location=storage_location,
                    description=description,
                )
            else:
                self.repo.update_fixture(
                    fixture,
                    customer_id=customer_id,
                    owner_id=owner.id if owner else None,
                    code=code,
                    name=name,
                    manage_type=manage_type,
                    storage_location=storage_location,
                    description=description,
                    is_active=is_active,
                )
            level = self.repo.get_or_create_stock_level(fixture.id)
            level.min_stock_qty = min_stock_qty
            fixture.is_active = is_active
            imported_count += 1
        self.audit.record(
            customer_id=customer_id,
            entity_type="fixture",
            entity_key=customer.code,
            action="import",
            summary=f"匯入治具資料，共 {imported_count} 筆",
            actor=actor,
        )
        self.db.commit()
        return imported_count

    def export_models_csv(self, customer_id: int | None = None) -> str:
        rows_source = self.repo.list_models(customer_id=customer_id)
        return render_csv_text(
            ["code", "name", "is_active"],
            [{"code": row.code, "name": row.name, "is_active": str(row.is_active)} for row in rows_source],
        )

    def model_template_csv(self) -> str:
        return render_csv_text(
            ["code", "name", "is_active"],
            [{"code": "VPort-254", "name": "VPort 254", "is_active": "true"}],
        )

    def import_models_csv(self, customer_id: int | None, payload: CsvImportPayload, actor: SessionContext | None = None) -> int:
        if customer_id is None:
            raise ValueError("customer_id is required")
        customer = self.repo.get_customer(customer_id)
        if customer is None:
            raise ValueError(f"customer {customer_id} not found")
        rows = parse_csv_bytes(payload.content.encode("utf-8"))
        imported_count = 0
        for row in rows:
            code = row.get("code", "")
            name = row.get("name", "")
            if not code or not name:
                continue
            is_active = _parse_bool(row.get("is_active", ""), default=True)
            model = self.repo.get_model_by_code(code, customer_id=customer_id)
            if model is None:
                self.repo.create_model(customer_id=customer_id, code=code, name=name)
                model = self.repo.get_model_by_code(code, customer_id=customer_id)
            if model is not None:
                self.repo.update_model(model, code=code, name=name, is_active=is_active)
                imported_count += 1
        self.audit.record(
            customer_id=customer_id,
            entity_type="model",
            entity_key=customer.code,
            action="import",
            summary=f"匯入機種資料，共 {imported_count} 筆",
            actor=actor,
        )
        self.db.commit()
        return imported_count

    def export_stations_csv(self, customer_id: int | None = None) -> str:
        rows_source = self.repo.list_stations(customer_id=customer_id)
        return render_csv_text(
            ["code", "name", "is_active"],
            [{"code": row.code, "name": row.name, "is_active": str(row.is_active)} for row in rows_source],
        )

    def station_template_csv(self) -> str:
        return render_csv_text(
            ["code", "name", "is_active"],
            [{"code": "ST-01", "name": "Burn-In", "is_active": "true"}],
        )

    def import_stations_csv(self, customer_id: int | None, payload: CsvImportPayload, actor: SessionContext | None = None) -> int:
        if customer_id is None:
            raise ValueError("customer_id is required")
        customer = self.repo.get_customer(customer_id)
        if customer is None:
            raise ValueError(f"customer {customer_id} not found")
        rows = parse_csv_bytes(payload.content.encode("utf-8"))
        imported_count = 0
        for row in rows:
            code = row.get("code", "")
            name = row.get("name", "")
            if not code or not name:
                continue
            is_active = _parse_bool(row.get("is_active", ""), default=True)
            station = self.repo.get_station_by_code(code, customer_id=customer_id)
            if station is None:
                self.repo.create_station(customer_id=customer_id, code=code, name=name)
                station = self.repo.get_station_by_code(code, customer_id=customer_id)
            if station is not None:
                self.repo.update_station(station, code=code, name=name, is_active=is_active)
                imported_count += 1
        self.audit.record(
            customer_id=customer_id,
            entity_type="station",
            entity_key=customer.code,
            action="import",
            summary=f"匯入站點資料，共 {imported_count} 筆",
            actor=actor,
        )
        self.db.commit()
        return imported_count

    def _serialize_fixture(self, fixture, min_stock_qty: int) -> dict:
        return {
            "id": fixture.id,
            "customer_id": fixture.customer_id,
            "owner_id": fixture.owner_id,
            "code": fixture.code,
            "name": fixture.name,
            "manage_type": fixture.manage_type,
            "storage_location": fixture.storage_location,
            "min_stock_qty": min_stock_qty,
            "description": fixture.description,
            "is_active": fixture.is_active,
            "created_at": fixture.created_at,
            "updated_at": fixture.updated_at,
        }
