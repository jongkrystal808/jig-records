from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.repositories.inventory_repository import InventoryRepository
from backend.app.schemas.common import CsvImportPayload
from backend.app.schemas.inventory import StockTransactionCreate
from backend.app.services.production_service import ProductionService
from backend.app.utils.csv_tools import parse_csv_bytes, render_csv_text


class InventoryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = InventoryRepository(db)
        self.capacity_service = ProductionService(db)

    def receipt(self, payload: StockTransactionCreate, *, commit: bool = True) -> None:
        self._apply_transaction(payload, "receipt", commit=commit)

    def return_material(self, payload: StockTransactionCreate, *, commit: bool = True) -> None:
        self._apply_transaction(payload, "return", commit=commit)

    def _apply_transaction(self, payload: StockTransactionCreate, transaction_type: str, *, commit: bool = True) -> None:
        occurred_at = payload.occurred_at or datetime.now(tz=timezone.utc)
        transaction = self.repo.create_transaction(
            customer_id=payload.customer_id,
            transaction_type=transaction_type,
            occurred_at=occurred_at,
            created_by=payload.created_by.strip(),
            note=payload.note,
        )
        changed_station_ids: set[int] = set()

        for item in payload.items:
            fixture = self.repo.get_fixture(item.fixture_id)
            if fixture is None:
                self.db.rollback()
                raise ValueError(f"治具不存在：ID {item.fixture_id}")
            if fixture.customer_id != payload.customer_id:
                self.db.rollback()
                raise ValueError(f"治具 {fixture.code} 不屬於目前客戶 {payload.customer_id}")
            if fixture.manage_type != item.manage_type:
                self.db.rollback()
                raise ValueError(f"治具 {fixture.code} 管理型態不符：資料庫是 {fixture.manage_type}，送出是 {item.manage_type}")

            if transaction_type == "return":
                if item.manage_type == "datecode":
                    datecode = item.datecode or ""
                    available_qty = self.repo.get_available_datecode_qty(
                        fixture_id=item.fixture_id,
                        datecode=datecode,
                    )
                    if available_qty <= 0:
                        self.db.rollback()
                        raise ValueError(f"datecode {datecode} 不在目前庫存中")
                    if available_qty < item.quantity:
                        self.db.rollback()
                        raise ValueError(f"datecode {datecode} 剩餘可退 {available_qty} pcs，申請退料 {item.quantity} pcs")
                else:
                    serial_number = item.serial_number or ""
                    serial = self.repo.get_fixture_serial(
                        fixture_id=item.fixture_id,
                        serial_number=serial_number,
                    )
                    if serial is None:
                        self.db.rollback()
                        raise ValueError(f"serial {serial_number} 不在目前庫存中")

            self.repo.add_transaction_item(
                transaction_id=transaction.id,
                fixture_id=item.fixture_id,
                manage_type=item.manage_type,
                ownership_type=item.ownership_type,
                datecode=item.datecode,
                serial_number=item.serial_number,
                quantity=item.quantity,
                note=item.note,
            )
            level = self.repo.get_or_create_stock_level(item.fixture_id)
            summary = self.repo.get_or_create_stock_summary(item.fixture_id)
            delta_quantity = item.quantity

            if item.manage_type == "serial":
                serial = self.repo.get_fixture_serial(fixture_id=item.fixture_id, serial_number=item.serial_number or "")
                if transaction_type == "receipt":
                    if serial is not None:
                        self.db.rollback()
                        raise ValueError(f"serial {item.serial_number} 已在目前庫存中")
                    self.repo.create_fixture_serial(fixture_id=item.fixture_id, serial_number=item.serial_number or "")
                else:
                    self.repo.delete_fixture_serial(serial)

            if transaction_type == "receipt":
                summary.stock_qty += delta_quantity
            else:
                next_qty = summary.stock_qty - delta_quantity
                if next_qty < 0:
                    self.db.rollback()
                    raise ValueError(f"治具 {fixture.code} 目前庫存 {summary.stock_qty} pcs，不足以退料 {delta_quantity} pcs")
                summary.stock_qty = next_qty
                summary.returned_qty += delta_quantity

            self.repo.set_stock_status(summary, level.min_stock_qty)
            changed_station_ids.update(self.capacity_service.get_affected_station_ids_by_fixture(item.fixture_id))

        for station_id in changed_station_ids:
            self.capacity_service.recalculate_station_capacity(station_id)

        if commit:
            self.db.commit()

    def list_stock_summary(self, customer_id: int | None = None):
        return self.repo.list_stock_summary_rows(customer_id=customer_id)

    def list_alerts(self, customer_id: int | None = None):
        return self.repo.list_stock_alert_rows(customer_id=customer_id)

    def list_transactions(
        self,
        limit: int,
        customer_id: int | None = None,
        *,
        transaction_type: str | None = None,
        manage_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        fixture_code: str | None = None,
        transaction_no: str | None = None,
        datecode: str | None = None,
        serial_number: str | None = None,
        created_by: str | None = None,
    ):
        return self.repo.list_transactions(
            limit,
            customer_id=customer_id,
            transaction_type=transaction_type,
            manage_type=manage_type,
            date_from=date_from,
            date_to=date_to,
            fixture_code=fixture_code,
            transaction_no=transaction_no,
            datecode=datecode,
            serial_number=serial_number,
            created_by=created_by,
        )

    def export_transactions_csv(
        self,
        limit: int,
        customer_id: int | None = None,
        *,
        transaction_type: str | None = None,
        manage_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        fixture_code: str | None = None,
        transaction_no: str | None = None,
        datecode: str | None = None,
        serial_number: str | None = None,
        created_by: str | None = None,
    ) -> str:
        transactions = self.list_transactions(
            limit,
            customer_id=customer_id,
            transaction_type=transaction_type,
            manage_type=manage_type,
            date_from=date_from,
            date_to=date_to,
            fixture_code=fixture_code,
            transaction_no=transaction_no,
            datecode=datecode,
            serial_number=serial_number,
            created_by=created_by,
        )
        rows = []
        for tx in transactions:
            for item in tx["items"]:
                rows.append(
                    {
                        "transaction_type": tx["transaction_type"],
                        "transaction_no": tx["transaction_no"],
                        "fixture_code": item["fixture_code"],
                        "manage_type": item["manage_type"],
                        "ownership_type": item["ownership_type"],
                        "datecode": item["datecode"] or "",
                        "serial_number": item["serial_number"] or "",
                        "quantity": item["quantity"],
                        "created_by": tx["created_by"],
                        "occurred_at": tx["occurred_at"].isoformat(),
                        "note": item["note"] or tx["note"] or "",
                    }
                )
        return render_csv_text(
            [
                "transaction_type",
                "transaction_no",
                "fixture_code",
                "manage_type",
                "ownership_type",
                "datecode",
                "serial_number",
                "quantity",
                "created_by",
                "occurred_at",
                "note",
            ],
            rows,
        )

    def transaction_template_csv(self) -> str:
        return render_csv_text(
            [
                "transaction_type",
                "fixture_code",
                "ownership_type",
                "datecode",
                "serial_number",
                "quantity",
                "created_by",
                "occurred_at",
                "note",
            ],
            [
                {
                    "transaction_type": "receipt",
                    "fixture_code": "C-00001",
                    "ownership_type": "self_purchased",
                    "datecode": "202605",
                    "serial_number": "",
                    "quantity": "10",
                    "created_by": "System Admin",
                    "occurred_at": "2026-05-26T08:30:00+00:00",
                    "note": "sample",
                }
            ],
        )

    def import_transactions_csv(self, customer_id: int, operator_name: str, payload: CsvImportPayload) -> int:
        rows = parse_csv_bytes(payload.content.encode("utf-8"))
        imported_count = 0
        for row in rows:
            fixture_code = row.get("fixture_code", "")
            transaction_type = row.get("transaction_type", "")
            ownership_type = row.get("ownership_type", "")
            if not fixture_code or transaction_type not in {"receipt", "return"}:
                continue
            fixture = self.repo.get_fixture_by_code(fixture_code, customer_id=customer_id)
            if fixture is None:
                raise ValueError(f"fixture code {fixture_code} not found")
            if fixture.customer_id != customer_id:
                raise ValueError(f"fixture {fixture_code} does not belong to customer {customer_id}")
            quantity = int(row.get("quantity", "0") or "0")
            if quantity <= 0:
                quantity = 1 if fixture.manage_type == "serial" else 0
            if quantity <= 0:
                continue
            occurred_at_raw = row.get("occurred_at", "")
            occurred_at = datetime.fromisoformat(occurred_at_raw) if occurred_at_raw else None
            payload_row = StockTransactionCreate(
                customer_id=customer_id,
                created_by=row.get("created_by", "") or operator_name,
                occurred_at=occurred_at,
                note=row.get("note", "") or None,
                items=[
                    {
                        "fixture_id": fixture.id,
                        "manage_type": fixture.manage_type,
                        "ownership_type": ownership_type or "self_purchased",
                        "datecode": row.get("datecode", "") or None,
                        "serial_number": row.get("serial_number", "") or None,
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
        self.db.commit()
        return imported_count
