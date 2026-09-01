from collections import Counter
from collections.abc import Iterator
from datetime import datetime, time, timedelta, timezone
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.auth import SessionContext
from backend.app.models.master import User
from backend.app.repositories.inventory_repository import InventoryRepository
from backend.app.schemas.common import CsvImportPayload
from backend.app.schemas.inventory import StockTransactionCreate
from backend.app.services.audit_service import AuditService
from backend.app.services.production_service import ProductionService
from backend.app.utils.csv_tools import escape_spreadsheet_formula, parse_csv_bytes, render_csv_text, stream_csv_text
from backend.app.utils.identifier_rules import resolve_identifier_query


class DuplicateTransactionError(ValueError):
    def __init__(self, *, transaction_id: int, message: str) -> None:
        super().__init__(message)
        self.transaction_id = transaction_id


class InventoryService:
    DUPLICATE_GUARD_WINDOW = timedelta(minutes=2)

    def __init__(self, db: Session, *, actor: SessionContext | None = None) -> None:
        self.db = db
        self.actor = actor
        self.repo = InventoryRepository(db)
        self.capacity_service = ProductionService(db)
        self.audit = AuditService(db)

    def receipt(self, payload: StockTransactionCreate, *, commit: bool = True, allow_duplicate: bool = False) -> None:
        self._apply_transaction(payload, "receipt", commit=commit, allow_duplicate=allow_duplicate)

    def return_material(self, payload: StockTransactionCreate, *, commit: bool = True, allow_duplicate: bool = False) -> None:
        self._apply_transaction(payload, "return", commit=commit, allow_duplicate=allow_duplicate)

    @staticmethod
    def _normalize_occurred_at(value: datetime | None) -> datetime:
        source = value or datetime.now(tz=timezone.utc)
        tzinfo = source.tzinfo or timezone.utc
        return datetime.combine(source.date(), time.min, tzinfo=tzinfo)

    def _resolve_actor(self) -> tuple[int, str]:
        actor_user_id = None if self.actor is None else self.actor.user_id
        if actor_user_id is None:
            raise ValueError("交易操作必須綁定已登入使用者")
        user = self.db.get(User, actor_user_id)
        if user is None or not user.is_active:
            raise ValueError("交易操作人不存在或已停用")
        return user.id, user.display_name.strip()

    @staticmethod
    def _build_duplicate_signature_items(payload: StockTransactionCreate) -> Counter[tuple[int, str, int, str]]:
        return Counter(
            (
                item.fixture_id,
                item.identifier or "",
                item.quantity,
                item.ownership_type,
            )
            for item in payload.items
        )

    @staticmethod
    def _format_duplicate_elapsed(reference_time: datetime, now: datetime) -> str:
        normalized_reference = reference_time if reference_time.tzinfo is not None else reference_time.replace(tzinfo=timezone.utc)
        delta_seconds = max(1, int((now - normalized_reference).total_seconds()))
        if delta_seconds < 60:
            return f"{delta_seconds} 秒前"
        minutes = delta_seconds // 60
        return f"{minutes} 分鐘前"

    def _ensure_not_duplicate_transaction(
        self,
        payload: StockTransactionCreate,
        transaction_type: str,
        *,
        actor_user_id: int,
    ) -> None:
        now = datetime.now(tz=timezone.utc)
        candidates = self.repo.find_recent_transactions_by_signature(
            customer_id=payload.customer_id,
            transaction_type=transaction_type,
            actor_user_id=actor_user_id,
            transaction_no=payload.transaction_no,
            created_at_from=now - self.DUPLICATE_GUARD_WINDOW,
        )
        if not candidates:
            return

        expected_items = self._build_duplicate_signature_items(payload)
        for transaction in candidates:
            actual_items = Counter(
                (
                    item.fixture_id,
                    item.identifier or "",
                    item.quantity,
                    item.ownership_type,
                )
                for item in transaction.items
            )
            if actual_items != expected_items:
                continue
            elapsed = self._format_duplicate_elapsed(transaction.created_at, now)
            raise DuplicateTransactionError(
                transaction_id=transaction.id,
                message=f"發現 {elapsed} 已有相同交易，是否重複送出？",
            )

    def _apply_transaction(
        self,
        payload: StockTransactionCreate,
        transaction_type: str,
        *,
        commit: bool = True,
        allow_duplicate: bool = False,
    ) -> None:
        actor_user_id, actor_display_name = self._resolve_actor()
        if not allow_duplicate:
            self._ensure_not_duplicate_transaction(
                payload,
                transaction_type,
                actor_user_id=actor_user_id,
            )
        occurred_at = self._normalize_occurred_at(payload.occurred_at)
        fixtures_by_id = self.repo.lock_fixtures_for_update([item.fixture_id for item in payload.items])
        for item_index, item in enumerate(payload.items, start=1):
            fixture = fixtures_by_id.get(item.fixture_id)
            if fixture is None:
                self.db.rollback()
                raise ValueError(f"第 {item_index} 筆：治具不存在：ID {item.fixture_id}")
            if fixture.customer_id != payload.customer_id:
                self.db.rollback()
                raise ValueError(f"第 {item_index} 筆：治具 {fixture.code} 不屬於目前客戶 {payload.customer_id}")

        try:
            transaction = self.repo.create_transaction(
                customer_id=payload.customer_id,
                transaction_type=transaction_type,
                occurred_at=occurred_at,
                actor_user_id=actor_user_id,
                created_by=actor_display_name,
                transaction_no=payload.transaction_no,
                note=payload.note,
            )
        except IntegrityError as exc:
            self.db.rollback()
            normalized_transaction_no = payload.transaction_no.strip()
            raise ValueError(f"單號 {normalized_transaction_no} 已存在，若要重複送出請先修改單號") from exc
        changed_station_model_pairs: set[tuple[int, int]] = set()

        for item_index, item in enumerate(payload.items, start=1):
            fixture = fixtures_by_id[item.fixture_id]

            if transaction_type == "return":
                identifier = item.identifier or ""
                available_qty = self.repo.get_available_identifier_qty(
                    fixture_id=item.fixture_id,
                    identifier=identifier,
                    ownership_type=item.ownership_type,
                )
                if available_qty <= 0:
                    self.db.rollback()
                    raise ValueError(f"第 {item_index} 筆：治具 {fixture.code} 的識別碼 {identifier} 不在目前庫存中")
                if available_qty < item.quantity:
                    self.db.rollback()
                    raise ValueError(
                        f"第 {item_index} 筆：治具 {fixture.code} 的識別碼 {identifier} 剩餘可退 {available_qty} pcs，申請退料 {item.quantity} pcs"
                    )

            self.repo.add_transaction_item(
                transaction_id=transaction.id,
                fixture_id=item.fixture_id,
                fixture_code=fixture.code,
                fixture_name=fixture.name,
                ownership_type=item.ownership_type,
                identifier=item.identifier,
                quantity=item.quantity,
                note=item.note,
            )
            level = self.repo.get_or_create_stock_level(item.fixture_id)
            summary = self.repo.get_or_create_stock_summary_for_update(item.fixture_id)
            delta_quantity = item.quantity

            if transaction_type == "receipt":
                summary.stock_qty += delta_quantity
            else:
                next_qty = summary.stock_qty - delta_quantity
                if next_qty < 0:
                    self.db.rollback()
                    raise ValueError(f"第 {item_index} 筆：治具 {fixture.code} 目前庫存 {summary.stock_qty} pcs，不足以退料 {delta_quantity} pcs")
                summary.stock_qty = next_qty
                summary.returned_qty += delta_quantity

            self.repo.set_stock_status(summary, level.min_stock_qty)
            self.db.flush()
            changed_station_model_pairs.update(
                self.capacity_service.get_affected_station_model_pairs_by_fixture(
                    item.fixture_id,
                    customer_id=payload.customer_id,
                )
            )

        for station_id, model_id in changed_station_model_pairs:
            self.capacity_service.recalculate_station_capacity(
                station_id,
                model_id=model_id,
                customer_id=payload.customer_id,
            )

        if commit:
            self.db.commit()

    def list_stock_summary(self, customer_id: int | None = None):
        return self.repo.list_stock_summary_rows(customer_id=customer_id)

    def list_alerts(self, customer_id: int | None = None):
        return self.repo.list_stock_alert_rows(customer_id=customer_id)

    def list_identifier_stock_summary(
        self,
        customer_id: int | None = None,
        fixture_id: int | None = None,
    ):
        return self.repo.list_identifier_stock_summary_rows(customer_id=customer_id, fixture_id=fixture_id)

    def build_dashboard_summary(self, customer_id: int | None = None) -> dict:
        target_date = datetime.now().astimezone().date()
        today_totals = self.repo.summarize_transaction_quantities_on_date(target_date, customer_id=customer_id)
        low_stock_rows = self.repo.list_stock_alert_rows(customer_id=customer_id)
        return {
            "today_receipt_qty": int(today_totals.get("receipt", 0)),
            "today_return_qty": int(today_totals.get("return", 0)),
            "low_stock_count": len(low_stock_rows),
            "low_stock_preview_entries": low_stock_rows[:20],
            "has_more_low_stock_entries": len(low_stock_rows) > 20,
            "recent_receipt_entries": self.repo.list_recent_transaction_item_entries(
                10,
                customer_id=customer_id,
                transaction_type="receipt",
            ),
            "recent_return_entries": self.repo.list_recent_transaction_item_entries(
                10,
                customer_id=customer_id,
                transaction_type="return",
            ),
        }

    def list_transactions(
        self,
        limit: int,
        customer_id: int | None = None,
        *,
        fixture_id: int | None = None,
        transaction_type: str | None = None,
        ownership_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        fixture_code: str | None = None,
        transaction_no: str | None = None,
        identifier: str | None = None,
        created_by: str | None = None,
    ):
        identifier_exact_matches, identifier_contains = resolve_identifier_query(identifier)
        return self.repo.list_transactions(
            limit,
            customer_id=customer_id,
            fixture_id=fixture_id,
            transaction_type=transaction_type,
            ownership_type=ownership_type,
            date_from=date_from,
            date_to=date_to,
            fixture_code=fixture_code,
            transaction_no=transaction_no,
            identifier_exact_matches=identifier_exact_matches,
            identifier_contains=identifier_contains,
            created_by=created_by,
        )

    def list_transaction_overview_page(
        self,
        page: int,
        page_size: int,
        customer_id: int | None = None,
        *,
        transaction_type: str | None = None,
        ownership_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        fixture_code: str | None = None,
        transaction_no: str | None = None,
        identifier: str | None = None,
        created_by: str | None = None,
    ):
        identifier_exact_matches, identifier_contains = resolve_identifier_query(identifier)
        return self.repo.list_transaction_overview_page(
            page,
            page_size,
            customer_id=customer_id,
            transaction_type=transaction_type,
            ownership_type=ownership_type,
            date_from=date_from,
            date_to=date_to,
            fixture_code=fixture_code,
            transaction_no=transaction_no,
            identifier_exact_matches=identifier_exact_matches,
            identifier_contains=identifier_contains,
            created_by=created_by,
        )

    def list_transaction_page(
        self,
        page: int,
        page_size: int,
        customer_id: int | None = None,
        *,
        transaction_type: str | None = None,
        fixture_code: str | None = None,
        transaction_no: str | None = None,
        created_by: str | None = None,
    ):
        return self.repo.list_transaction_page(
            page,
            page_size,
            customer_id=customer_id,
            transaction_type=transaction_type,
            fixture_code=fixture_code,
            transaction_no=transaction_no,
            created_by=created_by,
        )

    def build_transaction_export_report(
        self,
        customer_id: int | None = None,
        *,
        report_type: str,
        transaction_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        fixture_code: str | None = None,
        transaction_no: str | None = None,
        ownership_type: str | None = None,
        identifier: str | None = None,
        created_by: str | None = None,
    ) -> tuple[list[str], list[dict]]:
        identifier_exact_matches, identifier_contains = resolve_identifier_query(identifier)
        item_rows = self.repo.list_transaction_item_rows(
            customer_id=customer_id,
            transaction_type=transaction_type,
            date_from=date_from,
            date_to=date_to,
            fixture_code=fixture_code,
            transaction_no=transaction_no,
            ownership_type=ownership_type,
            identifier_exact_matches=identifier_exact_matches,
            identifier_contains=identifier_contains,
            created_by=created_by,
        )
        if report_type == "summary":
            columns = ["治具編號", "收料數", "退料數", "總數"]
            grouped: dict[str, dict] = {}
            for row in item_rows:
                target = grouped.setdefault(
                    row["fixture_code"],
                    {"治具編號": row["fixture_code"], "收料數": 0, "退料數": 0, "總數": 0},
                )
                if row["transaction_type"] == "receipt":
                    target["收料數"] += int(row["quantity"])
                else:
                    target["退料數"] += int(row["quantity"])
                target["總數"] = target["收料數"] - target["退料數"]
            rows = sorted(grouped.values(), key=lambda row: str(row["治具編號"]))
            return columns, rows

        columns = ["治具編號", "識別碼", "收料數", "退料數", "總數"]
        grouped_detail: dict[tuple[str, str], dict] = {}
        for row in item_rows:
            key = (row["fixture_code"], row["identifier"] or "")
            target = grouped_detail.setdefault(
                key,
                {
                    "治具編號": row["fixture_code"],
                    "識別碼": row["identifier"] or "",
                    "收料數": 0,
                    "退料數": 0,
                    "總數": 0,
                },
            )
            if row["transaction_type"] == "receipt":
                target["收料數"] += int(row["quantity"])
            else:
                target["退料數"] += int(row["quantity"])
            target["總數"] = target["收料數"] - target["退料數"]
        rows = sorted(grouped_detail.values(), key=lambda row: (str(row["治具編號"]), str(row["識別碼"])))
        return columns, rows

    def get_transaction_export_preview(
        self,
        customer_id: int | None = None,
        *,
        report_type: str,
        transaction_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        fixture_code: str | None = None,
        transaction_no: str | None = None,
        ownership_type: str | None = None,
        identifier: str | None = None,
        created_by: str | None = None,
    ) -> dict:
        columns, rows = self.build_transaction_export_report(
            customer_id=customer_id,
            report_type=report_type,
            transaction_type=transaction_type,
            date_from=date_from,
            date_to=date_to,
            fixture_code=fixture_code,
            transaction_no=transaction_no,
            ownership_type=ownership_type,
            identifier=identifier,
            created_by=created_by,
        )
        identifier_exact_matches, identifier_contains = resolve_identifier_query(identifier)
        item_rows = self.repo.list_transaction_item_rows(
            customer_id=customer_id,
            transaction_type=transaction_type,
            date_from=date_from,
            date_to=date_to,
            fixture_code=fixture_code,
            transaction_no=transaction_no,
            ownership_type=ownership_type,
            identifier_exact_matches=identifier_exact_matches,
            identifier_contains=identifier_contains,
            created_by=created_by,
        )
        return {
            "report_type": report_type,
            "column_count": len(columns),
            "raw_item_count": len(item_rows),
            "export_row_count": len(rows),
        }

    @staticmethod
    def render_transaction_report_txt(columns: list[str], rows: list[dict]) -> str:
        return render_csv_text(columns, rows).replace(",", "\t")

    @staticmethod
    def render_transaction_report_xlsx(report_title: str, columns: list[str], rows: list[dict]) -> bytes:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "匯出資料"
        sheet.append([escape_spreadsheet_formula(report_title)])
        sheet.append([escape_spreadsheet_formula(column) for column in columns])
        sheet["A1"].font = Font(bold=True)
        for cell in sheet[2]:
            cell.font = Font(bold=True)
        for row in rows:
            sheet.append([escape_spreadsheet_formula(row.get(column, "")) for column in columns])
        for column_cells in sheet.columns:
            max_length = max(len(str(cell.value or "")) for cell in column_cells)
            sheet.column_dimensions[column_cells[0].column_letter].width = min(max(max_length + 2, 10), 24)
        buffer = BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

    def stream_transactions_csv(
        self,
        customer_id: int | None = None,
        *,
        transaction_type: str | None = None,
        ownership_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        fixture_code: str | None = None,
        transaction_no: str | None = None,
        identifier: str | None = None,
        created_by: str | None = None,
    ) -> Iterator[str]:
        identifier_exact_matches, identifier_contains = resolve_identifier_query(identifier)
        transactions = self.repo.iter_transactions(
            customer_id=customer_id,
            transaction_type=transaction_type,
            ownership_type=ownership_type,
            date_from=date_from,
            date_to=date_to,
            fixture_code=fixture_code,
            transaction_no=transaction_no,
            identifier_exact_matches=identifier_exact_matches,
            identifier_contains=identifier_contains,
            created_by=created_by,
        )
        fieldnames = [
            "transaction_type",
            "transaction_no",
            "fixture_code",
            "ownership_type",
            "identifier",
            "quantity",
            "created_by",
            "occurred_at",
            "note",
        ]
        rows = (
            {
                "transaction_type": tx["transaction_type"],
                "transaction_no": tx["transaction_no"],
                "fixture_code": item["fixture_code"],
                "ownership_type": item["ownership_type"],
                "identifier": item["identifier"] or "",
                "quantity": item["quantity"],
                "created_by": tx["created_by"],
                "occurred_at": tx["occurred_at"].date().isoformat(),
                "note": item["note"] or tx["note"] or "",
            }
            for tx in transactions
            for item in tx["items"]
        )
        yield from stream_csv_text(fieldnames, rows)

    def transaction_template_csv(self) -> str:
        return render_csv_text(
            [
                "transaction_type",
                "fixture_code",
                "ownership_type",
                "identifier",
                "quantity",
                "occurred_at",
                "note",
            ],
            [
                {
                    "transaction_type": "receipt",
                    "transaction_no": "12005436",
                    "fixture_code": "C-00001",
                    "ownership_type": "self_purchased",
                    "identifier": "2605",
                    "quantity": "10",
                    "occurred_at": "2026-05-26",
                    "note": "sample",
                }
            ],
        )

    def reverse_transaction(self, transaction_id: int, *, customer_id: int | None = None, actor=None) -> dict:
        transaction = self.repo.get_transaction(transaction_id, customer_id=customer_id)
        if transaction is None:
            raise ValueError(f"transaction {transaction_id} not found")
        item_count = len(transaction.items)
        total_quantity = sum(int(item.quantity) for item in transaction.items)
        transaction_no = transaction.transaction_no.strip() if transaction.transaction_no else ""
        transaction_no_display = transaction_no or "（無單號）"
        summary = {
            "transaction_id": transaction.id,
            "transaction_no": transaction_no or None,
            "transaction_type": transaction.transaction_type,
            "item_count": item_count,
            "total_quantity": total_quantity,
        }
        self.repo.delete_transaction(transaction)
        self.recalculate_inventory_state(customer_id=transaction.customer_id)
        action_label = "收料" if summary["transaction_type"] == "receipt" else "退料"
        self.audit.record(
            customer_id=transaction.customer_id,
            entity_type="material_transaction",
            entity_key=transaction_no or f"transaction:{transaction.id}",
            action="reverse",
            summary=f"撤回{action_label}案件 {transaction_no_display}，共 {item_count} 筆明細 / {total_quantity} pcs",
            actor=actor,
        )
        self.db.commit()
        return summary

    def recalculate_inventory_state(self, *, customer_id: int | None = None) -> dict:
        fixture_rows = self.repo.list_fixtures(customer_id=customer_id)
        aggregates = self.repo.summarize_transactions_by_fixture(customer_id=customer_id)
        for fixture in fixture_rows:
            summary = self.repo.get_or_create_stock_summary(fixture.id)
            level = self.repo.get_or_create_stock_level(fixture.id)
            aggregate = aggregates.get(fixture.id)
            summary.stock_qty = 0 if aggregate is None else int(aggregate["stock_qty"])
            summary.returned_qty = 0 if aggregate is None else int(aggregate["returned_qty"])
            summary.last_transaction_at = None if aggregate is None else aggregate["last_transaction_at"]
            self.repo.set_stock_status(summary, level.min_stock_qty, touch_last_transaction=False)

        return {
            "customer_id": customer_id,
            "fixture_count": len(fixture_rows),
            "transaction_count": self.repo.count_transactions(customer_id=customer_id),
            "item_count": self.repo.count_transaction_items(customer_id=customer_id),
        }

    def import_transactions_csv(self, customer_id: int, payload: CsvImportPayload) -> int:
        rows = parse_csv_bytes(payload.content.encode("utf-8"))
        imported_count = 0
        for row_index, row in enumerate(rows, start=2):
            try:
                fixture_code = row.get("fixture_code", "")
                transaction_type = row.get("transaction_type", "")
                ownership_type = row.get("ownership_type", "")
                if not fixture_code or transaction_type not in {"receipt", "return"}:
                    continue
                fixture = self.repo.get_fixture_by_code(fixture_code, customer_id=customer_id)
                if fixture is None:
                    raise ValueError(f"找不到治具編號 {fixture_code}")
                if fixture.customer_id != customer_id:
                    raise ValueError(f"治具 {fixture_code} 不屬於目前客戶 {customer_id}")
                quantity = int(row.get("quantity", "0") or "0")
                if quantity <= 0:
                    continue
                occurred_at_raw = row.get("occurred_at", "")
                occurred_at = self._normalize_occurred_at(datetime.fromisoformat(occurred_at_raw)) if occurred_at_raw else None
                payload_row = StockTransactionCreate(
                    customer_id=customer_id,
                    occurred_at=occurred_at,
                    transaction_no=row.get("transaction_no", "") or None,
                    note=row.get("note", "") or None,
                    items=[
                        {
                            "fixture_id": fixture.id,
                            "ownership_type": ownership_type or "self_purchased",
                            "identifier": row.get("identifier", "") or None,
                            "quantity": quantity,
                            "note": row.get("note", "") or None,
                        }
                    ],
                )
                if transaction_type == "receipt":
                    self.receipt(payload_row, commit=False)
                else:
                    self.return_material(payload_row, commit=False)
                imported_count += 1
            except ValueError as exc:
                self.db.rollback()
                raise ValueError(f"CSV 第 {row_index} 列：{exc}") from exc
        self.db.commit()
        return imported_count
