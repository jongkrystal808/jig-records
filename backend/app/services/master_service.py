from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.auth import SessionContext
from backend.app.repositories.inventory_repository import InventoryRepository
from backend.app.repositories.master_repository import MasterRepository
from backend.app.services.audit_service import AuditService
from backend.app.schemas.common import CsvImportPayload
from backend.app.schemas.master import (
    CustomerCreate,
    CustomerUpdate,
    FixtureCreate,
    FixtureQualityReportRead,
    FixtureUpdate,
    MachineModelCreate,
    MachineModelUpdate,
    StationCreate,
    StationUpdate,
)
from backend.app.utils.csv_tools import parse_csv_bytes, render_csv_text
from backend.app.utils.fixture_images import resolve_fixture_image_path


def _parse_bool(value: str, *, default: bool = True) -> bool:
    normalized = value.strip().lower()
    if not normalized:
        return default
    return normalized in {"1", "true", "yes", "y", "on", "啟用", "啟用中"}


class MasterService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = MasterRepository(db)
        self.inventory_repo = InventoryRepository(db)
        self.audit = AuditService(db)

    def _sync_fixture_stock_status(self, fixture_id: int, min_stock_qty: int) -> None:
        summary = self.inventory_repo.get_or_create_stock_summary(fixture_id)
        self.inventory_repo.set_stock_status(summary, min_stock_qty, touch_last_transaction=False)

    @staticmethod
    def _normalize_storage_location(value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @classmethod
    def _compose_storage_location(
        cls,
        line_storage_location: str | None,
        department_storage_location: str | None,
    ) -> str | None:
        line = cls._normalize_storage_location(line_storage_location)
        department = cls._normalize_storage_location(department_storage_location)
        if line or department:
            return " / ".join(part for part in [line, department] if part)
        return None

    @classmethod
    def _split_storage_location(cls, storage_location: str | None) -> tuple[str | None, str | None]:
        normalized = cls._normalize_storage_location(storage_location)
        if not normalized:
            return None, None
        if " / " in normalized:
            left, right = normalized.split(" / ", 1)
            return cls._normalize_storage_location(left), cls._normalize_storage_location(right)
        return normalized, None

    @classmethod
    def _resolve_storage_fields(
        cls,
        line_storage_location: str | None,
        department_storage_location: str | None,
    ) -> tuple[str | None, str | None, str | None]:
        line = cls._normalize_storage_location(line_storage_location)
        department = cls._normalize_storage_location(department_storage_location)
        return line, department, cls._compose_storage_location(line, department)

    @classmethod
    def _read_storage_fields(cls, fixture) -> tuple[str | None, str | None, str | None]:
        line = cls._normalize_storage_location(getattr(fixture, "line_storage_location", None))
        department = cls._normalize_storage_location(getattr(fixture, "department_storage_location", None))
        return line, department, cls._compose_storage_location(line, department)

    def create_customer(self, payload: CustomerCreate, actor: SessionContext | None = None):
        assigned_user_ids = sorted({int(user_id) for user_id in payload.assigned_user_ids})
        users = self.repo.list_users_by_ids(assigned_user_ids)
        found_user_ids = {user.id for user in users}
        missing_user_ids = [user_id for user_id in assigned_user_ids if user_id not in found_user_ids]
        if missing_user_ids:
            raise ValueError(f"user {missing_user_ids[0]} not found")
        try:
            customer = self.repo.create_customer(code=payload.code, name=payload.name)
            self.repo.replace_allowed_users_for_customer(customer.id, assigned_user_ids)
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
            return self._serialize_customer(customer)
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("customer code or name already exists") from exc

    def list_customers(self):
        return [self._serialize_customer(customer) for customer in self.repo.list_customers()]

    def update_customer(self, customer_id: int, payload: CustomerUpdate, actor: SessionContext | None = None):
        customer = self.repo.get_customer(customer_id)
        if customer is None:
            raise ValueError(f"customer {customer_id} not found")
        assigned_user_ids = sorted({int(user_id) for user_id in payload.assigned_user_ids})
        users = self.repo.list_users_by_ids(assigned_user_ids)
        found_user_ids = {user.id for user in users}
        missing_user_ids = [user_id for user_id in assigned_user_ids if user_id not in found_user_ids]
        if missing_user_ids:
            raise ValueError(f"user {missing_user_ids[0]} not found")
        before_code = customer.code
        before_name = customer.name
        try:
            customer = self.repo.update_customer(customer, code=payload.code.strip(), name=payload.name.strip())
            self.repo.replace_allowed_users_for_customer(customer.id, assigned_user_ids)
            self.audit.record(
                customer_id=customer.id,
                entity_type="customer",
                entity_key=customer.code,
                action="update",
                summary=f"更新客戶 {before_code} / {before_name} -> {customer.code} / {customer.name}",
                actor=actor,
            )
            self.db.commit()
            self.db.refresh(customer)
            return self._serialize_customer(customer)
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("customer code or name already exists") from exc

    def create_fixture(self, payload: FixtureCreate, actor: SessionContext | None = None):
        customer = self.repo.get_customer(payload.customer_id)
        if customer is None:
            raise ValueError(f"customer {payload.customer_id} not found")
        if payload.responsible_user_id is not None:
            user = self.repo.get_user(payload.responsible_user_id)
            if user is None:
                raise ValueError(f"user {payload.responsible_user_id} not found")
            if payload.responsible_user_id not in self.repo.list_allowed_user_ids_for_customer(payload.customer_id):
                raise ValueError(f"user {payload.responsible_user_id} is not assigned to customer {payload.customer_id}")
        line_storage_location, department_storage_location, _ = self._resolve_storage_fields(
            payload.line_storage_location,
            payload.department_storage_location,
        )
        try:
            fixture = self.repo.create_fixture(
                customer_id=payload.customer_id,
                responsible_user_id=payload.responsible_user_id,
                code=payload.code,
                name=payload.name,
                line_storage_location=line_storage_location,
                department_storage_location=department_storage_location,
                description=payload.description,
            )
            level = self.repo.get_or_create_stock_level(fixture.id)
            if payload.min_stock_qty is not None:
                level.min_stock_qty = payload.min_stock_qty
            self._sync_fixture_stock_status(fixture.id, level.min_stock_qty)
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
            raise ValueError("fixture code already exists within customer") from exc

    def list_fixtures(self, customer_id: int | None = None):
        fixtures = self.repo.list_fixtures(customer_id=customer_id)
        stock_levels = self.repo.list_stock_levels([fixture.id for fixture in fixtures])
        return [
            self._serialize_fixture(
                fixture,
                0 if (level := stock_levels.get(fixture.id)) is None else level.min_stock_qty,
            )
            for fixture in fixtures
        ]

    def build_fixture_quality_report(self, customer_id: int) -> FixtureQualityReportRead:
        fixtures = [fixture for fixture in self.repo.list_fixtures(customer_id=customer_id) if fixture.is_active]
        fixture_ids = [fixture.id for fixture in fixtures]
        stock_levels = self.repo.list_stock_levels(fixture_ids)
        stock_summary_by_fixture = self.inventory_repo.list_stock_summary_rows(customer_id=customer_id)
        identifier_stock_rows = self.inventory_repo.list_identifier_stock_summary_rows(customer_id=customer_id)
        related_model_count_by_fixture = self.repo.count_related_models_by_fixture(fixture_ids)

        stock_qty_by_fixture = {int(row["fixture_id"]): int(row["stock_qty"] or 0) for row in stock_summary_by_fixture}
        identifier_stock_qty_by_fixture: dict[int, int] = {}
        for row in identifier_stock_rows:
            fixture_id = int(row["fixture_id"])
            identifier_stock_qty_by_fixture[fixture_id] = identifier_stock_qty_by_fixture.get(fixture_id, 0) + int(row["stock_qty"] or 0)

        rows: list[dict] = []
        counts = {
            "missing_name": 0,
            "missing_storage_location": 0,
            "missing_image": 0,
            "missing_min_stock_qty": 0,
            "missing_model_relation": 0,
            "stock_mismatch": 0,
        }
        for fixture in fixtures:
            fixture_name = (fixture.name or "").strip() or None
            _, _, storage_location = self._read_storage_fields(fixture)
            min_stock_qty = stock_levels.get(fixture.id).min_stock_qty if stock_levels.get(fixture.id) is not None else 0
            stock_qty = stock_qty_by_fixture.get(fixture.id, 0)
            identifier_stock_qty = identifier_stock_qty_by_fixture.get(fixture.id, 0)
            related_model_count = related_model_count_by_fixture.get(fixture.id, 0)
            has_image = resolve_fixture_image_path(fixture.code) is not None

            issue_codes: list[str] = []
            if not fixture_name:
                issue_codes.append("missing_name")
            if not storage_location:
                issue_codes.append("missing_storage_location")
            if not has_image:
                issue_codes.append("missing_image")
            if min_stock_qty <= 0:
                issue_codes.append("missing_min_stock_qty")
            if related_model_count <= 0:
                issue_codes.append("missing_model_relation")
            if stock_qty != identifier_stock_qty:
                issue_codes.append("stock_mismatch")

            if not issue_codes:
                continue

            for issue_code in issue_codes:
                counts[issue_code] += 1
            rows.append(
                {
                    "fixture_id": fixture.id,
                    "fixture_code": fixture.code,
                    "fixture_name": fixture_name,
                    "storage_location": storage_location,
                    "min_stock_qty": int(min_stock_qty),
                    "stock_qty": int(stock_qty),
                    "identifier_stock_qty": int(identifier_stock_qty),
                    "related_model_count": int(related_model_count),
                    "has_image": has_image,
                    "issue_codes": issue_codes,
                }
            )

        return FixtureQualityReportRead(
            total_fixture_count=len(fixtures),
            problematic_fixture_count=len(rows),
            missing_name_count=counts["missing_name"],
            missing_storage_location_count=counts["missing_storage_location"],
            missing_image_count=counts["missing_image"],
            missing_min_stock_qty_count=counts["missing_min_stock_qty"],
            missing_model_relation_count=counts["missing_model_relation"],
            stock_mismatch_count=counts["stock_mismatch"],
            rows=rows,
        )

    def get_fixture_detail(self, fixture_id: int, customer_id: int | None = None):
        fixture = self.repo.get_fixture(fixture_id)
        if fixture is None:
            raise ValueError(f"fixture {fixture_id} not found")
        if customer_id is not None and fixture.customer_id != customer_id:
            raise ValueError(f"fixture {fixture_id} not found")
        level = self.repo.get_stock_level(fixture.id)
        return self._serialize_fixture(fixture, 0 if level is None else level.min_stock_qty)

    def update_fixture(self, fixture_id: int, payload: FixtureUpdate, actor: SessionContext | None = None):
        fixture = self.repo.get_fixture(fixture_id)
        if fixture is None:
            raise ValueError(f"fixture {fixture_id} not found")
        customer = self.repo.get_customer(payload.customer_id)
        if customer is None:
            raise ValueError(f"customer {payload.customer_id} not found")
        if payload.responsible_user_id is not None:
            user = self.repo.get_user(payload.responsible_user_id)
            if user is None:
                raise ValueError(f"user {payload.responsible_user_id} not found")
            if payload.responsible_user_id not in self.repo.list_allowed_user_ids_for_customer(payload.customer_id):
                raise ValueError(f"user {payload.responsible_user_id} is not assigned to customer {payload.customer_id}")
        line_storage_location, department_storage_location, _ = self._resolve_storage_fields(
            payload.line_storage_location,
            payload.department_storage_location,
        )
        try:
            fixture = self.repo.update_fixture(
                fixture,
                customer_id=payload.customer_id,
                responsible_user_id=payload.responsible_user_id,
                code=payload.code,
                name=payload.name,
                line_storage_location=line_storage_location,
                department_storage_location=department_storage_location,
                description=payload.description,
                is_active=payload.is_active,
            )
            level = self.repo.get_or_create_stock_level(fixture.id)
            if payload.min_stock_qty is not None:
                level.min_stock_qty = payload.min_stock_qty
            self._sync_fixture_stock_status(fixture.id, level.min_stock_qty)
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
            raise ValueError("fixture code already exists within customer") from exc

    def delete_fixture(
        self,
        fixture_id: int,
        *,
        customer_id: int,
        delete_transactions: bool,
        actor: SessionContext | None = None,
    ) -> dict:
        fixture = self.repo.get_fixture(fixture_id)
        if fixture is None or fixture.customer_id != customer_id:
            raise ValueError(f"fixture {fixture_id} not found")

        fixture_code = fixture.code
        fixture_name = fixture.name
        try:
            transaction_stats = self.inventory_repo.remove_fixture_transaction_items(
                fixture,
                delete_records=delete_transactions,
            )
            deleted_requirement_count = self.repo.delete_fixture(fixture)
            record_action = "並刪除相關收退料明細" if delete_transactions else "並保留相關收退料歷史"
            self.audit.record(
                customer_id=customer_id,
                entity_type="fixture",
                entity_key=fixture_code,
                action="delete",
                summary=(
                    f"永久刪除治具 {fixture_code} / {fixture_name}，{record_action}；"
                    f"影響 {transaction_stats['transaction_item_count']} 筆明細"
                ),
                actor=actor,
            )
            self.db.commit()
            return {
                "fixture_id": fixture_id,
                "fixture_code": fixture_code,
                "transaction_records_deleted": delete_transactions,
                "deleted_requirement_count": deleted_requirement_count,
                **transaction_stats,
            }
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("治具仍被其他資料引用，無法刪除") from exc

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

    def get_model_detail(self, model_id: int, customer_id: int | None = None):
        model = self.repo.get_model(model_id, customer_id=customer_id)
        if model is None:
            raise ValueError(f"model {model_id} not found")
        return model

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

    def export_fixtures_csv(self, customer_id: int) -> str:
        fixtures = self.repo.list_fixtures(customer_id=customer_id)
        rows = [
            {
                "code": fixture.code,
                "name": fixture.name,
                "line_storage_location": self._read_storage_fields(fixture)[0] or "",
                "department_storage_location": self._read_storage_fields(fixture)[1] or "",
                "min_stock_qty": 0 if (level := self.repo.get_stock_level(fixture.id)) is None else level.min_stock_qty,
                "description": fixture.description or "",
                "is_active": str(fixture.is_active),
            }
            for fixture in fixtures
        ]
        return render_csv_text(
            ["code", "name", "line_storage_location", "department_storage_location", "min_stock_qty", "description", "is_active"],
            rows,
        )

    def fixture_template_csv(self) -> str:
        return render_csv_text(
            ["code", "name", "line_storage_location", "department_storage_location", "min_stock_qty", "description", "is_active"],
            [
                {
                    "code": "C-00001",
                    "name": "RJ45 Fixture",
                    "line_storage_location": "A-01-01",
                    "department_storage_location": "RD-SHELF-3",
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
            if not code or not name:
                continue
            line_storage_location = self._normalize_storage_location(row.get("line_storage_location", ""))
            department_storage_location = self._normalize_storage_location(row.get("department_storage_location", ""))
            if line_storage_location is None and department_storage_location is None:
                line_storage_location, department_storage_location = self._split_storage_location(row.get("storage_location", ""))
            line_storage_location, department_storage_location, _ = self._resolve_storage_fields(
                line_storage_location,
                department_storage_location,
            )
            min_stock_qty = int(row.get("min_stock_qty", "0") or "0")
            description = row.get("description", "") or None
            is_active = _parse_bool(row.get("is_active", ""), default=True)
            fixture = self.repo.get_fixture_by_code(code, customer_id=customer_id)
            if fixture is None:
                fixture = self.repo.create_fixture(
                    customer_id=customer_id,
                    responsible_user_id=None,
                    code=code,
                    name=name,
                    line_storage_location=line_storage_location,
                    department_storage_location=department_storage_location,
                    description=description,
                )
            else:
                self.repo.update_fixture(
                    fixture,
                    customer_id=customer_id,
                    responsible_user_id=None,
                    code=code,
                    name=name,
                    line_storage_location=line_storage_location,
                    department_storage_location=department_storage_location,
                    description=description,
                    is_active=is_active,
                )
            level = self.repo.get_or_create_stock_level(fixture.id)
            level.min_stock_qty = min_stock_qty
            fixture.is_active = is_active
            self._sync_fixture_stock_status(fixture.id, level.min_stock_qty)
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
        line_storage_location, department_storage_location, _ = self._read_storage_fields(fixture)
        return {
            "id": fixture.id,
            "customer_id": fixture.customer_id,
            "responsible_user_id": fixture.responsible_user_id,
            "code": fixture.code,
            "name": fixture.name,
            "line_storage_location": line_storage_location,
            "department_storage_location": department_storage_location,
            "min_stock_qty": min_stock_qty,
            "description": fixture.description,
            "is_active": fixture.is_active,
            "created_at": fixture.created_at,
            "updated_at": fixture.updated_at,
        }

    def _serialize_customer(self, customer) -> dict:
        return {
            "id": customer.id,
            "code": customer.code,
            "name": customer.name,
            "assigned_user_ids": self.repo.list_allowed_user_ids_for_customer(customer.id),
            "created_at": customer.created_at,
            "updated_at": customer.updated_at,
        }
