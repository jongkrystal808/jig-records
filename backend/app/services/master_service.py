import logging
from pathlib import Path

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
    MachineModelDeleteRead,
    MachineModelUpdate,
    StationCreate,
    StationDeleteRead,
    StationUpdate,
)
from backend.app.utils.csv_tools import parse_csv_bytes, render_csv_text, stream_csv_text
from backend.app.utils.fixture_images import (
    delete_fixture_image,
    delete_legacy_fixture_image,
    list_fixture_image_codes,
    list_legacy_fixture_image_codes,
    rename_fixture_image,
    resolve_fixture_image_path,
    resolve_legacy_fixture_image_path,
    rollback_fixture_image_rename,
    save_fixture_image,
)


logger = logging.getLogger(__name__)


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

    def _resolve_fixture_image(self, fixture, *, legacy_unique_codes: set[str] | None = None) -> Path | None:
        image_path = resolve_fixture_image_path(fixture.customer_id, fixture.code)
        if image_path is not None:
            return image_path
        legacy_is_safe = (
            fixture.code in legacy_unique_codes
            if legacy_unique_codes is not None
            else self.repo.is_fixture_code_globally_unique(fixture.code)
        )
        return resolve_legacy_fixture_image_path(fixture.code) if legacy_is_safe else None

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
        customers = self.repo.list_customers()
        assigned_user_ids = self.repo.list_allowed_user_ids_for_customers(
            [customer.id for customer in customers]
        )
        return [
            self._serialize_customer(
                customer,
                assigned_user_ids=assigned_user_ids[customer.id],
            )
            for customer in customers
        ]

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
            from backend.app.services.storage_service import StorageService

            StorageService(self.db).sync_fixture_storage_fields(
                fixture, line_storage_location, department_storage_location
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
        legacy_unique_codes = self.repo.list_globally_unique_fixture_codes([fixture.code for fixture in fixtures])
        return [
            self._serialize_fixture(
                fixture,
                0 if (level := stock_levels.get(fixture.id)) is None else level.min_stock_qty,
                legacy_unique_codes=legacy_unique_codes,
            )
            for fixture in fixtures
        ]

    def _fixture_image_codes(self, customer_id: int) -> set[str]:
        scoped_codes = list_fixture_image_codes(customer_id)
        legacy_codes = list_legacy_fixture_image_codes()
        safe_legacy_codes = self.repo.list_globally_unique_fixture_codes(list(legacy_codes))
        return scoped_codes | safe_legacy_codes

    def list_fixtures_page(
        self,
        *,
        customer_id: int,
        page: int,
        page_size: int,
        keyword: str = "",
        is_active: bool | None = None,
        image_status: str = "all",
    ) -> dict:
        image_codes = None
        has_image = None
        if image_status != "all":
            image_codes = self._fixture_image_codes(customer_id)
            has_image = image_status == "with-image"
        fixtures, total = self.repo.list_fixtures_page(
            customer_id=customer_id,
            page=page,
            page_size=page_size,
            keyword=keyword,
            is_active=is_active,
            image_codes=image_codes,
            has_image=has_image,
        )
        levels = self.repo.list_stock_levels([fixture.id for fixture in fixtures])
        unique_codes = self.repo.list_globally_unique_fixture_codes([fixture.code for fixture in fixtures])
        return {
            "items": [
                self._serialize_fixture(
                    fixture,
                    0 if (level := levels.get(fixture.id)) is None else level.min_stock_qty,
                    legacy_unique_codes=unique_codes,
                )
                for fixture in fixtures
            ],
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    def build_fixture_quality_report(self, customer_id: int) -> FixtureQualityReportRead:
        fixtures = [fixture for fixture in self.repo.list_fixtures(customer_id=customer_id) if fixture.is_active]
        fixture_ids = [fixture.id for fixture in fixtures]
        stock_levels = self.repo.list_stock_levels(fixture_ids)
        stock_summary_by_fixture = self.inventory_repo.list_stock_summary_rows(customer_id=customer_id)
        identifier_stock_rows = self.inventory_repo.list_identifier_stock_summary_rows(customer_id=customer_id)
        related_model_count_by_fixture = self.repo.count_related_models_by_fixture(fixture_ids)
        legacy_unique_codes = self.repo.list_globally_unique_fixture_codes([fixture.code for fixture in fixtures])

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
            line_storage_location, department_storage_location, storage_location = self._read_storage_fields(fixture)
            min_stock_qty = stock_levels.get(fixture.id).min_stock_qty if stock_levels.get(fixture.id) is not None else 0
            stock_qty = stock_qty_by_fixture.get(fixture.id, 0)
            identifier_stock_qty = identifier_stock_qty_by_fixture.get(fixture.id, 0)
            related_model_count = related_model_count_by_fixture.get(fixture.id, 0)
            has_image = self._resolve_fixture_image(fixture, legacy_unique_codes=legacy_unique_codes) is not None

            issue_codes: list[str] = []
            if not fixture_name:
                issue_codes.append("missing_name")
            if line_storage_location is None and department_storage_location is None:
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

    def get_fixture_customer_id(self, fixture_id: int) -> int:
        fixture = self.repo.get_fixture(fixture_id)
        if fixture is None:
            raise ValueError(f"fixture {fixture_id} not found")
        return fixture.customer_id

    def get_fixture_image_path(self, fixture_code: str, *, customer_id: int) -> Path | None:
        fixture = self.repo.get_fixture_by_code(fixture_code, customer_id=customer_id)
        if fixture is None:
            return None
        return self._resolve_fixture_image(fixture)

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
        before_customer_id = fixture.customer_id
        before_code = fixture.code
        legacy_source_is_safe = self.repo.is_fixture_code_globally_unique(before_code)
        image_rename = None
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
            from backend.app.repositories.storage_repository import StorageRepository
            from backend.app.services.storage_service import StorageService

            if before_customer_id != fixture.customer_id:
                StorageRepository(self.db).clear_placements(fixture.id)
            StorageService(self.db).sync_fixture_storage_fields(
                fixture, line_storage_location, department_storage_location
            )
            image_rename = rename_fixture_image(
                before_customer_id,
                before_code,
                fixture.customer_id,
                fixture.code,
                allow_legacy_source=legacy_source_is_safe,
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
            image_rename = None
            self.db.refresh(fixture)
            return self._serialize_fixture(fixture, level.min_stock_qty)
        except IntegrityError as exc:
            self.db.rollback()
            rollback_fixture_image_rename(image_rename)
            raise ValueError("fixture code already exists within customer") from exc
        except Exception:
            self.db.rollback()
            rollback_fixture_image_rename(image_rename)
            raise

    def upload_fixture_image(
        self,
        fixture_id: int,
        *,
        customer_id: int,
        content: bytes,
        content_type: str | None,
        filename: str | None,
        actor: SessionContext | None = None,
    ):
        fixture = self.repo.get_fixture(fixture_id)
        if fixture is None or fixture.customer_id != customer_id:
            raise ValueError(f"fixture {fixture_id} not found")
        if not content:
            raise ValueError("fixture image content is empty")
        if len(content) > 5 * 1024 * 1024:
            raise ValueError("fixture image exceeds 5 MB limit")
        try:
            save_fixture_image(customer_id, fixture.code, content, content_type=content_type, filename=filename)
            if self.repo.is_fixture_code_globally_unique(fixture.code):
                delete_legacy_fixture_image(fixture.code)
            self.audit.record(
                customer_id=customer_id,
                entity_type="fixture",
                entity_key=fixture.code,
                action="upload_image",
                summary=f"上傳治具圖片 {fixture.code}",
                actor=actor,
            )
            self.db.commit()
            level = self.repo.get_stock_level(fixture.id)
            return {
                "fixture_id": fixture.id,
                "fixture_code": fixture.code,
                "has_image": True,
                "fixture": self._serialize_fixture(fixture, 0 if level is None else level.min_stock_qty),
            }
        except ValueError:
            self.db.rollback()
            raise

    def upload_fixture_images_batch(
        self,
        *,
        customer_id: int,
        uploads: list[dict],
        actor: SessionContext | None = None,
    ) -> dict:
        if not uploads:
            raise ValueError("請至少選擇 1 張圖片")
        if len(uploads) > 50:
            raise ValueError("單次最多可上傳 50 張圖片")

        uploaded_count = 0
        results: list[dict] = []

        for upload in uploads:
            filename = str(upload.get("filename") or "").strip()
            content = upload.get("content") or b""
            content_type = upload.get("content_type")
            fixture_code = Path(filename).stem.strip() if filename else ""

            if not filename:
                results.append({"file_name": "", "fixture_code": None, "fixture_id": None, "success": False, "message": "缺少檔名"})
                continue
            if not fixture_code:
                results.append({"file_name": filename, "fixture_code": None, "fixture_id": None, "success": False, "message": "檔名需對應治具編號"})
                continue

            fixture = self.repo.get_fixture_by_code(fixture_code, customer_id=customer_id)
            if fixture is None:
                results.append({"file_name": filename, "fixture_code": fixture_code, "fixture_id": None, "success": False, "message": "找不到對應治具編號"})
                continue
            if not content:
                results.append({"file_name": filename, "fixture_code": fixture.code, "fixture_id": fixture.id, "success": False, "message": "圖片內容不可為空"})
                continue
            if len(content) > 5 * 1024 * 1024:
                results.append({"file_name": filename, "fixture_code": fixture.code, "fixture_id": fixture.id, "success": False, "message": "單檔超過 5 MB"})
                continue

            try:
                save_fixture_image(customer_id, fixture.code, content, content_type=content_type, filename=filename)
                if self.repo.is_fixture_code_globally_unique(fixture.code):
                    delete_legacy_fixture_image(fixture.code)
            except ValueError as exc:
                results.append({"file_name": filename, "fixture_code": fixture.code, "fixture_id": fixture.id, "success": False, "message": str(exc)})
                continue

            self.audit.record(
                customer_id=customer_id,
                entity_type="fixture",
                entity_key=fixture.code,
                action="upload_image",
                summary=f"批次上傳治具圖片 {fixture.code}",
                actor=actor,
            )
            uploaded_count += 1
            results.append({"file_name": filename, "fixture_code": fixture.code, "fixture_id": fixture.id, "success": True, "message": "上傳成功"})

        self.db.commit()
        return {
            "requested_count": len(uploads),
            "uploaded_count": uploaded_count,
            "failed_count": len(uploads) - uploaded_count,
            "results": results,
        }

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
            try:
                delete_fixture_image(customer_id, fixture_code)
                # A flat legacy file is either this unique fixture's old image or ambiguous
                # shared state. Removing it prevents a duplicate code from becoming a false
                # match after one of the fixtures is deleted.
                delete_legacy_fixture_image(fixture_code)
            except OSError:
                logger.warning(
                    "Failed to clean up fixture image after deleting fixture %s for customer %s",
                    fixture_code,
                    customer_id,
                    exc_info=True,
                )
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

    def list_models_page(self, *, customer_id: int, page: int, page_size: int, keyword: str = "", is_active: bool | None = None) -> dict:
        items, total = self.repo.list_models_page(customer_id=customer_id, page=page, page_size=page_size, keyword=keyword, is_active=is_active)
        return {"items": items, "page": page, "page_size": page_size, "total": total}

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

    def delete_model(
        self,
        model_id: int,
        *,
        customer_id: int,
        actor: SessionContext | None = None,
    ) -> MachineModelDeleteRead:
        model = self.repo.get_model(model_id, customer_id=customer_id)
        if model is None:
            raise ValueError(f"model {model_id} not found")

        model_code = model.code
        model_name = model.name
        try:
            delete_stats = self.repo.delete_model(model)
            self.audit.record(
                customer_id=customer_id,
                entity_type="model",
                entity_key=model_code,
                action="delete",
                summary=(
                    f"永久刪除機種 {model_code} / {model_name}；"
                    f"刪除 {delete_stats['deleted_model_station_count']} 筆機種站點對應、"
                    f"{delete_stats['deleted_requirement_count']} 筆治具需求、"
                    f"{delete_stats['deleted_capacity_summary_count']} 筆產能摘要"
                ),
                actor=actor,
            )
            self.db.commit()
            return MachineModelDeleteRead(
                model_id=model_id,
                model_code=model_code,
                **delete_stats,
            )
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("機種仍被其他資料引用，無法刪除") from exc

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

    def list_stations_page(self, *, customer_id: int, page: int, page_size: int, keyword: str = "", is_active: bool | None = None) -> dict:
        items, total = self.repo.list_stations_page(customer_id=customer_id, page=page, page_size=page_size, keyword=keyword, is_active=is_active)
        return {"items": items, "page": page, "page_size": page_size, "total": total}

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

    def delete_station(
        self,
        station_id: int,
        *,
        customer_id: int,
        actor: SessionContext | None = None,
    ) -> StationDeleteRead:
        station = self.repo.get_station(station_id, customer_id=customer_id)
        if station is None:
            raise ValueError(f"station {station_id} not found")

        station_code = station.code
        station_name = station.name
        try:
            delete_stats = self.repo.delete_station(station)
            self.audit.record(
                customer_id=customer_id,
                entity_type="station",
                entity_key=station_code,
                action="delete",
                summary=(
                    f"永久刪除站點 {station_code} / {station_name}；"
                    f"刪除 {delete_stats['deleted_model_station_count']} 筆機種站點對應、"
                    f"{delete_stats['deleted_requirement_count']} 筆治具需求、"
                    f"{delete_stats['deleted_capacity_summary_count']} 筆產能摘要"
                ),
                actor=actor,
            )
            self.db.commit()
            return StationDeleteRead(
                station_id=station_id,
                station_code=station_code,
                **delete_stats,
            )
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("站點仍被其他資料引用，無法刪除") from exc

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

    def stream_form_export_csv(
        self,
        *,
        entity: str,
        customer_id: int | None = None,
        keyword: str = "",
        is_active: bool | None = None,
        image_status: str = "all",
        accessible_customer_ids: list[int] | None = None,
    ):
        if entity in {"fixture", "fixture-images"}:
            if customer_id is None:
                raise ValueError("customer_id is required")
            image_codes = self._fixture_image_codes(customer_id) if entity == "fixture-images" else None
            has_image = None if image_status == "all" else image_status == "with-image"
            source = self.repo.iter_fixture_export_rows(
                customer_id=customer_id,
                keyword=keyword,
                is_active=is_active if entity == "fixture" else None,
                image_codes=image_codes,
                has_image=has_image,
            )
            if entity == "fixture-images":
                normalized_image_codes = {code.lower() for code in image_codes or set()}
                rows = (
                    {
                        "治具編號": row["code"],
                        "治具名稱": row["name"],
                        "圖片狀態": "已有圖片" if row["code"].lower() in normalized_image_codes else "尚無圖片",
                    }
                    for row in source
                )
                return stream_csv_text(["治具編號", "治具名稱", "圖片狀態"], rows)
            rows = (
                {
                    "治具編號": row["code"],
                    "治具名稱": row["name"],
                    "產線儲位": row["line_storage_location"] or "",
                    "部門儲位": row["department_storage_location"] or "",
                    "最低水位": row["min_stock_qty"],
                    "狀態": "啟用" if row["is_active"] else "停用",
                }
                for row in source
            )
            return stream_csv_text(
                ["治具編號", "治具名稱", "產線儲位", "部門儲位", "最低水位", "狀態"],
                rows,
            )
        if entity == "model":
            if customer_id is None:
                raise ValueError("customer_id is required")
            source = self.repo.iter_models(
                customer_id=customer_id,
                keyword=keyword,
                is_active=is_active,
            )
        elif entity == "station":
            if customer_id is None:
                raise ValueError("customer_id is required")
            source = self.repo.iter_stations(
                customer_id=customer_id,
                keyword=keyword,
                is_active=is_active,
            )
        elif entity == "customer":
            source = self.repo.iter_customers(keyword=keyword, customer_ids=accessible_customer_ids)
        else:
            raise ValueError(f"unsupported form export entity: {entity}")
        rows = (
            {
                "編號": row.code,
                "名稱": row.name,
                "狀態": "啟用" if getattr(row, "is_active", None) else ("停用" if hasattr(row, "is_active") else "—"),
            }
            for row in source
        )
        return stream_csv_text(["編號", "名稱", "狀態"], rows)

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
            from backend.app.services.storage_service import StorageService

            StorageService(self.db).sync_fixture_storage_fields(
                fixture, line_storage_location, department_storage_location
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

    def _serialize_fixture(
        self,
        fixture,
        min_stock_qty: int,
        *,
        legacy_unique_codes: set[str] | None = None,
    ) -> dict:
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
            "has_image": self._resolve_fixture_image(fixture, legacy_unique_codes=legacy_unique_codes) is not None,
            "created_at": fixture.created_at,
            "updated_at": fixture.updated_at,
        }

    def _serialize_customer(
        self,
        customer,
        *,
        assigned_user_ids: list[int] | None = None,
    ) -> dict:
        return {
            "id": customer.id,
            "code": customer.code,
            "name": customer.name,
            "assigned_user_ids": (
                self.repo.list_allowed_user_ids_for_customer(customer.id)
                if assigned_user_ids is None
                else assigned_user_ids
            ),
            "created_at": customer.created_at,
            "updated_at": customer.updated_at,
        }
