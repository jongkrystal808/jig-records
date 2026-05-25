from datetime import datetime, timezone

from sqlalchemy import case, select
from sqlalchemy.orm import Session

from backend.app.models.inventory import FixtureStockLevel, FixtureStockSummary, MaterialTransaction, MaterialTransactionItem
from backend.app.models.master import Fixture


class InventoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_transaction(self, *, transaction_type: str, note: str | None) -> MaterialTransaction:
        transaction = MaterialTransaction(transaction_type=transaction_type, note=note)
        self.db.add(transaction)
        self.db.flush()
        return transaction

    def add_transaction_item(self, *, transaction_id: int, fixture_id: int, qty: int) -> MaterialTransactionItem:
        item = MaterialTransactionItem(transaction_id=transaction_id, fixture_id=fixture_id, qty=qty)
        self.db.add(item)
        return item

    def get_fixture(self, fixture_id: int) -> Fixture | None:
        return self.db.get(Fixture, fixture_id)

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

    def list_stock_summary_rows(self) -> list[dict]:
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
        return [dict(row._mapping) for row in self.db.execute(stmt).all()]

    def list_stock_alert_rows(self) -> list[dict]:
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
        return [dict(row._mapping) for row in self.db.execute(stmt).all()]

    def list_transactions(self, limit: int) -> list[dict]:
        tx_stmt = (
            select(MaterialTransaction)
            .order_by(MaterialTransaction.id.desc())
            .limit(limit)
        )
        transactions = list(self.db.scalars(tx_stmt))
        if not transactions:
            return []

        tx_ids = [tx.id for tx in transactions]
        item_stmt = (
            select(
                MaterialTransactionItem.transaction_id,
                MaterialTransactionItem.fixture_id,
                MaterialTransactionItem.qty,
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
                    "qty": row["qty"],
                }
            )

        result: list[dict] = []
        for tx in transactions:
            result.append(
                {
                    "id": tx.id,
                    "transaction_type": tx.transaction_type,
                    "note": tx.note,
                    "created_at": tx.created_at,
                    "items": item_map.get(tx.id, []),
                }
            )
        return result
