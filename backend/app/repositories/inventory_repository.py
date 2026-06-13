from datetime import datetime, timezone

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from backend.app.models.inventory import (
    FixtureSerial,
    FixtureStockLevel,
    FixtureStockSummary,
    MaterialTransaction,
    MaterialTransactionItem,
)
from backend.app.models.master import Fixture


class InventoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_transaction(
        self,
        *,
        customer_id: int,
        transaction_type: str,
        occurred_at: datetime,
        created_by: str,
        note: str | None,
    ) -> MaterialTransaction:
        temp_no = f"TMP-{datetime.now(tz=timezone.utc):%Y%m%d%H%M%S%f}-{customer_id}"
        transaction = MaterialTransaction(
            customer_id=customer_id,
            transaction_type=transaction_type,
            transaction_no=temp_no,
            occurred_at=occurred_at,
            created_by=created_by,
            note=note,
        )
        self.db.add(transaction)
        self.db.flush()
        prefix = "RCV" if transaction_type == "receipt" else "RTN"
        transaction.transaction_no = f"{prefix}-{occurred_at:%Y%m%d}-{transaction.id:06d}"
        return transaction

    def add_transaction_item(
        self,
        *,
        transaction_id: int,
        fixture_id: int,
        ownership_type: str,
        identifier: str | None,
        quantity: int,
        note: str | None,
    ) -> MaterialTransactionItem:
        item = MaterialTransactionItem(
            transaction_id=transaction_id,
            fixture_id=fixture_id,
            manage_type="datecode",
            ownership_type=ownership_type,
            datecode=identifier,
            serial_number=None,
            quantity=quantity,
            note=note,
        )
        self.db.add(item)
        return item

    def get_fixture(self, fixture_id: int) -> Fixture | None:
        return self.db.get(Fixture, fixture_id)

    def get_fixture_by_code(self, code: str, customer_id: int | None = None) -> Fixture | None:
        stmt = select(Fixture).where(Fixture.code == code)
        if customer_id is not None:
            stmt = stmt.where(Fixture.customer_id == customer_id)
        return self.db.scalar(stmt)

    def get_or_create_stock_level(self, fixture_id: int) -> FixtureStockLevel:
        level = self.db.get(FixtureStockLevel, fixture_id)
        if level:
            return level
        level = FixtureStockLevel(fixture_id=fixture_id, min_stock_qty=0, warning_threshold=0, alert_enabled=True)
        self.db.add(level)
        self.db.flush()
        return level

    def get_or_create_stock_summary(self, fixture_id: int) -> FixtureStockSummary:
        summary = self.db.get(FixtureStockSummary, fixture_id)
        if summary:
            return summary
        summary = FixtureStockSummary(fixture_id=fixture_id, stock_qty=0, returned_qty=0, stock_status="normal")
        self.db.add(summary)
        self.db.flush()
        return summary

    def set_stock_status(self, summary: FixtureStockSummary, min_stock_qty: int) -> None:
        if summary.stock_qty <= 0:
            summary.stock_status = "out_of_stock"
        elif summary.stock_qty < min_stock_qty:
            summary.stock_status = "low_stock"
        else:
            summary.stock_status = "normal"
        summary.last_transaction_at = datetime.now(tz=timezone.utc)

    def get_available_identifier_qty(self, *, fixture_id: int, identifier: str) -> int:
        stmt = (
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (MaterialTransaction.transaction_type == "receipt", MaterialTransactionItem.quantity),
                            else_=0,
                        )
                    ),
                    0,
                ).label("receipt_qty"),
                func.coalesce(
                    func.sum(
                        case(
                            (MaterialTransaction.transaction_type == "return", MaterialTransactionItem.quantity),
                            else_=0,
                        )
                    ),
                    0,
                ).label("return_qty"),
            )
            .join(MaterialTransaction, MaterialTransaction.id == MaterialTransactionItem.transaction_id)
            .where(
                MaterialTransactionItem.fixture_id == fixture_id,
                func.coalesce(MaterialTransactionItem.datecode, MaterialTransactionItem.serial_number) == identifier,
            )
        )
        row = self.db.execute(stmt).one()
        return int(row.receipt_qty or 0) - int(row.return_qty or 0)

    def list_stock_summary_rows(self, customer_id: int | None = None) -> list[dict]:
        stmt = (
            select(
                Fixture.id.label("fixture_id"),
                Fixture.code.label("fixture_code"),
                Fixture.name.label("fixture_name"),
                case((FixtureStockSummary.stock_qty.is_not(None), FixtureStockSummary.stock_qty), else_=0).label("stock_qty"),
                case((FixtureStockLevel.min_stock_qty.is_not(None), FixtureStockLevel.min_stock_qty), else_=0).label(
                    "min_stock_qty"
                ),
                case(
                    (FixtureStockSummary.stock_status.is_not(None), FixtureStockSummary.stock_status),
                    else_="normal",
                ).label("stock_status"),
                FixtureStockSummary.last_transaction_at.label("last_transaction_at"),
            )
            .outerjoin(FixtureStockSummary, FixtureStockSummary.fixture_id == Fixture.id)
            .outerjoin(FixtureStockLevel, FixtureStockLevel.fixture_id == Fixture.id)
            .order_by(Fixture.code)
        )
        if customer_id is not None:
            stmt = stmt.where(Fixture.customer_id == customer_id)
        return [dict(row._mapping) for row in self.db.execute(stmt).all()]

    def list_stock_alert_rows(self, customer_id: int | None = None) -> list[dict]:
        stmt = (
            select(
                Fixture.id.label("fixture_id"),
                Fixture.code.label("fixture_code"),
                Fixture.name.label("fixture_name"),
                case((FixtureStockSummary.stock_qty.is_not(None), FixtureStockSummary.stock_qty), else_=0).label("stock_qty"),
                case((FixtureStockLevel.min_stock_qty.is_not(None), FixtureStockLevel.min_stock_qty), else_=0).label(
                    "min_stock_qty"
                ),
                case(
                    (FixtureStockSummary.stock_status.is_not(None), FixtureStockSummary.stock_status),
                    else_="normal",
                ).label("stock_status"),
            )
            .outerjoin(FixtureStockSummary, FixtureStockSummary.fixture_id == Fixture.id)
            .outerjoin(FixtureStockLevel, FixtureStockLevel.fixture_id == Fixture.id)
            .where(FixtureStockSummary.stock_status.in_(["low_stock", "out_of_stock"]))
            .order_by(Fixture.code)
        )
        if customer_id is not None:
            stmt = stmt.where(Fixture.customer_id == customer_id)
        return [dict(row._mapping) for row in self.db.execute(stmt).all()]

    def list_transactions(
        self,
        limit: int,
        customer_id: int | None = None,
        *,
        transaction_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        fixture_code: str | None = None,
        transaction_no: str | None = None,
        identifier: str | None = None,
        created_by: str | None = None,
    ) -> list[dict]:
        tx_id_stmt = (
            select(MaterialTransaction.id)
            .join(MaterialTransactionItem, MaterialTransactionItem.transaction_id == MaterialTransaction.id)
            .join(Fixture, Fixture.id == MaterialTransactionItem.fixture_id)
            .distinct()
        )
        if customer_id is not None:
            tx_id_stmt = tx_id_stmt.where(MaterialTransaction.customer_id == customer_id)
        if transaction_type:
            tx_id_stmt = tx_id_stmt.where(MaterialTransaction.transaction_type == transaction_type)
        if date_from is not None:
            tx_id_stmt = tx_id_stmt.where(MaterialTransaction.occurred_at >= date_from)
        if date_to is not None:
            tx_id_stmt = tx_id_stmt.where(MaterialTransaction.occurred_at <= date_to)
        if fixture_code:
            tx_id_stmt = tx_id_stmt.where(Fixture.code.ilike(f"%{fixture_code.strip()}%"))
        if transaction_no:
            tx_id_stmt = tx_id_stmt.where(MaterialTransaction.transaction_no.ilike(f"%{transaction_no.strip()}%"))
        if identifier:
            tx_id_stmt = tx_id_stmt.where(
                func.coalesce(MaterialTransactionItem.datecode, MaterialTransactionItem.serial_number).ilike(
                    f"%{identifier.strip()}%"
                )
            )
        if created_by:
            tx_id_stmt = tx_id_stmt.where(MaterialTransaction.created_by.ilike(f"%{created_by.strip()}%"))
        tx_id_stmt = tx_id_stmt.order_by(MaterialTransaction.id.desc()).limit(limit)
        tx_ids = list(self.db.scalars(tx_id_stmt))
        if not tx_ids:
            return []

        tx_stmt = select(MaterialTransaction).where(MaterialTransaction.id.in_(tx_ids)).order_by(MaterialTransaction.id.desc())
        transactions = list(self.db.scalars(tx_stmt))
        if not transactions:
            return []

        item_stmt = (
            select(
                MaterialTransactionItem.transaction_id,
                MaterialTransactionItem.fixture_id,
                MaterialTransactionItem.ownership_type,
                MaterialTransactionItem.datecode,
                MaterialTransactionItem.serial_number,
                MaterialTransactionItem.quantity,
                MaterialTransactionItem.note,
                Fixture.code.label("fixture_code"),
                Fixture.name.label("fixture_name"),
            )
            .join(Fixture, Fixture.id == MaterialTransactionItem.fixture_id)
            .where(MaterialTransactionItem.transaction_id.in_(tx_ids))
            .order_by(MaterialTransactionItem.id.asc())
        )
        item_rows = [dict(row._mapping) for row in self.db.execute(item_stmt).all()]
        item_map: dict[int, list[dict]] = {}
        for row in item_rows:
            item_map.setdefault(row["transaction_id"], []).append(
                {
                    "fixture_id": row["fixture_id"],
                    "fixture_code": row["fixture_code"],
                    "fixture_name": row["fixture_name"],
                    "ownership_type": row["ownership_type"],
                    "identifier": row["datecode"] or row["serial_number"],
                    "quantity": row["quantity"],
                    "note": row["note"],
                }
            )

        result: list[dict] = []
        for tx in transactions:
            result.append(
                {
                    "id": tx.id,
                    "customer_id": tx.customer_id,
                    "transaction_type": tx.transaction_type,
                    "transaction_no": tx.transaction_no,
                    "occurred_at": tx.occurred_at,
                    "created_by": tx.created_by,
                    "note": tx.note,
                    "created_at": tx.created_at,
                    "items": item_map.get(tx.id, []),
                }
            )
        return result
